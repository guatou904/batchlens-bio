# Reading an audit

Start with the requested comparison and experimental-unit declaration. An incorrect declaration can yield a correctly computed but irrelevant result.

`NON_ESTIMABLE`: this model cannot uniquely distinguish the requested effect. Review column dependencies and coverage. Discuss crossed sampling/controls or revising the question. Dropping batch changes the model; integration cannot manufacture missing information.

`ESTIMABLE`: the contrast is structurally identifiable under the declaration. No guarantee of power, correct covariance, randomization, adequate replication, absence of unmeasured confounding or causality. Partial overlap relies on additive assumptions and may extrapolate across missing combinations.

`NOT_ASSESSED`: descriptive checks completed, but no estimability conclusion. Repeated sections may exceed the independent contract while their sample/unit counts remain meaningful.

Findings have separate info/warning/critical severity. A rank-deficient matrix can coexist with an estimable contrast. Exit 0 is not a scientific pass; use `--fail-on warning` to stop automated workflows on unsupported models.

## Boundaries and sharing

- Metadata association does not measure expression batch effects.
- More cells/spots do not add experimental units.
- Biological sampling time and processing date are different variables.
- Donor, library and slide need not form a one-to-one hierarchy.
- Spatial autocorrelation, interaction/random effects and mechanisms are not assessed.

Findings reference JSON evidence by pointer. Manifest includes raw and canonical table hashes; row/column reordering leaves canonical hashes unchanged. Environment/time belong in manifest; numerical values can vary slightly across platforms.

Aliases remove direct sample/unit IDs, not all identifying information. Labels, covariates and rare combinations can identify people. Review every output before sharing; no original ID map is exported.

Output directories must be new. Failed writes can leave a staging directory or partial destination for inspection; nothing is automatically deleted. Only a bundle with COMPLETE and valid manifest hashes is a completed output.
