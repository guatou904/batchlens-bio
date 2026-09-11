"""Read only explicitly supplied tables, preserving strings and experimental units."""

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from batchlens.config import InputError, StudySpec


@dataclass
class Inputs:
    samples: pd.DataFrame
    observations: pd.DataFrame | None
    assays: pd.DataFrame | None
    provenance: dict[str, Any]


def read_table(path: Path) -> tuple[pd.DataFrame, str]:
    if path.suffix.lower() not in {".csv", ".tsv"}:
        raise InputError("Tables must use .csv or .tsv extensions")
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        reader = csv.reader(io.StringIO(text), delimiter=delimiter, strict=True)
        header = next(reader, [])
        if not header or any(not n.strip() or n != n.strip() for n in header):
            raise InputError("Header names must be nonempty, without surrounding whitespace")
        if len(set(header)) != len(header):
            raise InputError("Duplicate column names are not allowed")
        rows = []
        for row in reader:
            if len(row) != len(header):
                raise InputError(f"Wrong number of fields at input line {reader.line_num}")
            rows.append(row)
        if not rows:
            raise InputError("Table has no records")
        return pd.DataFrame(rows, columns=header, dtype=str), hashlib.sha256(raw).hexdigest()
    except (OSError, UnicodeError, csv.Error) as exc:
        raise InputError(
            f"Cannot read table ({type(exc).__name__}); check path and CSV/TSV"
        ) from exc


def required(table: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = sorted(set(columns) - set(table.columns))
    if missing:
        raise InputError(f"{label}: missing columns: {', '.join(missing)}")
    for column in columns:
        bad = table[column].map(lambda x: not x.strip() or x != x.strip())
        if bad.any():
            rows = (np.flatnonzero(bad.to_numpy())[:5] + 2).tolist()
            raise InputError(f"{label}: empty/padded value in column {column!r}, rows {rows}")


def canonical_hash(table: pd.DataFrame) -> str:
    columns = sorted(table.columns)
    rows = sorted(table[columns].values.tolist())
    content = json.dumps([columns, rows], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(content.encode()).hexdigest()


def load_inputs(
    samples_path: Path,
    spec: StudySpec,
    observations_path: Path | None = None,
    assays_path: Path | None = None,
) -> Inputs:
    samples, raw_hash = read_table(samples_path)
    required(samples, [spec.sample_id, spec.unit_id, *spec.variables], "samples")
    if samples[spec.sample_id].duplicated().any():
        raise InputError(
            "samples: sample_id must be unique; do not duplicate technical observations"
        )
    for name, variable in spec.variables.items():
        if variable.type == "categorical":
            unknown = set(samples[name]) - set(variable.levels or [])
            if unknown:
                raise InputError(f"samples: undeclared categorical levels in {name!r}")
        else:
            try:
                values = samples[name].astype(float).to_numpy()
            except (ValueError, OverflowError) as exc:
                raise InputError(f"samples: {name!r} must contain finite numbers") from exc
            if not np.isfinite(values).all():
                raise InputError(f"samples: {name!r} must contain finite numbers")
    for contrast in spec.contrasts:
        if not {contrast.numerator, contrast.denominator} <= set(samples[spec.target]):
            raise InputError(f"samples: requested levels absent for contrast {contrast.id!r}")
    provenance = {"samples": {"sha256": raw_hash, "canonical_sha256": canonical_hash(samples)}}
    optional: list[pd.DataFrame | None] = []
    for label, path, identity in [
        ("observations", observations_path, "observation_id"),
        ("assays", assays_path, "assay_id"),
    ]:
        if path is None:
            optional.append(None)
            continue
        table, digest = read_table(path)
        required(table, [identity, spec.sample_id], label)
        if not set(table[spec.sample_id]) <= set(samples[spec.sample_id]):
            raise InputError(f"{label}: unknown sample reference")
        subset = [identity] if label == "observations" else [spec.sample_id, identity]
        if table.duplicated(subset=subset).any():
            raise InputError(f"{label}: duplicate identity/link")
        if label == "assays":
            for name, var in spec.variables.items():
                if var.role == "batch" and name in table:
                    required(table, [name], label)
                    if not set(table[name]) <= set(var.levels or []):
                        raise InputError(f"assays: undeclared batch levels in {name!r}")
                    if (table.groupby(identity)[name].nunique() > 1).any():
                        raise InputError(f"assays: one assay has conflicting {name!r} values")
                    for sample, group in table.groupby(spec.sample_id, sort=True):
                        if group[name].nunique() == 1:
                            expected = samples.set_index(spec.sample_id)[name].to_dict()[sample]
                            if group[name].iloc[0] != expected:
                                raise InputError(
                                    f"assays: single-batch link conflicts with {name!r}"
                                )
        for column in ["cell_type", "region", "slide_id", "section_id"]:
            if column in table:
                required(table, [column], label)
        provenance[label] = {"sha256": digest, "canonical_sha256": canonical_hash(table)}
        optional.append(table)
    samples = samples.sort_values(spec.sample_id).reset_index(drop=True)
    return Inputs(samples, optional[0], optional[1], provenance)


def deidentify(inputs: Inputs, spec: StudySpec) -> Inputs:
    """Stable local aliases, not anonymity. Never export the source-to-alias mapping."""
    samples = inputs.samples[[spec.sample_id, spec.unit_id, *spec.variables]].copy()
    tables = [t.copy() if t is not None else None for t in [inputs.observations, inputs.assays]]
    for column, prefix in [(spec.sample_id, "sample"), (spec.unit_id, "unit")]:
        mapping = {
            value: f"{prefix}-{i:04d}" for i, value in enumerate(sorted(set(samples[column])), 1)
        }
        samples[column] = samples[column].map(mapping)
        for table in tables:
            if table is not None and column in table:
                table[column] = table[column].map(mapping)
    for table in tables:
        if table is not None:
            for column in ["observation_id", "assay_id", "slide_id", "section_id"]:
                if column in table and column not in spec.variables:
                    values = sorted(set(table[column]))
                    mapping = {v: f"{column}-{i:04d}" for i, v in enumerate(values, 1)}
                    table[column] = table[column].map(mapping)
    return Inputs(samples, tables[0], tables[1], inputs.provenance)
