# BatchLens Bio

[English](https://github.com/guatou904/batchlens-bio/blob/main/README.md) | [简体中文](https://github.com/guatou904/batchlens-bio/blob/main/README.zh-CN.md)

**Experimental-design and batch-confounding audits for single-cell and spatial metadata.**

BatchLens checks declared experimental units, target-by-batch coverage and whether a specific contrast is estimable under an additive fixed-effects model. It produces an offline HTML report, JSON findings and auditable tables. It never fits or corrects expression data.

**0.3.0 unified workbench:** start with a cell metadata table or an explicit samples/YAML design. Both paths use the same audit engine, with Chinese/English interfaces and offline reports. [Migration and scope](docs/quick-check.md).

[GitHub Releases](https://github.com/guatou904/batchlens-bio/releases/tag/v0.3.0) · [PyPI](https://pypi.org/project/batchlens-bio/0.3.0/) · [Browser / desktop guide](docs/desktop.md)

Version 0.3.0 is published. The [validation record](docs/validation-record.md) links the release-commit checks, installer/package download hashes and fresh installation from the official PyPI index.

## Why another tool?

Keep using scIB/kBET/LISI for integration evaluation. Good embedding mixing cannot recover information absent from an experimental design. If D0 samples were processed only in run A and D7 only in run B, `time + run` cannot distinguish the time effect from run.

BatchQC and ExploreModelMatrix already provide valuable confounding/design diagnostics. BatchLens offers a narrowly scoped CLI, local browser UI and desktop app that connects experimental-unit checks, explicit contrasts, machine-readable findings and offline delivery. It is a workflow tool using established linear algebra, not a new statistical method. See [competitor research](https://github.com/guatou904/batchlens-bio/blob/main/COMPETITOR_ANALYSIS.md).

## Open the unified workbench

With Python 3.12 or 3.13, install the release:

```sh
python -m pip install "batchlens-bio==0.3.0"
batchlens serve
```

For a source checkout or development branch, use `python -m pip install .` instead.

Choose a synthetic example to see a report immediately, with no private data.
The interface starts in Chinese; **EN** switches to English without rerunning the audit.

| Entry | Start with | Confirm |
|---|---|---|
| Quick check | One cell-level CSV/TSV | Five column roles, comparison direction, sampling structure and coverage thresholds |
| Advanced design | Samples CSV/TSV + design YAML | Explicit contrasts, categorical/numeric covariates, independent or paired model; optional observations/assays |

Quick mode previews metadata and can convert it into standard advanced inputs. Both paths call the same contrast engine. Quick mode includes three original synthetic cell tables; advanced mode keeps all seven existing scenarios. [Quick workflow and boundaries](docs/quick-check.md).

Files stay on your computer. Raw uploads remain in memory; completed reports are saved under `~/BatchLens Audits`. Download either language's HTML, the canonical JSON or a ZIP containing both reports, tables and hashes. No account, cloud upload or expression matrix is needed.

![BatchLens unified workbench](https://raw.githubusercontent.com/guatou904/batchlens-bio/v0.3.0/docs/workbench-home.png)

**Desktop:** choose the Mac Apple Silicon, Intel Mac or Windows x64 installer from [GitHub Releases](https://github.com/guatou904/batchlens-bio/releases/tag/v0.3.0). Python and dependencies are included. Version 0.3.0 uses this unified interface; v0.2.0 installers retain the earlier advanced interface. See [platform evidence and alpha signing status](docs/desktop.md).

**CLI remains available:**

```sh
batchlens demo --case balanced --out demo-balanced
batchlens demo --case confounded-time --out demo-confounded --language zh --fail-on none
```

The second example deliberately shows `NON_ESTIMABLE`; exit-policy selection does not hide findings. Each output path must be new and have an existing parent. Other advanced examples: `partial-overlap`, `redundant-nuisance`, `paired`, `spatial-replicates`, `mixed-assays`.

[New Chinese quick report](docs/quick-demo.zh.html) · [English report](docs/quick-demo.en.html) · [Public spatial example](docs/public-data.md)

## Your metadata

Prepare a CSV/TSV with one row per sample and a YAML design declaration. IDs are strings; declare the true experimental unit rather than assuming every cell or spot is independent.

```sh
batchlens validate --samples samples.tsv --design design.yaml
batchlens audit --samples samples.tsv --design design.yaml --out audit-001
batchlens audit --samples samples.tsv --design design.yaml \
  --observations cells.tsv --assays assays.tsv --out audit-002
```

The [input guide](https://github.com/guatou904/batchlens-bio/blob/main/docs/input-schema.md) specifies columns and includes a complete configuration. Export only metadata from your analysis environment; h5ad, expression matrices and spatial images are not required or read.

## Understand the result

| Contrast status | Meaning |
|---|---|
| `ESTIMABLE` | Algebraically estimable under the declared model; **not** a power, biological validity or causality pass |
| `NON_ESTIMABLE` | The requested contrast cannot be uniquely determined under that model |
| `NOT_ASSESSED` | Sampling structure is outside the supported independent/paired model; descriptive checks still run |

Rank deficiency does not necessarily invalidate every contrast. Partial target-by-batch overlap is not automatically complete confounding. More cells or technical sections do not create more experimental units. See [methods](https://github.com/guatou904/batchlens-bio/blob/main/docs/methods.md) and [interpretation](https://github.com/guatou904/batchlens-bio/blob/main/docs/interpretation.md).

## Output and automation

- `report.html`: selected language, self-contained; `report.en.html` and `report.zh.html` are always included. No network or JavaScript required.
- `result.json`: canonical English keys/rule IDs/text, output schema and ruleset 1.1; design YAML remains schema 1.0. Adds `cell_support` and optional quick `input_adapter`.
- `tables/*.tsv`: sample/unit coverage, annotation summaries and optional `cell_support.tsv`.
- `manifest.json`: input/output SHA256 hashes, environment and dependency versions.
- `COMPLETE`: written last; its absence indicates an incomplete bundle.

IDs are replaced with local aliases; labels/design values can still identify people. Review **all** outputs before sharing. No original ID map, absolute input paths or cell-level rows are exported. TSV formula-like labels are prefixed with an apostrophe for spreadsheet safety; JSON preserves original scientific labels.

Exit codes: `0` completed, `1` internal failure, `2` input/output error, `3` findings exceed policy. `--fail-on critical` is the default. Use `--fail-on warning` in strict CI so unsupported models do not pass silently; `--fail-on none` changes only exit behavior. A successful `validate` command does not test estimability.

## Supported scope

Independent: one sample per declared experimental unit. Paired: one sample at each of two target levels per unit, with an explicit unit block. Categorical target; additive categorical/numeric adjustment. Multi-batch samples and more complex repeated sampling produce `NOT_ASSESSED`, never silent aggregation. No interaction terms, mixed-effects inference, power analysis, causal inference, spatial correlation test or batch correction.

Metadata-only audits cannot verify randomization, independence or unmeasured confounding. The study specification is supplied by the analyst. Near-singular designs require numerical review. Current resource guard: at most 100,000 samples and 256 encoded columns; this is a safety limit, not a performance guarantee.

## Development and verification

```sh
uv sync --locked --no-editable
uv run --no-editable pytest
uv run --no-editable ruff check .
uv run --no-editable mypy
uv run --no-editable python -m build
uv run --no-editable twine check dist/*.whl dist/*.tar.gz
```

The [validation record](https://github.com/guatou904/batchlens-bio/blob/main/docs/validation-record.md) distinguishes executed tests from pending external evidence. R's `model.matrix`/QR supplies an independent oracle for selected scientific fixtures; see `scripts/verify_r_oracle.R`. The CI and release workflows validate tests, package installation outside the source directory, and demo output. Remote CI success is claimed only with a recorded run URL.

See [CONTRIBUTING.md](https://github.com/guatou904/batchlens-bio/blob/main/CONTRIBUTING.md), [CITATION.cff](https://github.com/guatou904/batchlens-bio/blob/main/CITATION.cff), [release checklist](https://github.com/guatou904/batchlens-bio/blob/main/RELEASE_CHECKLIST.md) and [CHANGELOG.md](https://github.com/guatou904/batchlens-bio/blob/main/CHANGELOG.md). MIT-licensed code and synthetic examples; public datasets have their own provenance and terms.

## Project status and feedback

BatchLens is an exploratory alpha project with completed automated tests and clean-install verification. It still needs evaluation in more real research settings; external user validation and independent scientific review are not yet completed. The [validation record](https://github.com/guatou904/batchlens-bio/blob/main/docs/validation-record.md) documents completed checks and outstanding evidence.

Maintainer: [guatou904](https://github.com/guatou904). Usage feedback, minimal reproducible examples and statistical-method suggestions are welcome via [GitHub Issues](https://github.com/guatou904/batchlens-bio/issues). Use synthetic inputs and include the software version when reporting installation or scientific issues. The next iteration prioritizes fixes and actual user feedback.
