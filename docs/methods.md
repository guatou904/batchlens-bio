# Methods and numerical contract

BatchLens inspects design structure, fitting no response/outcome. It does not measure expression batch-effect magnitude or validate a model declaration.

## Encoding

Rows are samples sorted by sample ID. There is always an intercept. Categorical variables use treatment coding with declared level order/reference; unused nuisance levels stay visible. Target columns precede adjustments. Paired mode adds unit indicators. Numeric adjustment is scaled by maximum absolute magnitude before centering/standardizing to avoid overflow; parameters are exported. Constant numeric columns become zero columns.

## Rank and estimability

For n×p matrix X, double-precision SVD supplies singular values and a row-space basis. Rank cutoff is `eps * max(n,p) * largest_singular_value`. Encoding, design rows, singular values, realized tolerance and normalized null-space dependency vectors are exported. Null-space basis/sign can differ between BLAS implementations.

cᵀβ is estimable iff c is in the row space of X. With orthonormal row basis V, test `norm(c - V.T @ V @ c) / max(1, norm(c)) <= 1e-10`. A target-level difference adds +1/-1 to non-reference target indicators; additive nuisance terms cancel. No coefficient is estimated from an arbitrary generalized-inverse fit.

Rank deficiency alone does not invalidate every contrast: duplicated nuisance columns may coexist with an estimable target. Good cell mixing cannot restore missing design information.

Condition number on the retained nonzero subspace above `1e8` triggers numerical sensitivity. This is an engineering review threshold, not a biological cutoff. Near-collinear designs need review. `n-rank` describes design-row residual degrees of freedom, not replication or power.

## Scope

Counts distinguish samples, units, observations and assay links. An empty target×batch combination alone does not prove non-estimability. Fewer than two units at a target level triggers a replication warning; two units do not receive a power pass.

Independent: one sample/unit. Paired: one sample/unit/target with two target levels. Complex nesting, missing pairs and multi-batch sample links produce descriptive findings and NOT_ASSESSED. No aggregation, representative-section selection, donor-to-run inference or automatic model repair.

## Independent verification

`scripts/verify_r_oracle.R` constructs five designs independently and uses R `model.matrix` with QR rank before/after appending the contrast. It does not reuse Python matrices or SVD logic. This regression evidence is not independent expert review.

Background: [DESeq2 design discussion](https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html#model-matrix-not-full-rank), [ExploreModelMatrix](https://csoneson.github.io/ExploreModelMatrix/articles/ExploreModelMatrix.html). BatchLens does not replace their downstream analyses.
