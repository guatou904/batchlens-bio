# One product, two entry points

BatchLens Bio 0.3.0 incorporates the scDesign Audit workbench prototype. BatchLens is the maintained product; the prototype remains available as historical source, not a second release target. Existing BatchLens sample/design inputs and CLI commands remain supported. This is an input/UX consolidation, not equivalence between the old prototype's rank warnings and BatchLens's explicit contrast test.

## Quick check

1. Open `batchlens serve`, choose **Quick check**, and load a UTF-8 CSV/TSV with one row per cell. Limits: 10 MiB, 100,000 rows, 256 columns; up to 200 characters per column name. CSV quoting, header uniqueness and field counts are checked before adaptation.
2. Confirm five distinct columns: sample/library, donor/biological unit, condition, technical batch, cell type. Unambiguous aliases are suggested; biological independence is not inferred. Missing values, conflicting assignments within a sample and selected duplicate cell IDs fail explicitly.
3. Optionally choose timepoint as a categorical adjustment. It is off by default and must use a different column from the target. For a time-group comparison, map that column to condition; do not add a duplicate time adjustment. Continuous covariates belong in advanced mode.
4. Explicitly select target minus reference and independent or paired sampling. Independent means one sample per unit. Paired means exactly two target levels and one sample per level per unit, with a unit fixed-effect block. Unsupported repeated structures remain NOT_ASSESSED. No automatic pairing or removal of adjustment terms occurs.
5. Review configurable coverage thresholds, then run. Defaults: at least 3 units each contributing at least 20 cells; flag largest-unit share strictly above 0.6. Counts are pooled within unit × condition × cell type. These are descriptive review thresholds, not power or scientific-validity cutoffs.

Only selected columns enter the standard inputs. If no cell-ID column is selected, generated row identifiers link observations but do not prove uniqueness of original cells. The report explicitly records this limitation, column mapping and the SHA256 of the original file.

A cell table cannot recover planned samples or units entirely missing from the export. Use an advanced sample manifest to preserve those units. Cell types absent from all observations cannot be invented; observed types missing in a declared condition receive an explicit zero row. More cells and technical libraries never increase the number of declared units. Cell-type thresholds do not fit separate subgroup contrast models.

## Continue in advanced mode

**Use as advanced input** creates `samples.tsv`, `observations.tsv` and `design.yaml` in browser memory. It switches modes without running an audit. The files can be downloaded and edited. JSON-formatted design content is valid YAML and follows the same StudySpec schema. Standard input uses named sample/unit/condition/batch columns; original unused columns are excluded.

Both modes call `service.run_audit` and the same `design.py`. For unchanged converted inputs, all scientific JSON fields match; quick mode additionally records `input_adapter`. Advanced reruns do not retain the original quick mapping automatically. Keep the original report/manifest when preserving that provenance matters.

Advanced group selection/drop accepts YAML as design, `observations`, `cells`, `spots` prefixes as observations, and `assay`/`assays` prefixes as assay links. Remaining CSV/TSV files are samples. Ambiguous duplicate roles fail; use a named field for custom filenames. Combined limit: 32 MiB; YAML: 1 MB. [Full contract](input-schema.md).

## Reports and compatibility

Every bundle includes both HTML languages and a selected-language `report.html`. Language changes presentation only; canonical JSON keys, finding IDs and evidence stay stable. CLI `audit` and `demo` accept `--language en|zh`. Output schema/ruleset are 1.1, adding `cell_support` and optional `input_adapter`; consumers enforcing 1.0 must update their accepted version. Input YAML remains 1.0, with optional `cell_coverage`. Existing declarations without it keep the previous scientific checks.

The report ZIP contains one audit-named directory. `manifest.json` hashes both localized reports and all other listed outputs. Raw input tables and original ID maps are not bundled. Downloaded converted inputs are a separate, explicit user action and contain source identifiers. Labels, mapped column names and design values can still be identifying; aliases do not make them anonymous.

The unified workbench accepts CSV/TSV metadata. The old prototype's optional h5ad reader has not been ported. Export relevant `adata.obs` columns first; expression matrices are never needed. No rule-ID mapping between prototype and BatchLens is promised. Existing prototype reports and source files are retained.
