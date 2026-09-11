"""Linear-model estimability, without fitting outcomes or interpreting causality."""

from typing import Any

import numpy as np
import pandas as pd

from batchlens.config import InputError, StudySpec


def analyse_design(samples: pd.DataFrame, spec: StudySpec) -> tuple[dict[str, Any], list[dict]]:
    n_columns = 1 + sum(
        len(v.levels or []) - 1 if v.type == "categorical" else 1 for v in spec.variables.values()
    )
    if spec.design_mode == "paired":
        n_columns += int(samples[spec.unit_id].nunique()) - 1
    if n_columns > 256 or len(samples) > 100_000:
        raise InputError("Design exceeds v0.1 limit: 100,000 samples or 256 encoded columns")
    vectors = [np.ones(len(samples), dtype=float)]
    columns: list[dict[str, Any]] = [{"name": "Intercept", "kind": "intercept"}]
    target_indices: dict[str, int] = {}
    terms = [spec.target, *spec.adjust_for]
    if spec.design_mode == "paired":
        terms.append(spec.unit_id)
    for term in terms:
        var = spec.variables.get(term)
        if var is None or var.type == "categorical":
            levels = sorted(set(samples[term])) if var is None else (var.levels or [])
            reference = levels[0] if var is None else var.reference
            for level in levels:
                if level == reference:
                    continue
                if term == spec.target:
                    target_indices[level] = len(vectors)
                vectors.append((samples[term] == level).to_numpy(dtype=float))
                columns.append(
                    {"name": term, "kind": "categorical", "level": level, "reference": reference}
                )
        else:
            values = samples[term].to_numpy(dtype=float)
            # Rescale before centering to avoid overflow for large finite input values.
            magnitude = float(np.max(np.abs(values))) or 1.0
            scaled = values / magnitude
            center = float(scaled.mean())
            scale = float(np.std(scaled)) or 1.0
            vectors.append((scaled - center) / scale)
            columns.append(
                {
                    "name": term,
                    "kind": "numeric",
                    "magnitude": magnitude,
                    "scaled_center": center,
                    "scaled_std": scale,
                }
            )
    if len(vectors) > 256 or len(samples) > 100_000:
        raise InputError("Design exceeds v0.1 limit: 100,000 samples or 256 encoded columns")
    matrix = np.column_stack(vectors)
    n, p = matrix.shape
    _, singular, vt = np.linalg.svd(matrix, full_matrices=n < p)
    tolerance = float(np.finfo(float).eps * max(n, p) * singular[0])
    rank = int(np.count_nonzero(singular > tolerance))
    basis = vt[:rank]
    dependencies = []
    for vector in vt[rank:]:
        vector = vector / np.max(np.abs(vector))
        first = next((value for value in vector if abs(value) > 1e-10), 1)
        if first < 0:
            vector = -vector
        dependencies.append([round(float(v), 12) for v in vector])
    condition = float(singular[0] / singular[rank - 1]) if rank else None
    sensitive = condition is not None and condition > 1e8
    comparisons = []
    for contrast in spec.contrasts:
        vector = np.zeros(p)
        for level, sign in [(contrast.numerator, 1), (contrast.denominator, -1)]:
            if level in target_indices:
                vector[target_indices[level]] += sign
        residual = float(
            np.linalg.norm(vector - basis.T @ (basis @ vector)) / max(1, np.linalg.norm(vector))
        )
        comparisons.append(
            {
                **contrast.model_dump(),
                "status": "ESTIMABLE" if residual <= 1e-10 else "NON_ESTIMABLE",
                "vector": vector.tolist(),
                "row_space_residual": residual,
                "tolerance": 1e-10,
            }
        )
    return {
        "n_rows": n,
        "n_columns": p,
        "rank": rank,
        "row_residual_df": n - rank,
        "columns": columns,
        "encoded_rows": matrix.tolist(),
        "sample_aliases": samples[spec.sample_id].tolist(),
        "singular_values": singular.tolist(),
        "rank_tolerance": tolerance,
        "condition_on_nonzero_subspace": condition,
        "numerically_sensitive": sensitive,
        "dependencies": dependencies,
        "assumptions": "Additive fixed-effects design; estimability is not power or causality.",
    }, comparisons
