# Validation record — 2026-09-12

Status: [GitHub Release v0.1.0](https://github.com/guatou904/batchlens-bio/releases/tag/v0.1.0) published at 2026-09-11 19:49:59 UTC (2026-09-12 Asia/Shanghai); PyPI publication pending. The [initial CI run](https://github.com/guatou904/batchlens-bio/actions/runs/34640147143) passed all five jobs on commit `af84864b8ec361f5a51e43ef7405ee7b1df4ef2c`: Linux/macOS × Python 3.12/3.13 plus the independent R oracle. This is engineering evidence, not proof of external adoption or an independent scientific review.

| Check | Executed result | Evidence |
|---|---|---|
| Python 3.12.14, macOS 26.2 arm64 | 67 tests passed, 0 skipped/failures | [JUnit](validation/tests-py312.xml) |
| Python 3.13.9, same platform | 67 tests passed, 0 skipped/failures | [JUnit](validation/tests-py313.xml) |
| Scientific oracle | Five model.matrix / QR counterexamples independently constructed in R 4.6.1, compared to NumPy SVD | `scripts/verify_r_oracle.R`, `tests/test_science.py`; included in both test runs |
| Static code checks | Ruff lint/format and mypy passed | Commands below; remote logs pending |
| Distribution | Wheel and sdist built; both pass Twine metadata checks | Final artifact checksums supplied with local dist and eventual Release |
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
- PyPI Trusted Publisher configuration, actual distribution, then clean install from the official index.
- External user validation, comparative task trials with BatchQC/ExploreModelMatrix and independent statistical review. Source-level research and base R comparisons do not complete those tasks.
- Maintainer review of release checklist; BatchLens remains the main active project.

See [implementation decisions](decisions.md) for the owner's authorization to proceed with a bounded exploratory release despite incomplete external validation. No task has been silently marked as done.
