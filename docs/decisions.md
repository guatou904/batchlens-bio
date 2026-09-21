# Implementation decisions

## 2026-09-21: v0.3.0 publication authorized

After reviewing the completed local candidate, the owner explicitly approved pushing a PR, running the full cross-platform checks, merging after success, then publishing GitHub Release and PyPI v0.3.0. Follow existing branch protection. Preserve prior releases and require exact artifact hashes; external scientific/user review remains open.

## 2026-09-21: consolidate scDesign Audit into BatchLens

The owner approved one BatchLens product with quick cell-table and advanced design entry points after reviewing overlap with scDesign Audit. Keep the existing BatchLens engine, CLI, packaging and release history; bring the prototype’s role mapping, bilingual workbench/report and configurable donor coverage into that core. Maintain one scientific implementation. The original prototype and its reports remain intact; no second public package is planned.

Do not promise equivalence to the prototype’s rank-only warnings: BatchLens requires an explicit pairwise contrast and declared sampling model. Quick mode is a strict adapter to standard inputs. Paired designs add the existing unit block. Coverage thresholds are descriptive and opt-in for old advanced inputs. This preserves older scientific behavior while making the input path accessible.

Retain CSV/TSV as the unified import boundary; defer h5ad dependency expansion. Deliver a local 0.3.0 candidate with installed-package, browser and native-arm64 evidence. Public release, other-platform execution, external usability and scientific review remain separately evidenced steps.


## 2026-09-12: browser and native desktop interfaces

The owner requested both `batchlens serve` and downloadable Mac/Windows applications. Version 0.2.0 adds these interfaces without extending the scientific model. A shared service handles CLI and uploaded metadata. An in-memory source adapter avoids writing raw browser uploads to temporary directories. Completed reports remain in unique directories, following the existing completion-marker contract.

Use a standard-library loopback HTTP server and static packaged HTML/CSS/JavaScript so the browser UI adds no runtime dependency. Native pywebview is an optional extra; PyInstaller includes Python and libraries in desktop builds. macOS uses the system WebKit; Windows setup provisions WebView2 when missing. Desktop builds are alpha distributions without provisioned public signing identities. Record actual installation/GUI evidence and signing limits separately.

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
