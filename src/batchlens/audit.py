"""Evidence-backed findings over experimental units and declared contrasts."""

from typing import Any

from batchlens import __version__
from batchlens.config import StudySpec
from batchlens.design import analyse_design
from batchlens.metadata import Inputs, deidentify

LIMITATION = (
    "Metadata and the declared additive model only. This audit does not establish power, "
    "independence, randomization, absence of unmeasured confounding, or causality."
)


def audit(inputs: Inputs, spec: StudySpec) -> dict[str, Any]:
    inputs = deidentify(inputs, spec)
    samples, observations, assays = inputs.samples, inputs.observations, inputs.assays
    findings: list[dict[str, Any]] = []

    def finding(rule: str, severity: str, message: str, refs: list[str], next_step: str) -> None:
        findings.append(
            {
                "rule_id": rule,
                "rule_version": "1.0",
                "severity": severity,
                "scope": "declared study",
                "message": message,
                "evidence_refs": refs,
                "limitations": LIMITATION,
                "suggested_next_step": next_step,
            }
        )

    units: list[dict[str, Any]] = [
        {
            "unit_alias": unit,
            "samples": len(group),
            "sample_aliases": sorted(group[spec.sample_id]),
            "target_levels": sorted(set(group[spec.target])),
        }
        for unit, group in samples.groupby(spec.unit_id, sort=True)
    ]
    unsupported: list[str] = []
    if any(unit["samples"] > 1 for unit in units):
        finding(
            "BL-UNIT-001",
            "info",
            "Repeated samples from an experimental unit are present.",
            ["/units"],
            "Verify the declared experimental unit and repeated-sampling structure.",
        )
    if spec.design_mode == "independent" and any(unit["samples"] != 1 for unit in units):
        unsupported.append("independent mode requires exactly one sample per experimental unit")
    if spec.design_mode == "paired":
        expected = set(spec.variables[spec.target].levels or [])
        for _, group in samples.groupby(spec.unit_id):
            if len(group) != 2 or set(group[spec.target]) != expected:
                unsupported.append(
                    "paired mode needs one sample at each target level for every unit"
                )
                break

    target_counts = []
    for level in spec.variables[spec.target].levels or []:
        subset = samples[samples[spec.target] == level]
        count = int(subset[spec.unit_id].nunique())
        target_counts.append({"target_level": level, "samples": len(subset), "units": count})
        if count < 2:
            finding(
                "BL-UNIT-002",
                "warning",
                f"Target level {level!r} has fewer than two units.",
                ["/target_counts"],
                "Review biological replication; this is not a power analysis.",
            )
    coverage = []
    for name, var in spec.variables.items():
        if var.role != "batch":
            continue
        for target in spec.variables[spec.target].levels or []:
            for batch in var.levels or []:
                subset = samples[(samples[spec.target] == target) & (samples[name] == batch)]
                coverage.append(
                    {
                        "batch_variable": name,
                        "batch_level": batch,
                        "target_level": target,
                        "samples": len(subset),
                        "units": int(subset[spec.unit_id].nunique()),
                    }
                )
    if any(row["samples"] == 0 for row in coverage):
        finding(
            "BL-COVER-001",
            "warning",
            "Some target-by-batch combinations have no samples.",
            ["/coverage"],
            "Review coverage. An empty combination alone is not non-estimability.",
        )

    observation_coverage = []
    if observations is not None:
        lookup = samples.set_index(spec.sample_id)
        observed = set(observations[spec.sample_id])
        absent = sorted(set(samples[spec.sample_id]) - observed)
        if absent:
            finding(
                "BL-COVER-002",
                "warning",
                f"{len(absent)} samples have no linked observations.",
                ["/counts"],
                "Confirm whether the observation export is intentionally partial.",
            )
        for column in ["cell_type", "region"]:
            if column not in observations:
                continue
            for label, group in observations.groupby(column, sort=True):
                for target in spec.variables[spec.target].levels or []:
                    selected = group[group[spec.sample_id].map(lookup[spec.target]) == target]
                    observation_coverage.append(
                        {
                            "annotation": column,
                            "label": label,
                            "target_level": target,
                            "observations": len(selected),
                            "samples": int(selected[spec.sample_id].nunique()),
                            "units": int(
                                selected[spec.sample_id].map(lookup[spec.unit_id]).nunique()
                            ),
                        }
                    )

    assay_summary: dict[str, Any] = {"links": 0, "assays": 0, "multi_batch_samples": []}
    if assays is not None:
        assay_summary.update(links=len(assays), assays=int(assays.assay_id.nunique()))
        for name, var in spec.variables.items():
            if var.role != "batch" or name not in assays:
                continue
            for sample, group in assays.groupby(spec.sample_id, sort=True):
                if group[name].nunique() > 1:
                    assay_summary["multi_batch_samples"].append(
                        {
                            "sample_alias": sample,
                            "batch_variable": name,
                            "batch_levels": sorted(set(group[name])),
                        }
                    )
        for column in ["slide_id", "section_id"]:
            if column in assays:
                assay_summary[column + "_count"] = int(assays[column].nunique())
        if assay_summary["multi_batch_samples"]:
            unsupported.append(
                "some samples span multiple batches; sample-level batch is not unique"
            )

    matrix = None
    if unsupported:
        comparisons = [{**c.model_dump(), "status": "NOT_ASSESSED"} for c in spec.contrasts]
        finding(
            "BL-SUPPORT-001",
            "warning",
            "; ".join(unsupported),
            ["/not_assessed"],
            "Review the analysis unit/model explicitly; no samples are automatically dropped.",
        )
    else:
        matrix, comparisons = analyse_design(samples, spec)
        if matrix["rank"] < matrix["n_columns"]:
            finding(
                "BL-DESIGN-001",
                "warning",
                "The declared design matrix is rank deficient.",
                ["/matrix_diagnostics/dependencies"],
                "Inspect the dependencies and each contrast separately; do not drop batch blindly.",
            )
        if matrix["numerically_sensitive"]:
            finding(
                "BL-NUMERIC-001",
                "warning",
                "The design is nearly singular and sensitive to tolerance.",
                ["/matrix_diagnostics"],
                "Review covariate redundancy and the numeric diagnostics.",
            )
        for index, comparison in enumerate(comparisons):
            if comparison["status"] == "NON_ESTIMABLE":
                finding(
                    "BL-CONTRAST-001",
                    "critical",
                    f"{comparison['id']}: the requested contrast is not estimable in this model.",
                    [f"/contrasts/{index}", "/matrix_diagnostics/dependencies"],
                    "Discuss crossed sampling or a revised scientific question; correction cannot "
                    "supply missing design information.",
                )

    findings.sort(
        key=lambda f: (
            {"critical": 0, "warning": 1, "info": 2}[f["severity"]],
            f["rule_id"],
            f["message"],
        )
    )
    return {
        "schema_version": "1.0",
        "tool_version": __version__,
        "ruleset_version": "1.0",
        "run_status": "completed",
        "declared_design": spec.model_dump(),
        "counts": {
            "experimental_units": len(units),
            "samples": len(samples),
            "observations": 0 if observations is None else len(observations),
        },
        "units": units,
        "target_counts": target_counts,
        "coverage": coverage,
        "observation_coverage": observation_coverage,
        "assay_summary": assay_summary,
        "matrix_diagnostics": matrix,
        "contrasts": comparisons,
        "findings": findings,
        "not_assessed": unsupported,
        "limitations": LIMITATION,
        "sharing_notice": "IDs use aliases. Labels and design values may still identify people; "
        "review every output before sharing. No observation-level data are exported.",
    }


def policy_exit(result: dict[str, Any], fail_on: str) -> int:
    levels = {"none": 99, "critical": 2, "warning": 1}
    severity = {"info": 0, "warning": 1, "critical": 2}
    return 3 if any(severity[f["severity"]] >= levels[fail_on] for f in result["findings"]) else 0
