# Changelog

## 0.3.0 — unified workbench, 2026-09-21

- One BatchLens workbench combines quick cell-table import and advanced samples/YAML, using the same scientific core.
- Explicit role mapping, contrast direction, independent/paired declaration, optional timepoint and standard-input conversion.
- Configurable donor representation and dominance checks within cell types/conditions; technical libraries never inflate unit counts.
- Chinese/English UI and offline reports, evidence disclosures, mobile layouts and keyboard navigation.
- Retains advanced file drag/drop, all seven original demos, CLI and native packaging; adds three synthetic quick scenarios.
- Input YAML remains 1.0 with optional `cell_coverage`; output schema/ruleset 1.1 add `cell_support` and quick adapter provenance. JSON remains canonical English.
- Real-browser automation is added to CI; frozen smoke checks cover both entries and both report languages.
- scDesign Audit is retained as the original prototype rather than published as a second product. h5ad import is not part of this consolidation.


## 0.2.0 — 2026-09-12

- `batchlens serve` opens a local browser UI with multi-file selection, drag/drop, optional tables, seven examples, inline reports and HTML/ZIP downloads.
- Shared audit service keeps browser, native desktop and CLI results consistent; raw uploads stay in memory and completed bundles are saved to unique local folders.
- Native BatchLens Bio window and reproducible macOS arm64/Intel DMG and Windows x64 EXE installer builds, including Python and audit dependencies.
- Windows setup checks WebView2; missing runtimes are installed with Microsoft's signed bootstrapper. Initial runtime setup requires internet.
- Loopback-only service with session capability, Host/Origin checks, escaped reports, bounded requests and single-audit execution.
- Core CI includes Windows; packaged-resource, HTTP, frozen runtime, native-window and installed-Windows smoke checks gate desktop releases.
- Desktop alpha builds are not Developer ID/notarized or Authenticode-signed releases. Scientific scope is unchanged.

## 0.1.0 — 2026-09-12

- Metadata-only CLI with strict sample/design/optional observation and assay validation.
- Experimental-unit counts, target/batch coverage, independent and simple paired support checks.
- Explicit contrast estimability with SVD diagnostics; unsupported structures remain NOT_ASSESSED.
- Offline HTML, versioned JSON, tables, input/output hashes and completion marker.
- Seven packaged synthetic demos and an opt-in public spatial metadata example.
- Scientific regression fixtures, independent R oracle, clean-install smoke checks and release workflows.

Exploratory alpha: external user validation and independent scientific review remain pending. No expression correction, causal inference or power guarantee. The GitHub release records publication assets and execution evidence; PyPI publication is tracked separately.
