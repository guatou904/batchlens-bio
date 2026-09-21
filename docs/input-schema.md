# Input contract

Use UTF-8 CSV or TSV, with a header and consistent field counts. IDs remain strings: `001` stays `001`; `NA` is a literal ID. Empty/padded required values, duplicate headers/IDs, unknown references and nonfinite numeric covariates fail explicitly. Unknown sample columns are not modeled or exported.

## Samples and YAML

One row per sampled specimen/time point, not per cell/spot. The configured sample ID is unique. The unit ID identifies the analyst-declared experimental unit (person, animal, organoid, etc.); it is not inferred or verified.

```csv
sample_id,unit_id,time,run
s1,u1,D0,A
s2,u2,D0,A
s3,u3,D7,B
s4,u4,D7,B
```

```yaml
schema_version: "1.0"
design_mode: independent
sample_id: sample_id
unit_id: unit_id
variables:
  time:
    role: target
    type: categorical
    levels: [D0, D7]
    reference: D0
  run:
    role: batch
    type: categorical
    levels: [A, B]
    reference: A
target: time
adjust_for: [run]
contrasts:
  - id: D7_vs_D0
    numerator: D7
    denominator: D0
```

This asks for D7 minus D0 adjusted for run; the example is completely confounded. All declared non-target variables must occur exactly once in `adjust_for`, including every declared batch. One categorical target and at least one categorical batch are required. Numeric adjustment uses `role: covariate, type: numeric`, without reference/levels.

Quote numeric-looking levels (`["1", "2"]`) and YAML boolean-like values. Unobserved nuisance levels stay as zero columns; both requested target levels must be observed. No formula evaluation, YAML aliases/anchors, duplicate keys or unknown fields. See [JSON Schema](design.schema.json). Configuration has column mappings, not paths; CLI paths are relative to the invocation directory.

`independent` requires one sample/unit. `paired` requires one sample at each of two target levels for every unit and adds a unit block. Missing pairs or repeated sections give NOT_ASSESSED; no rows are silently dropped.

## Optional observations

`observation_id` (unique) and the configured sample ID are required. Optional `cell_type`/`region` add descriptive summaries for each label and target level, with distinct sample/unit counts. All sample references must exist; partial exports trigger a warning. Observations never enter the design matrix, and no cell-level result is exported.

## Optional assay links

`assay_id` plus sample ID form a unique link. A library may include multiple samples; a sample may have multiple assays. Batch columns use declared levels. One assay cannot have conflicting values for a batch field. A sample with one linked batch must match the sample table; disagreement fails.

Multi-batch sample relations remain visible and produce NOT_ASSESSED; no majority batch is selected. Optional `slide_id`/`section_id` support counts. More complex split/pool models are not inferred. Configured sample/unit ID column names cannot reuse `observation_id`, `assay_id`, `slide_id`, `section_id`, `cell_type` or `region`. Model variables cannot reuse `observation_id`/`assay_id`; other annotation fields may be explicitly declared as model variables.

Design guard: 100,000 samples / 256 encoded columns. This is not a performance guarantee; observation tables are read in memory. Export metadata only, not HDF5 objects or expression matrices.

## Optional cell-type donor thresholds (0.3.0)

```yaml
cell_coverage:
  min_units: 3
  min_cells: 20
  dominance: 0.6
```

This requires observations with `cell_type`. Units are pooled within target level and cell type, preserving the sample manifest's denominator when cells are missing. Minimum-unit and minimum-cell thresholds are inclusive; dominance is flagged strictly above its threshold. Integers are required: units 2–100,000, cells 1–1,000,000. Share must be finite in [0.5, 1]. Booleans are not numbers here. At most 10,000 cell-type × declared-target combinations are allowed.

Omit the section to retain the prior checks. Coverage does not change contrast status. Cell-level quick import adapts to this same contract; see [quick check](quick-check.md).
