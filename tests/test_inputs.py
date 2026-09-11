import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_science import case

from batchlens.config import InputError, StudySpec, read_spec
from batchlens.metadata import canonical_hash, load_inputs, read_table


def sample_file(tmp_path, content):
    path = tmp_path / "samples.tsv"
    path.write_text(content)
    return path


@pytest.mark.parametrize(
    "content",
    [
        "sample_id\tsample_id\n1\t2\n",
        "\tunit\n1\t2\n",
        "id\tx\n1\n",
        "id\n",
        'id\tx\n"unclosed\t2\n',
    ],
)
def test_malformed_table(tmp_path, content):
    with pytest.raises(InputError):
        read_table(sample_file(tmp_path, content))


@pytest.mark.parametrize(
    "change",
    [
        lambda c: c.update(typo=True),
        lambda c: c.update(adjust_for=[]),
        lambda c: c.update(sample_id="unit_id"),
        lambda c: c["variables"]["time"].update(reference="absent"),
        lambda c: c["variables"]["run"].update(levels=["A", "A"]),
        lambda c: c["contrasts"][0].update(denominator="D7"),
        lambda c: c.update(contrasts=c["contrasts"] * 2),
    ],
)
def test_config_rejects_ambiguous_declarations(change):
    _, spec = case("balanced")
    config = spec.model_dump()
    change(config)
    with pytest.raises(ValidationError):
        StudySpec.model_validate(config)


@pytest.mark.parametrize(
    "content",
    [
        "a: 1\na: 2",
        "a: &anchor hi\nb: *anchor",
        "!!python/object/apply:os.system ['echo unsafe']",
        "[unclosed",
        "true: x",
    ],
)
def test_unsafe_or_ambiguous_yaml(tmp_path, content):
    path = tmp_path / "design.yaml"
    path.write_text(content)
    with pytest.raises(InputError):
        read_spec(path)


@pytest.mark.parametrize(
    "rows",
    [
        "s1\tu1\tD0\tA\ns1\tu2\tD7\tB\n",
        "s1\t\tD0\tA\ns2\tu2\tD7\tB\n",
        "s1\tu1\tD0\tA\ns2\tu2\tD8\tB\n",
        "s1\tu1\tD0\tA\ns2\tu2\tD0\tB\n",
        " s1\tu1\tD0\tA\ns2\tu2\tD7\tB\n",
    ],
)
def test_sample_contract(tmp_path, rows):
    _, spec = case("balanced")
    path = sample_file(tmp_path, "sample_id\tunit_id\ttime\trun\n" + rows)
    with pytest.raises(InputError):
        load_inputs(path, spec)


def test_id_strings_and_canonical_hash(tmp_path):
    path = sample_file(tmp_path, "sample_id\tunit_id\ttime\trun\n001\tNA\tD0\tA\n002\t02\tD7\tB\n")
    table, _ = read_table(path)
    assert table.iloc[0].sample_id == "001"
    assert table.iloc[0].unit_id == "NA"
    assert canonical_hash(table) == canonical_hash(table.iloc[::-1])
    assert canonical_hash(table) == canonical_hash(table[table.columns[::-1]])


@pytest.mark.parametrize(
    "table,filename",
    [
        ("observation_id\tsample_id\nc1\tmissing\n", "cells.tsv"),
        ("observation_id\tsample_id\nc1\ts1\nc1\ts2\n", "cells.tsv"),
        ("assay_id\tsample_id\trun\na1\ts1\tB\n", "assays.tsv"),
        ("assay_id\tsample_id\trun\na1\ts1\tA\na1\ts2\tB\n", "assays.tsv"),
    ],
)
def test_optional_references(tmp_path, table, filename):
    _, spec = case("balanced")
    samples = Path("src/batchlens/resources/demo/balanced/samples.tsv")
    optional = tmp_path / filename
    optional.write_text(table)
    with pytest.raises(InputError):
        load_inputs(
            samples,
            spec,
            optional if filename == "cells.tsv" else None,
            optional if filename == "assays.tsv" else None,
        )


def test_schema_export(tmp_path):
    # The shipped schema is a consumer contract, so changes must update the artifact explicitly.
    schema = json.loads(Path("docs/design.schema.json").read_text())
    assert schema == StudySpec.model_json_schema()


@pytest.mark.parametrize("name", ["observation_id", "assay_id", "cell_type", "slide_id"])
def test_reserved_identity_names(name):
    _, spec = case("balanced")
    config = spec.model_dump()
    config["sample_id"] = name
    with pytest.raises(ValidationError):
        StudySpec.model_validate(config)


@pytest.mark.parametrize("number", ["nan", "inf", "-inf", "not-a-number"])
def test_nonfinite_numeric_covariates(tmp_path, number):
    _, spec = case("balanced")
    config = spec.model_dump()
    config["variables"]["age"] = {"role": "covariate", "type": "numeric"}
    config["adjust_for"].append("age")
    spec = StudySpec.model_validate(config)
    path = sample_file(
        tmp_path,
        f"sample_id\tunit_id\ttime\trun\tage\ns1\tu1\tD0\tA\t{number}\ns2\tu2\tD7\tB\t30\n",
    )
    with pytest.raises(InputError):
        load_inputs(path, spec)
