# Validation record — 2026-09-12

Status: local release candidate, **not yet published**. No GitHub run/release/PyPI URL exists at this checkpoint. This is engineering evidence, not proof of external adoption or an independent scientific review.

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

- Real GitHub Actions: Linux/macOS × Python 3.12/3.13 and independent R job. Local macOS success is not a Linux result.
- GitHub repository, immutable release tag, actual Release assets and successful run URLs.
- PyPI Trusted Publisher configuration, actual distribution, then clean install from the official index.
- External user validation, comparative task trials with BatchQC/ExploreModelMatrix and independent statistical review. Source-level research and base R comparisons do not complete those tasks.
- Maintainer review of release checklist; BatchLens remains the main active project.

See [implementation decisions](decisions.md) for the owner's authorization to proceed with a bounded exploratory release despite incomplete external validation. No task has been silently marked as done.
