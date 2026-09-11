# Implementation decisions

## 2026-09-11/12: proceed with a bounded first release

After reviewing the portfolio/specification, the owner explicitly instructed development to continue and authorized creating/uploading the first repository after completion. This supersedes the initial planning-only hold. It does **not** mean the proposed external-user interviews, comparative usability trials or independent expert review have happened.

Proceed with an exploratory metadata-only v0.1.0. Keep adoption and external review as open evidence tasks; publish their status accurately. Do not start PathwayBridge or another large implementation. Scientific regression tests and an independent numerical oracle remain required engineering checks.

## Statistical scope

Retain NumPy SVD without adding SciPy, R, Scanpy or scIB to runtime dependencies. R is used only for an independent QR/model.matrix test. No novel metric, expression correction or universal confounding score. Categorical target and additive fixed effects only. Unsupported repeated sampling/multi-batch input yields NOT_ASSESSED.

The public HumanPilot example demonstrates repeat-unit accounting, not a proven technical batch effect. Its replicate index is an illustrative technical factor, explicitly identified as such.

## Files and outputs

Require a new output directory, stricter than the earlier empty-directory allowance. Stage files first, exclusively reserve the destination, then write COMPLETE last. This is a completion-marker protocol, not an atomic directory replacement. Failures retain inspectable artifacts; no automatic cleanup or recursive deletion. IDs are aliased; model/category values are not anonymized.

## Build reproducibility

Hatchling 1.32 defaults to core metadata 2.5, which the selected Twine reader rejected. Both build targets explicitly use metadata 2.4. Keep versioned dependency locks and test built artifacts in fresh environments.

The local macOS environment applied a hidden flag to editable-install .pth files, which Python skips. Validation uses non-editable installs. uv cache keys explicitly include source/resources, avoiding stale installed code after source-only changes. This changes neither system Python nor user-wide package behavior.

## Publication

Candidate repository/package: batchlens-bio, import/CLI: batchlens, display name: BatchLens Bio. MIT for original code/synthetic examples; external data retain original terms. Real GitHub CI, repository creation, GitHub Release and PyPI publication require actual recorded evidence. User authorization is present; authentication and service-side configuration are separate prerequisites, never inferred from a local build.

## 2026-09-12: publication completed

GitHub Release and official PyPI 0.1.0 are published with identical wheel/sdist bytes. Trusted Publisher configuration was completed through the authenticated browser interface. Both remote and local official-index installation passed. See validation-record.md for run URLs, hashes and remaining external evidence tasks. Main now requires the five CI checks; subsequent changes use a branch and pull request.
