"""Adapter parity and scientific counterexamples for the unified workbench."""

import base64
import copy
import hashlib
import io
import json
from importlib.resources import files

import pandas as pd
import pytest
from pydantic import ValidationError

from batchlens.audit import audit
from batchlens.config import CellCoverage, InputError, read_spec
from batchlens.metadata import load_inputs
from batchlens.quick import cell_table, decode_cell_file, prepare, preview
from batchlens.service import run_audit
from batchlens.sources import Upload

MAPPING = {
    "sample": "sample",
    "unit": "donor",
    "target": "condition",
    "batch": "batch",
    "cell_type": "cell_type",
    "timepoint": None,
    "cell_id": "cell_id",
}


def source(case="balanced"):
    return Upload(
        case + ".csv",
        files("batchlens").joinpath("resources/quick-demo", case + ".csv").read_bytes(),
    )


def options(case="balanced"):
    return {
        "mapping": MAPPING.copy(),
        "numerator": "regeneration",
        "denominator": "control",
        "design_mode": "paired" if case == "paired" else "independent",
    }


def adapted(case="balanced", payload=None, cell_source=None):
    uploads, context = prepare(cell_source or source(case), payload or options(case))
    spec = read_spec(uploads["design"])
    inputs = load_inputs(uploads["samples"], spec, uploads["observations"])
    return inputs, spec, uploads, context


@pytest.mark.parametrize(
    "case,status,units",
    [
        ("balanced", "ESTIMABLE", 6),
        ("confounded", "NON_ESTIMABLE", 6),
        ("paired", "ESTIMABLE", 3),
    ],
)
def test_quick_and_advanced_share_exact_scientific_result(tmp_path, case, status, units):
    inputs, spec, uploads, context = adapted(case)
    expected = audit(inputs, spec)
    advanced = run_audit(**uploads, out=tmp_path / "advanced")
    quick = run_audit(**uploads, out=tmp_path / "quick", context=context, language="zh")
    assert quick.pop("input_adapter") == context
    assert quick == advanced == expected
    assert quick["contrasts"][0]["status"] == status
    assert quick["counts"]["experimental_units"] == units
    assert quick["declared_design"]["cell_coverage"]["min_cells"] == 20
    assert b'lang="zh"' in (tmp_path / "quick/report.html").read_bytes()
    assert b'lang="en"' in (tmp_path / "quick/report.en.html").read_bytes()
    assert b'lang="zh"' in (tmp_path / "advanced/report.zh.html").read_bytes()
    for folder in ("quick", "advanced"):
        root = tmp_path / folder
        manifest = json.loads((root / "manifest.json").read_text())
        for name, digest in manifest["outputs"].items():
            assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
        text = (root / "result.json").read_text()
        assert "synthetic_00001" not in text and '"D01"' not in text and '"S01"' not in text
        assert str(tmp_path) not in text


def test_paired_requires_declaration_and_never_silently_pools_samples():
    inputs, paired, _, _ = adapted("paired")
    paired_result = audit(inputs, paired)
    independent = paired.model_copy(update={"design_mode": "independent"})
    independent_result = audit(inputs, independent)
    assert paired_result["contrasts"][0]["status"] == "ESTIMABLE"
    assert any(c["name"] == "unit_id" for c in paired_result["matrix_diagnostics"]["columns"])
    assert independent_result["contrasts"][0]["status"] == "NOT_ASSESSED"
    assert independent_result["matrix_diagnostics"] is None
    assert paired_result["cell_support"] == independent_result["cell_support"]


def test_more_cells_do_not_add_units_or_change_contrast():
    inputs, spec, _, _ = adapted()
    original = audit(inputs, spec)
    larger = copy.deepcopy(inputs)
    extra = larger.observations.copy()
    extra.observation_id = "extra-" + extra.observation_id
    larger.observations = pd.concat([larger.observations, extra])
    result = audit(larger, spec)
    assert result["counts"]["experimental_units"] == original["counts"]["experimental_units"]
    assert result["contrasts"] == original["contrasts"]
    assert result["matrix_diagnostics"] == original["matrix_diagnostics"]
    assert [r["largest_unit_share"] for r in result["cell_support"]] == [
        r["largest_unit_share"] for r in original["cell_support"]
    ]


def test_selected_timepoint_changes_the_model_only_after_explicit_opt_in():
    table = cell_table(source())
    table["timepoint"] = table.condition
    upload = Upload("time.csv", table.to_csv(index=False).encode())
    payload = options()
    inputs, spec, _, _ = adapted(payload=payload, cell_source=upload)
    assert audit(inputs, spec)["contrasts"][0]["status"] == "ESTIMABLE"
    payload["mapping"]["timepoint"] = "timepoint"
    inputs, spec, _, _ = adapted(payload=payload, cell_source=upload)
    assert spec.adjust_for == ["batch", "timepoint"]
    assert audit(inputs, spec)["contrasts"][0]["status"] == "NON_ESTIMABLE"


def test_coverage_minimum_is_inclusive_and_share_threshold_is_strict():
    inputs, spec, _, _ = adapted()
    # Each donor has exactly 40 cells per type in this balanced fixture.
    spec.cell_coverage = CellCoverage(min_units=3, min_cells=40, dominance=0.5)
    result = audit(inputs, spec)
    assert all(row["supported_units"] == 3 for row in result["cell_support"])
    spec.cell_coverage = CellCoverage(min_units=3, min_cells=41, dominance=0.5)
    result = audit(inputs, spec)
    assert all(row["supported_units"] == 0 for row in result["cell_support"])
    # Two donors contribute 40 cells each: exactly 50% must not trigger dominance.
    ids = set(inputs.samples.iloc[[0, 3]].sample_id)
    inputs.observations = inputs.observations[~inputs.observations.sample_id.isin(ids)]
    result = audit(inputs, spec)
    assert all(row["largest_unit_share"] == 0.5 for row in result["cell_support"])
    assert not any(f["rule_id"] == "BL-CELL-002" for f in result["findings"])


def test_coverage_counts_units_after_pooling_samples_within_condition():
    inputs, spec, _, _ = adapted()
    original = audit(inputs, spec)
    altered = copy.deepcopy(inputs)
    selected = altered.samples.iloc[0].copy()
    first_sample = selected.sample_id
    selected.sample_id += "-technical"
    altered.samples = pd.concat([altered.samples, selected.to_frame().T], ignore_index=True)
    rows = altered.observations.index[altered.observations.sample_id == first_sample]
    altered.observations.loc[rows[::2], "sample_id"] = selected.sample_id
    result = audit(altered, spec)
    assert result["cell_support"] == original["cell_support"]
    assert result["contrasts"][0]["status"] == "NOT_ASSESSED"


def test_missing_type_uses_manifest_and_dominance_is_within_condition():
    inputs, spec, _, _ = adapted()
    group_a = set(inputs.samples.loc[inputs.samples.condition == "control", "sample_id"])
    obs = inputs.observations
    # A whole type missing in one condition is a real zero, not a missing table row.
    inputs.observations = obs[~((obs.cell_type == "Hepatocyte") & obs.sample_id.isin(group_a))]
    result = audit(inputs, spec)
    row = next(
        r
        for r in result["cell_support"]
        if r["cell_type"] == "Hepatocyte" and r["target_level"] == "control"
    )
    assert row["cells"] == row["supported_units"] == row["observed_units"] == 0
    assert row["eligible_units"] == 3 and row["largest_unit_share"] is None
    assert any(f["rule_id"] == "BL-CELL-003" for f in result["findings"])
    # Keep one donor's cells in control; all other donors remain in the sample manifest.
    first = sorted(group_a)[0]
    inputs.observations = obs[~obs.sample_id.isin(group_a - {first})]
    result = audit(inputs, spec)
    control = [r for r in result["cell_support"] if r["target_level"] == "control"]
    treatment = [r for r in result["cell_support"] if r["target_level"] == "regeneration"]
    assert all(r["largest_unit_share"] == 1 and r["eligible_units"] == 3 for r in control)
    assert all(r["largest_unit_share"] == pytest.approx(1 / 3) for r in treatment)
    assert sum(f["rule_id"] == "BL-CELL-002" for f in result["findings"]) == 3


def test_coverage_is_opt_in_and_requires_cell_annotations():
    inputs, spec, _, _ = adapted()
    disabled = spec.model_copy(update={"cell_coverage": None})
    result = audit(inputs, disabled)
    assert result["cell_support"] == []
    assert not any(f["rule_id"].startswith("BL-CELL") for f in result["findings"])
    inputs.observations = None
    with pytest.raises(InputError, match="cell_type"):
        audit(inputs, spec)


@pytest.mark.parametrize(
    "field,value",
    [
        ("min_units", 1),
        ("min_units", True),
        ("min_units", 2.5),
        ("min_cells", 0),
        ("min_cells", "20"),
        ("min_cells", False),
        ("dominance", float("nan")),
        ("dominance", float("inf")),
        ("dominance", 0.49),
        ("dominance", 1.01),
    ],
)
def test_thresholds_are_strict_finite_and_bounded(field, value):
    with pytest.raises(ValidationError):
        CellCoverage.model_validate({field: value})


def test_preview_suggestions_and_timepoint_opt_in():
    value = preview(source())
    assert value["row_count"] == 720 and len(value["rows"]) == 5
    assert value["suggested_mapping"] == MAPPING
    value = preview(source(), MAPPING)
    assert value["study"] == {
        "levels": ["control", "regeneration"],
        "samples": 6,
        "units": 6,
        "repeated_units": 0,
    }
    ambiguous = Upload(
        "ambiguous.csv", b"sample,sample_id,donor,condition,batch,cell_type\na,a,d,c,b,t"
    )
    assert preview(ambiguous)["suggested_mapping"]["sample"] is None
    # Empty unused timepoint is valid. Explicitly selecting it must reject missing data.
    payload = options()
    payload["mapping"]["timepoint"] = "timepoint"
    with pytest.raises(InputError, match="empty/padded"):
        prepare(source(), payload)


@pytest.mark.parametrize(
    "change",
    [
        {"mapping": None},
        {"mapping": {**MAPPING, "unit": "sample"}},
        {"mapping": {**MAPPING, "unit": "unknown"}},
        {"mapping": {**MAPPING, "unit": []}},
        {"numerator": "missing"},
        {"denominator": "regeneration"},
        {"numerator": []},
        {"design_mode": "auto"},
        {"design_mode": []},
        {"cell_coverage": {"min_units": True}},
    ],
)
def test_invalid_mapping_or_design_never_becomes_a_report(change):
    payload = options()
    payload.update(change)
    with pytest.raises(InputError):
        prepare(source(), payload)


def test_conflicting_sample_and_duplicate_ids_fail():
    data = pd.read_csv(io.BytesIO(source().data), dtype=str, keep_default_na=False)
    data.loc[0, "donor"] = "other-donor"
    with pytest.raises(InputError, match="conflicting"):
        prepare(Upload("data.csv", data.to_csv(index=False).encode()), options())
    data.loc[0, "donor"] = "D01"
    data.loc[1, "cell_id"] = data.loc[0, "cell_id"]
    raw = Upload("data.csv", data.to_csv(index=False).encode())
    with pytest.raises(InputError, match="Duplicate cell IDs"):
        prepare(raw, options())
    payload = options()
    payload["mapping"]["cell_id"] = None
    _, context = prepare(raw, payload)
    assert context["cell_id_uniqueness"] == "not_checked_row_identifiers_generated"


@pytest.mark.parametrize(
    "content",
    [
        b"\xff\xfe",
        b'a,b\n"unfinished,x',
        b"a,b\nx",
        b"a,a\nx,y",
        b"a,b\n",
        b"a\x00,b\nx,y",
    ],
)
def test_malformed_cell_metadata(content):
    with pytest.raises(InputError):
        cell_table(Upload("data.csv", content))


def test_limits_are_checked_before_unbounded_materialization(monkeypatch):
    import batchlens.quick as quick

    monkeypatch.setattr(quick, "MAX_ROWS", 2)
    with pytest.raises(InputError, match="100,000"):
        cell_table(source())
    monkeypatch.setattr(quick, "MAX_BYTES", 2)
    with pytest.raises(InputError, match="10 MiB"):
        cell_table(source())


@pytest.mark.parametrize(
    "value",
    [
        None,
        {},
        [],
        {"name": "../x.csv", "data": "eA=="},
        {"name": "x.csv", "data": "!!!"},
        {"name": "x.csv", "data": ""},
    ],
)
def test_decode_rejects_bad_uploads(value):
    with pytest.raises(InputError):
        decode_cell_file(value)


def test_chinese_report_escapes_metadata_and_keeps_canonical_json(tmp_path):
    malicious = source().data.replace(b"Hepatocyte", b"<script>alert(1)</script>")
    uploads, context = prepare(Upload("study.csv", malicious), options())
    result = run_audit(**uploads, out=tmp_path / "output", context=context, language="zh")
    for language in ("en", "zh"):
        text = (tmp_path / f"output/report.{language}.html").read_text()
        assert "<script>" not in text and "&lt;script&gt;" in text
    assert result["schema_version"] == "1.1"
    assert json.loads((tmp_path / "output/result.json").read_text()) == result


def test_encoded_file_roundtrip():
    original = source()
    value = {"name": original.name, "data": base64.b64encode(original.data).decode()}
    assert decode_cell_file(value).data == original.data
