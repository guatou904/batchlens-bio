"""Donor support in cell types, independent of the contrast-estimability engine."""

from typing import Any

from batchlens.config import InputError, StudySpec
from batchlens.metadata import Inputs


def cell_support(inputs: Inputs, spec: StudySpec) -> list[dict[str, Any]]:
    """Consume already aliased metadata; pool within unit, target and annotation.

    Extra libraries never create extra units. A missing cell type is represented
    by zero rows, with the input sample manifest supplying the eligible units.
    These descriptive counts never change a design matrix or contrast status.
    """
    settings, observations = spec.cell_coverage, inputs.observations
    if settings is None:
        return []
    if observations is None or "cell_type" not in observations:
        raise InputError("Cell coverage requires observations with a cell_type column")
    samples = inputs.samples.set_index(spec.sample_id)
    cells = observations[[spec.sample_id, "cell_type"]].copy()
    # Internal names are separate from user-declared column names.
    cells = cells.rename(columns={spec.sample_id: "_sample", "cell_type": "_type"})
    cells["_unit"] = cells["_sample"].map(samples[spec.unit_id])
    cells["_target"] = cells["_sample"].map(samples[spec.target])
    counts = cells.groupby(["_type", "_target", "_unit"]).size().to_dict()
    labels = sorted(set(cells["_type"]))
    levels = spec.variables[spec.target].levels or []
    if len(labels) * len(levels) > 10_000:
        raise InputError("Cell coverage exceeds 10,000 cell-type/target groups")
    eligible = {
        level: sorted(set(samples.loc[samples[spec.target] == level, spec.unit_id]))
        for level in levels
    }
    rows = []
    for label in labels:
        for level in levels:
            unit_counts = [int(counts.get((label, level, unit), 0)) for unit in eligible[level]]
            total = sum(unit_counts)
            rows.append(
                {
                    "cell_type": label,
                    "target_level": level,
                    "cells": total,
                    "eligible_units": len(unit_counts),
                    "observed_units": sum(value > 0 for value in unit_counts),
                    "supported_units": sum(value >= settings.min_cells for value in unit_counts),
                    "largest_unit_share": max(unit_counts, default=0) / total if total else None,
                    "min_cells": settings.min_cells,
                    "min_units": settings.min_units,
                    "dominance_threshold": settings.dominance,
                }
            )
    return rows
