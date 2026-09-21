BatchLens Bio 0.2.0 adds a local browser interface and native desktop installers to the metadata-only experimental-design audit tool.

It checks experimental units, sample/batch coverage and explicit additive-model contrasts, with independent/paired support boundaries. Outputs include an offline HTML report, versioned JSON findings, tables and hashed provenance. Seven synthetic demos ship in the package.

**Desktop:** download the `.dmg` matching your Mac (arm64 for Apple Silicon, x86_64 for Intel), drag BatchLens Bio into Applications, and open it. Windows x64 users run `Setup.exe`. Python and audit dependencies are bundled. Windows setup provisions WebView2 if missing; that initial setup requires internet access.

**Browser:** install the wheel/source archive with `python -m pip install <downloaded-file>` and run `batchlens serve`. The default browser opens a protected localhost URL. Drag in sample/design files, click **Run Audit**, and view the full report. Optional observations/assays, seven examples, HTML export and ZIP downloads are included.

Reports are saved under `~/BatchLens Audits`. Raw uploaded files stay in memory. No cloud upload or account is used. The UI limit is 32 MiB combined; the existing scientific resource limits still apply. The original validate/audit/demo commands remain available.

**Desktop alpha signing:** Mac apps are ad-hoc signed, but not Developer ID signed or Apple-notarized. Windows installers are not Authenticode signed. OS unknown-publisher warnings may appear. macOS 14+ and Windows 10 2004+ / Windows 11 x64 are the targeted desktop platforms; see the attached workflow evidence for the exact systems actually tested.

`SHA256SUMS` covers every attached installer, package, demo and validation record. Frozen-runtime checks exercise all seven demos and downloads, native-window checks trigger an audit through JavaScript, and the Windows job installs the actual EXE before re-running validation. The attached HTML is a real synthetic demo report.

Limitations: no expression correction, power or causal inference, spatial correlation test, interaction/random-effect model, or guarantee of scientific validity. External user validation and independent scientific review remain pending. Python 3.12/3.13 are the CI targets; platform support should be assessed using the attached successful workflow evidence.

See README, methods, input schema and validation record. GitHub release does not imply PyPI publication; the latter is tracked separately.
