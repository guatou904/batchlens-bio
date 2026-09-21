"""A cell-table adapter to the standard BatchLens contract, not a second audit engine."""

import base64
import binascii
import csv
import hashlib
import io
import json
import unicodedata
from typing import Any

import pandas as pd
from pydantic import ValidationError

from batchlens.config import CellCoverage, InputError, StudySpec
from batchlens.metadata import read_table, required
from batchlens.sources import Upload

MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 100_000
ROLES = ("sample", "unit", "target", "batch", "cell_type", "timepoint", "cell_id")
ALIASES = {
    "sample": ("sample", "sampleid", "library", "libraryid", "样本"),
    "unit": ("donor", "donorid", "unit", "unitid", "animal", "patient", "subject", "供体"),
    "target": ("condition", "group", "treatment", "target", "分组", "条件"),
    "batch": ("batch", "batchid", "run", "runid", "批次"),
    "cell_type": ("celltype", "annotation", "cellannotation", "细胞类型"),
    "timepoint": ("timepoint", "time", "day", "visit", "时间点"),
    "cell_id": ("cellid", "barcode", "cellbarcode", "observationid", "细胞编号"),
}


def decode_cell_file(value: Any) -> Upload:
    if not isinstance(value, dict) or set(value) != {"name", "data"}:
        raise InputError("Choose one UTF-8 CSV/TSV cell metadata file")
    name, data = value["name"], value["data"]
    if not isinstance(name, str) or not 1 <= len(name) <= 255:
        raise InputError("Invalid metadata filename")
    if any(c in name for c in ("/", "\\")) or any(unicodedata.category(c) == "Cc" for c in name):
        raise InputError("Use a filename without a directory or control characters")
    if not isinstance(data, str) or len(data) > (MAX_BYTES * 4 // 3 + 4):
        raise InputError(
            "Quick check accepts a file up to 10 MiB; use advanced input for larger data"
        )
    try:
        raw = base64.b64decode(data, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise InputError("Invalid metadata file encoding") from exc
    if not 0 < len(raw) <= MAX_BYTES:
        raise InputError("Quick check requires a nonempty file up to 10 MiB")
    return Upload(name, raw)


def cell_table(source: Upload) -> pd.DataFrame:
    if not 0 < len(source.data) <= MAX_BYTES:
        raise InputError("Quick check requires a nonempty file up to 10 MiB")
    # Bound row/column allocation before pandas materializes a table.
    try:
        reader = csv.reader(
            io.StringIO(source.data.decode("utf-8-sig")),
            delimiter="\t" if source.suffix.lower() == ".tsv" else ",",
            strict=True,
        )
        columns = next(reader, [])
        if len(columns) > 256 or any(
            len(c) > 200 or any(unicodedata.category(ch) == "Cc" for ch in c) for c in columns
        ):
            raise InputError("Use up to 256 headers, each up to 200 characters without controls")
        for index, _ in enumerate(reader, 1):
            if index > MAX_ROWS:
                raise InputError("Quick check accepts at most 100,000 cell rows")
    except (UnicodeError, csv.Error) as exc:
        raise InputError("Cannot read UTF-8 CSV/TSV; check encoding and quoted fields") from exc
    table, _ = read_table(source)
    return table


def mapped_table(table: pd.DataFrame, mapping: Any) -> pd.DataFrame:
    if not isinstance(mapping, dict) or mapping.keys() - set(ROLES):
        raise InputError("Invalid column mapping")
    if any(not isinstance(mapping.get(role), str) or not mapping[role] for role in ROLES[:5]):
        raise InputError("Map sample, biological unit, condition, batch and cell type")
    selected = []
    for role in ROLES:
        value = mapping.get(role)
        if value is not None and (not isinstance(value, str) or value not in table.columns):
            raise InputError("Selected column does not exist")
        if value is not None:
            selected.append(value)
    if len(set(selected)) != len(selected):
        raise InputError("Each role must use a distinct column")
    required(table, selected, "cell metadata")
    if any(
        table[column].map(lambda x: any(unicodedata.category(c) == "Cc" for c in x)).any()
        for column in selected
    ):
        raise InputError("Selected metadata contains control characters")
    cells = pd.DataFrame({role: table[mapping[role]] for role in ROLES if mapping.get(role)})
    design_roles = [role for role in ("unit", "target", "batch", "timepoint") if role in cells]
    if (cells.groupby("sample")[design_roles].nunique() > 1).any().any():
        raise InputError("A sample has conflicting unit, condition, batch or selected timepoint")
    if "cell_id" in cells and cells.cell_id.duplicated().any():
        raise InputError("Duplicate cell IDs: review the source table or use globally unique IDs")
    return cells


def preview(source: Upload, mapping: Any = None) -> dict[str, Any]:
    table = cell_table(source)
    normalized = {
        column: "".join(c for c in column.casefold() if c.isalnum()) for column in table.columns
    }
    suggestions = {}
    for role, aliases in ALIASES.items():
        matches = [column for column, value in normalized.items() if value in aliases]
        suggestions[role] = matches[0] if len(matches) == 1 else None
    # Optional timepoint changes the model; always require an explicit choice.
    suggestions["timepoint"] = None
    result = {
        "columns": list(table.columns),
        "rows": table.head(5).to_dict("records"),
        "row_count": len(table),
        "suggested_mapping": suggestions,
    }
    if mapping is not None:
        cells = mapped_table(table, mapping)
        samples = cells.drop_duplicates("sample")
        result["study"] = {
            "levels": sorted(set(cells.target)),
            "samples": len(samples),
            "units": int(samples.unit.nunique()),
            "repeated_units": int((samples.groupby("unit").size() > 1).sum()),
        }
    return result


def prepare(source: Upload, payload: dict[str, Any]) -> tuple[dict[str, Upload], dict[str, Any]]:
    cells = mapped_table(cell_table(source), payload.get("mapping"))
    levels = sorted(set(cells.target))
    if len(levels) < 2:
        raise InputError("A comparison needs at least two observed conditions")
    numerator, denominator = payload.get("numerator"), payload.get("denominator")
    if (
        not isinstance(numerator, str)
        or not isinstance(denominator, str)
        or numerator not in levels
        or denominator not in levels
        or numerator == denominator
    ):
        raise InputError(
            "Choose two different observed conditions and confirm comparison direction"
        )
    mode = payload.get("design_mode")
    if mode not in ("independent", "paired"):
        raise InputError("Declare independent or paired sampling")
    if mode == "paired" and len(levels) != 2:
        raise InputError(
            "Paired mode supports exactly two conditions; use advanced input for review"
        )
    try:
        coverage = CellCoverage.model_validate(payload.get("cell_coverage", {}))
    except ValidationError as exc:
        raise InputError(
            "Invalid coverage thresholds: units >= 2, cells >= 1, share 0.5–1"
        ) from exc
    variables = {
        "condition": {
            "role": "target",
            "type": "categorical",
            "levels": levels,
            "reference": denominator,
        },
        "batch": {
            "role": "batch",
            "type": "categorical",
            "levels": sorted(set(cells.batch)),
            "reference": sorted(set(cells.batch))[0],
        },
    }
    rename = {"sample": "sample_id", "unit": "unit_id", "target": "condition"}
    columns = ["sample", "unit", "target", "batch"]
    if "timepoint" in cells:
        time_levels = sorted(set(cells.timepoint))
        variables["timepoint"] = {
            "role": "covariate",
            "type": "categorical",
            "levels": time_levels,
            "reference": time_levels[0],
        }
        columns.append("timepoint")
    config = {
        "schema_version": "1.0",
        "design_mode": mode,
        "sample_id": "sample_id",
        "unit_id": "unit_id",
        "variables": variables,
        "target": "condition",
        "adjust_for": [name for name in variables if name != "condition"],
        "contrasts": [
            {"id": "selected-comparison", "numerator": numerator, "denominator": denominator}
        ],
        "cell_coverage": coverage.model_dump(),
    }
    spec = StudySpec.model_validate(config)
    samples = cells[columns].drop_duplicates("sample").rename(columns=rename)
    observations = pd.DataFrame(
        {
            "sample_id": cells["sample"],
            "cell_type": cells.cell_type,
            "observation_id": cells.cell_id
            if "cell_id" in cells
            else [f"row-{i:06d}" for i in range(1, len(cells) + 1)],
        }
    )
    files = {
        "samples": Upload("samples.tsv", samples.to_csv(sep="\t", index=False).encode()),
        "observations": Upload(
            "observations.tsv", observations.to_csv(sep="\t", index=False).encode()
        ),
        "design": Upload("design.yaml", json.dumps(spec.model_dump(), ensure_ascii=False).encode()),
    }
    context = {
        "mode": "quick",
        "source_sha256": hashlib.sha256(source.data).hexdigest(),
        "column_mapping": {role: payload["mapping"].get(role) for role in ROLES},
        "rows": len(cells),
        "cell_id_uniqueness": "checked"
        if "cell_id" in cells
        else "not_checked_row_identifiers_generated",
    }
    return files, context
