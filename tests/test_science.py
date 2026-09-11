"""Hand-computable designs, invariants, and an independent R/QR oracle."""

import copy
import json
import shutil
import subprocess
from importlib import resources
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from batchlens.audit import audit, policy_exit
from batchlens.config import InputError, StudySpec, read_spec
from batchlens.design import analyse_design
from batchlens.metadata import load_inputs


def case(name):
    folder = Path(str(resources.files("batchlens").joinpath("resources/demo", name)))
    spec = read_spec(folder / "design.yaml")
    inputs = load_inputs(
        folder / "samples.tsv",
        spec,
        folder / "observations.tsv" if (folder / "observations.tsv").exists() else None,
        folder / "assays.tsv" if (folder / "assays.tsv").exists() else None,
    )
    return inputs, spec


@pytest.mark.parametrize(
    "name,status,rank",
    [
        ("balanced", "ESTIMABLE", 3),
        ("confounded-time", "NON_ESTIMABLE", 2),
        ("partial-overlap", "ESTIMABLE", 3),
        ("redundant-nuisance", "ESTIMABLE", 3),
        ("paired", "ESTIMABLE", 3),
        ("spatial-replicates", "NOT_ASSESSED", None),
        ("mixed-assays", "NOT_ASSESSED", None),
    ],
)
def test_scientific_examples(name, status, rank):
    result = audit(*case(name))
    assert result["contrasts"][0]["status"] == status
    assert (result["matrix_diagnostics"] or {}).get("rank") == rank
    if name == "spatial-replicates":
        assert result["counts"] == {"experimental_units": 3, "samples": 12, "observations": 120}
    if rank is not None:
        matrix = result["matrix_diagnostics"]
        for vector in matrix["dependencies"]:
            np.testing.assert_allclose(np.array(matrix["encoded_rows"]) @ vector, 0, atol=1e-10)


def test_each_contrast_not_blanket_rank_failure():
    inputs, spec = case("balanced")
    data = spec.model_dump()
    data["variables"]["time"]["levels"].append("D14")
    data["contrasts"].append({"id": "D14_vs_D0", "numerator": "D14", "denominator": "D0"})
    data["variables"]["run"]["levels"].append("C")
    extra = pd.DataFrame([{"sample_id": "s9", "unit_id": "u9", "time": "D14", "run": "C"}])
    inputs.samples = pd.concat([inputs.samples, extra], ignore_index=True)
    result = audit(inputs, StudySpec.model_validate(data))
    assert [c["status"] for c in result["contrasts"]] == ["ESTIMABLE", "NON_ESTIMABLE"]


@pytest.mark.parametrize("name", ["balanced", "confounded-time", "redundant-nuisance", "paired"])
def test_row_order_and_reference_invariance(name):
    inputs, spec = case(name)
    original = audit(inputs, spec)
    shuffled = copy.deepcopy(inputs)
    shuffled.samples = shuffled.samples.sample(frac=1, random_state=17)
    # Public load path sorts sample IDs; repeat that canonicalization here.
    shuffled.samples = shuffled.samples.sort_values(spec.sample_id).reset_index(drop=True)
    assert audit(shuffled, spec) == original
    config = spec.model_dump()
    config["variables"]["time"]["reference"] = "D7"
    revised = audit(inputs, StudySpec.model_validate(config))
    assert revised["contrasts"][0]["status"] == original["contrasts"][0]["status"]


def test_observations_never_increase_replication_or_rank():
    inputs, spec = case("balanced")
    first = audit(inputs, spec)
    inputs.observations = pd.DataFrame(
        {
            "observation_id": [f"c{i}" for i in range(200)],
            "sample_id": ["s1"] * 200,
            "cell_type": ["T"] * 200,
        }
    )
    second = audit(inputs, spec)
    assert first["counts"]["experimental_units"] == second["counts"]["experimental_units"]
    assert first["matrix_diagnostics"] == second["matrix_diagnostics"]
    assert second["observation_coverage"][0]["units"] == 1


def test_incomplete_pair_not_silently_dropped():
    inputs, spec = case("paired")
    inputs.samples = inputs.samples.iloc[:-1]
    result = audit(inputs, spec)
    assert result["counts"]["samples"] == 3
    assert result["contrasts"][0]["status"] == "NOT_ASSESSED"


def test_numeric_scaling_and_near_singularity():
    inputs, spec = case("balanced")
    config = spec.model_dump()
    config["variables"]["age"] = {"role": "covariate", "type": "numeric"}
    config["adjust_for"].append("age")
    spec = StudySpec.model_validate(config)
    inputs.samples["age"] = np.arange(len(inputs.samples)).astype(str)
    baseline = audit(inputs, spec)
    inputs.samples["age"] = (np.arange(len(inputs.samples)) * 1e300).astype(str)
    scaled = audit(inputs, spec)
    assert scaled["contrasts"][0]["status"] == baseline["contrasts"][0]["status"]
    inputs.samples["age"] = (
        (inputs.samples.time == "D7").astype(float) + np.arange(len(inputs.samples)) * 1e-10
    ).astype(str)
    sensitive = audit(inputs, spec)
    assert any(f["rule_id"] == "BL-NUMERIC-001" for f in sensitive["findings"])


def test_wide_design_and_unused_levels():
    inputs, spec = case("balanced")
    config = spec.model_dump()
    config["variables"]["run"]["levels"] += [f"unused-{i}" for i in range(12)]
    matrix, comparisons = analyse_design(inputs.samples, StudySpec.model_validate(config))
    assert matrix["n_columns"] > matrix["n_rows"]
    assert comparisons[0]["status"] == "ESTIMABLE"
    assert len(matrix["dependencies"]) == matrix["n_columns"] - matrix["rank"]


@pytest.mark.parametrize(
    "name,critical,warning",
    [
        ("confounded-time", 3, 3),
        ("spatial-replicates", 0, 3),
        ("balanced", 0, 0),
    ],
)
def test_policy(name, critical, warning):
    result = audit(*case(name))
    assert policy_exit(result, "critical") == critical
    assert policy_exit(result, "warning") == warning
    assert policy_exit(result, "none") == 0


def test_all_evidence_references_resolve():
    for name in ["balanced", "confounded-time", "spatial-replicates", "mixed-assays"]:
        result = audit(*case(name))
        for finding in result["findings"]:
            for pointer in finding["evidence_refs"]:
                item = result
                for part in pointer.strip("/").split("/"):
                    item = item[int(part)] if isinstance(item, list) else item[part]
                assert item is not None


@pytest.mark.skipif(shutil.which("Rscript") is None, reason="Optional independent R oracle")
def test_independent_r_model_matrix_oracle(tmp_path):
    destination = tmp_path / "oracle.tsv"
    script = Path(__file__).parents[1] / "scripts/verify_r_oracle.R"
    subprocess.run(["Rscript", str(script), str(destination)], check=True, capture_output=True)
    results = pd.read_csv(destination, sep="\t")
    for _, row in results.iterrows():
        actual = audit(*case(row["case"]))
        assert actual["matrix_diagnostics"]["rank"] == row["rank"]
        assert actual["contrasts"][0]["status"] == row["status"]
    assert len(results) == 5


def test_core_result_is_json_serializable():
    for name in ["balanced", "confounded-time", "spatial-replicates"]:
        json.dumps(audit(*case(name)), allow_nan=False)


def test_design_limit_precedes_dense_allocation():
    inputs, spec = case("balanced")
    config = spec.model_dump()
    config["variables"]["run"]["levels"] += [f"unused-{i}" for i in range(300)]
    with pytest.raises(InputError, match="256 encoded"):
        analyse_design(inputs.samples, StudySpec.model_validate(config))
