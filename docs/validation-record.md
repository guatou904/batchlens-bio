# Validation record — updated 2026-09-21

## 0.3.0 published unified workbench

[GitHub Release v0.3.0](https://github.com/guatou904/batchlens-bio/releases/tag/v0.3.0) was published on 2026-09-21, followed by [official PyPI 0.3.0](https://pypi.org/project/batchlens-bio/0.3.0/). The immutable tag points to `7f4555aa97de3a045f7b4451f7d5b5681956b06c`, whose source tree matches the validated PR head.

- [PR #5](https://github.com/guatou904/batchlens-bio/pull/5) passed all six Linux/macOS/Windows × Python 3.12/3.13 jobs, the independent R oracle, the installed-wheel browser workflow and three native desktop jobs before merging under branch protection. The first Windows run caught two tests reading localized HTML with the system encoding; explicit UTF-8 reads fixed those tests, and all final-head checks passed.
- The [tag release run](https://github.com/guatou904/batchlens-bio/actions/runs/35586633314) repeated all eleven validation jobs and passed its publication job. Its sixteen release assets include wheel/sdist, macOS arm64 and Intel DMGs, the Windows x64 installer, actual synthetic HTML, installation/native-window records and SHA256SUMS. The native runtimes pass seven advanced and three quick examples; Windows also runs the installed executable.
- The [PyPI publication run](https://github.com/guatou904/batchlens-bio/actions/runs/35591383316) downloaded the complete release and verified all fifteen listed checksums before publishing the exact wheel/sdist. A separate read of the official PyPI Simple JSON confirms both hashes match locally downloaded Python packages, GitHub asset digests, SHA256SUMS and INSTALL_VALIDATION.json.
- A fresh Python 3.12.14 environment on the runner installed `batchlens-bio==0.3.0` from the official index, outside the checkout. Its `confounded-time` demo correctly returns `NON_ESTIMABLE`, with tool version 0.3.0 and output/ruleset 1.1. The downloaded installation artifact contains both report languages, canonical JSON, tables, manifest and COMPLETE; all seven manifest output hashes match.
- [Release/asset evidence](validation/v0.3.0-release.json) and [official-index/install evidence](validation/v0.3.0-pypi.json) distinguish runner download checks from local checks. Thirteen smaller assets were fully downloaded and independently hashed locally. The three local installer transfers were interrupted after slow partial downloads; those partial files are not presented as installation or local checksum evidence. Their full download hashes are established by the linked successful publishing job and compared to GitHub's recorded asset digests.

External user validation, independent statistical expert review, clean end-user OS trials, Apple Developer ID/notarization and Windows Authenticode signing remain open. Engineering and R-oracle checks do not establish those outcomes. The local candidate records below are retained with their original hashes; published artifacts and the v0.3.0 tag are not rewritten by this documentation update.

## 0.3.0 unified workbench candidate — local evidence

The owner approved consolidating the scDesign Audit prototype into BatchLens. This section describes the 0.3.0 candidate; historical remote runs below establish earlier versions only. These are retained pre-publication records; final remote publication evidence is recorded above.

- Python 3.12.14 and 3.13.9 on macOS arm64: **158 tests passed on each**, including the independent R oracle. [3.12 JUnit](validation/v0.3.0-tests-py312.xml), [3.13 JUnit](validation/v0.3.0-tests-py313.xml). The 3.13 run uses a new locked environment and a non-editable installed package. Hostnames are removed from shared JUnit copies.
- Python suite statement coverage: **88% overall** (native GUI paths are exercised separately); new quick adapter 96%, donor support 96%, localization 100%. Coverage is engineering evidence, not a scientific-validity score.
- Scientific regressions verify exact quick/advanced output parity, explicit paired-unit blocking, no increase in units after cell multiplication or library splitting, missing cell-type groups, within-condition dominance, inclusive count thresholds, strict share thresholds and optional-timepoint confounding.
- Browser source QA: **17 grouped checks passed** in Chrome, including 3 quick + 7 advanced demos, actual uploads, keyboard mapping focus, explicit comparison, thresholds, handoff, localized HTML/ZIP downloads and matching hashes, 390px layouts, malformed inputs and inert filename markup. No JavaScript errors or external requests. The same 17 groups also pass against the built, installed wheel, including individual-slot drag/drop and expanded finding evidence. [Installed browser record](validation/v0.3.0-browser-qa.json).
- Static checks: Ruff lint/format, mypy, JavaScript syntax and Prettier pass. The candidate added an installed-wheel browser job; the completed remote execution is recorded above.

Wheel and sdist each install into a separate fresh environment **outside the source checkout**. Both pass explicit CLI validation/audit, all seven advanced demos, all three quick demos, packaged browser resources, both HTML languages, HTTP/ZIP downloads and `pip check`. [Exact artifact hashes and clean-install record](validation/v0.3.0-package-smoke.json). Twine metadata checks pass. The final source archive includes the macOS staging fix and is reinstalled/tested again; the runtime wheel is byte-identical to the one used for browser/native validation. For a specific downloaded artifact, use its adjacent INSTALL_VALIDATION.json and SHA256SUMS; validation files embedded in source archives are earlier build snapshots.

Local macOS arm64: frozen runtime passes all seven advanced and three quick scenarios, both localized reports and downloads. The native window loads and triggers an audit through JavaScript. Ad-hoc signing and DMG verification pass. The delivered DMG was mounted read-only; its bundled app independently passes signature verification and all ten frozen scenarios. [Mounted-installer checks](validation/v0.3.0-installed-dmg-smoke.json). [Frozen checks](validation/v0.3.0-desktop-smoke.json), [native window](validation/v0.3.0-desktop-gui-smoke.json), [installer hash/signing scope](validation/v0.3.0-macos-installer.json).

The first build encountered Finder metadata reattached under Documents. Recovery copied the generated app to local scratch before signing; this preserved its contents and all old builds. The builder now stages signing and DMG assembly outside the synchronized directory. That staging function was tested against the failed bundle and produced a successfully signed/verified copy. No clean-user-machine or Gatekeeper acceptance claim is made. Other-platform 0.3.0 execution had not run when these local records were created; the completed remote runs are recorded above. External user trials and independent statistical review remain open. Source code, original prototype and all prior report/build folders are retained.

## 0.2.0 browser and desktop validation

- 98 tests pass locally on Python 3.12.14 and Python 3.13.9, including 31 new HTTP/upload/download checks; original scientific and CLI fixtures remain green. Ruff, formatting, mypy, JavaScript syntax and actionlint checks pass. Non-editable installs avoid this Mac's previously documented hidden `.pth` behavior.
- A deterministic concurrent-request regression checks that a completed response releases the audit slot before the client can start its next audit. It reproduced the false `409` seen in a frozen Intel Mac smoke run, then passed after fixing the response/lock ordering.
- Wheel and sdist install into new environments outside the checkout. Both installed artifacts pass CLI checks, seven demos, packaged web-resource checks and live HTTP report/ZIP retrieval. Exact downloadable release artifacts are verified again by the release workflow.
- Local macOS arm64 build: frozen Python, all seven HTTP demos, report/JSON/ZIP downloads, a native window with a JavaScript-triggered audit, ad-hoc signature verification and DMG verification pass. A manually opened app displays the full report and saves a valid ZIP through the native save dialog; quitting stops the server.
- Browser QA: initial/disabled state, multiple-file chooser, balanced uploaded audit, confounded example, inline report and a 760-pixel minimum-window layout (no horizontal overflow) verified. Screenshot: [local UI](web-ui.png).
- The [first remote core matrix](https://github.com/guatou904/batchlens-bio/actions/runs/34654708950) passed on Linux/macOS/Windows, Python 3.12/3.13, plus the R oracle. The [desktop matrix with the UTF-8 report fix](https://github.com/guatou904/batchlens-bio/actions/runs/34655257596) passed native Mac arm64/Intel builds, GUI smoke checks, and actual Windows installation/audit validation.
- Publication is separately gated by the release workflow, which reruns core and native desktop checks on the exact tag. The [release page](https://github.com/guatou904/batchlens-bio/releases) carries the actual publishing run URL, installer/package hashes and validation JSON. Source checks alone are not publication evidence.
- Public signing credentials are not provisioned. Mac ad-hoc verification does not establish Developer ID/notarization or Gatekeeper acceptance; Windows Authenticode signing and clean end-user OS trials remain open.

## 0.1.0 published baseline

Status: [GitHub Release v0.1.0](https://github.com/guatou904/batchlens-bio/releases/tag/v0.1.0) published at 2026-09-11 19:49:59 UTC (2026-09-12 Asia/Shanghai); [PyPI 0.1.0](https://pypi.org/project/batchlens-bio/0.1.0/) published at 2026-09-11 20:39 UTC. The [initial CI run](https://github.com/guatou904/batchlens-bio/actions/runs/34640147143) passed all five jobs on commit `af84864b8ec361f5a51e43ef7405ee7b1df4ef2c`: Linux/macOS × Python 3.12/3.13 plus the independent R oracle. This is engineering evidence, not proof of external adoption or an independent scientific review.

| Check | Executed result | Evidence |
|---|---|---|
| Python 3.12.14, macOS 26.2 arm64 | 67 tests passed, 0 skipped/failures | [JUnit](validation/tests-py312.xml) |
| Python 3.13.9, same platform | 67 tests passed, 0 skipped/failures | [JUnit](validation/tests-py313.xml) |
| Scientific oracle | Five model.matrix / QR counterexamples independently constructed in R 4.6.1, compared to NumPy SVD | `scripts/verify_r_oracle.R`, `tests/test_science.py`; included in both test runs |
| Static code checks | Ruff lint/format and mypy passed | Commands below and successful remote run links |
| Distribution | Wheel and sdist built; both pass Twine metadata checks | Published SHA256SUMS and PyPI hashes match |
| Clean installation | Separate fresh Python 3.12 environments for wheel and sdist; outside checkout; all seven packaged demos passed, pip check clean | `scripts/package_smoke.py`; [smoke record](validation/package-smoke.json) |
| HTML | Actual synthetic and public-derived outputs inspected in Chrome 153; 1280×1000 desktop and 390×844 phone; no overflow or external requests | [Browser record](validation/visual-qa.json), [actual preview](demo.html), [screenshot](demo-preview.png) |
| Public metadata | Fixed HumanPilot revision and SHA256; 12 samples / 3 units, NOT_ASSESSED for unsupported independent sampling | [Provenance and reproduction](public-data.md) |
| Performance | 1,000 samples / 50 columns: core audit 0.0852 s, process peak RSS 90,718,208 bytes | [Measurement](validation/performance.json); includes aliasing, excludes file loading/report rendering/install; one measurement, not a benchmark guarantee |

JUnit hostname attributes are omitted from the shared copy; test outcomes are unchanged. The public example and screenshot contain no private study data. Public metadata are fetched explicitly and not bundled.

## Actual GitHub release

- Tag `v0.1.0` points to commit `0f9ae4560506cdcac7d23444751820792fe9af0a`.
- [Release workflow](https://github.com/guatou904/batchlens-bio/actions/runs/34640763878) passed all six jobs, including the repeated OS/Python matrix, R oracle, build, clean installation and publication.
- Each matrix job reports 66 passed and one R test skipped; the required separate R job executes that independent test over five fixtures. Local runs include R and report 67 passed.
- Downloaded wheel/sdist/demo/installation-record hashes match the published SHA256SUMS. Wheel and sdist also match the remote clean-install record byte for byte.
- [Post-publication installation evidence](validation/github-release-v0.1.0.json) records the downloaded artifacts and installation results.
- Five assets exist: wheel, sdist, real HTML demo, INSTALL_VALIDATION.json and SHA256SUMS. Published files and tag are preserved; this document may be updated on main without rewriting the release.

## Actual PyPI release

- [Trusted Publisher workflow](https://github.com/guatou904/batchlens-bio/actions/runs/34645331743) passed publication and installation from the official index. PyPI account `guatou` registered the GitHub publisher for `guatou904/batchlens-bio`, `pypi.yml`, environment `pypi`; no long-lived token is stored in the repository.
- [Local clean-install evidence](validation/pypi-v0.1.0.json): Python 3.12.14, fresh environment, official index, seven demos plus explicit validate/audit and pip check. All passed outside the checkout.
- Both official PyPI artifact SHA256 hashes match the existing GitHub Release. The pip installation report identifies the wheel from files.pythonhosted.org; no local package was substituted.
- Main requires the four OS/Python CI jobs and scientific-oracle check, with strict up-to-date checks and administrator enforcement. Force pushes/deletion of main are disabled.
- Published package documentation is a release-time snapshot. Current publication status and documentation updates live on main; published v0.1.0 artifacts and tag are not rewritten.

## Reproduce

```sh
uv sync --locked --no-editable --python 3.12
uv run --no-editable ruff check .
uv run --no-editable ruff format --check src tests scripts examples
uv run --no-editable mypy
uv run --no-editable pytest
uv run --no-editable python -m build
uv run --no-editable twine check dist/*.whl dist/*.tar.gz
uv run --no-editable python scripts/package_smoke.py --dist dist --out /tmp/batchlens-smoke-new
```

Use a new smoke output path. Repeat with Python 3.13 in a separate environment. Install R to execute the independent oracle; without R those tests skip locally. The dedicated CI oracle job requires R and must pass.

Workflow static validation: actionlint 1.7.12 passed for CI, GitHub Release and the manual PyPI workflow. This is not a remote execution result. See [publication runbook](publishing.md).

## Open evidence and release gates

- Remote CI and the final tag workflow are complete.
- GitHub repository, version tag and release assets are complete; links above record execution evidence.
- PyPI Trusted Publisher configuration, official distribution and clean installation are complete.
- External user validation, comparative task trials with BatchQC/ExploreModelMatrix and independent statistical review. Source-level research and base R comparisons do not complete those tasks.
- Maintainer review of release checklist; BatchLens remains the main active project.

See [implementation decisions](decisions.md) for the owner's authorization to proceed with a bounded exploratory release despite incomplete external validation. No task has been silently marked as done.
