# Browser and desktop guide

Both interfaces run the same metadata validation, audit and report pipeline as the CLI. They make no network requests for analysis. The scientific scope and the meanings of `ESTIMABLE`, `NON_ESTIMABLE` and `NOT_ASSESSED` are unchanged.

## Local browser

For the 0.3.0 unified workbench, install `batchlens-bio==0.3.0` (or this checkout with `python -m pip install .`), then run:

```sh
batchlens serve
```

The default browser opens a URL like `http://localhost:54321/<session-key>/`. Keep the entire URL, including its session key. A free port is chosen automatically; the service listens only on this computer. Options:

```sh
batchlens serve --port 8765
batchlens serve --no-browser
batchlens serve --out "/path/to/reports"
```

1. Choose **Quick check** for one cell CSV/TSV, or **Advanced design** for samples + design YAML. Quick mode requires explicit column roles, comparison direction and sampling structure. [Quick workflow](quick-check.md).
2. Advanced mode supports combined selection/drop and individual fields. YAML is design; observations/cells/spots and assay prefixes identify optional tables. Other CSV/TSV files are samples. Duplicate roles fail without partially replacing the selection.
3. Run the audit. Overview shows findings, concrete evidence, next steps and optional donor coverage; the full offline report and declared model have separate tabs. `NON_ESTIMABLE` is a completed audit with findings.
4. Switch **EN / 中** to change interface and report language without changing the scientific result. Download localized HTML, canonical JSON or the complete ZIP. Both HTML languages are in every bundle.
5. Completed bundles remain under `~/BatchLens Audits` (or `--out`). Raw uploads stay in memory. Quick-to-advanced conversion creates input files in browser memory and offers separate explicit downloads.

Three quick and seven advanced synthetic demos require no files. All scientific support boundaries remain explicit. Quick upload: 10 MiB / 100,000 rows / 256 columns. Advanced upload: 32 MiB combined / 1 MB YAML. Design guard: 100,000 samples / 256 model columns. One audit runs at a time.

Stop the local service with **Quit BatchLens** or Ctrl+C. If a browser cannot be opened automatically, copy the printed URL into one. After restarting, previous reports can be opened directly from their saved folders; the new session does not expose old reports over HTTP.

## Desktop installation

Version 0.3.0 installers use the unified workbench. Earlier 0.2.0 installers retain the previous advanced interface. Use the actual release assets and linked workflow evidence to identify validated platforms; see [current evidence](validation-record.md).


Desktop installers are built by the [Desktop installers workflow](https://github.com/guatou904/batchlens-bio/actions/workflows/desktop.yml) and attached to a validated [GitHub release](https://github.com/guatou904/batchlens-bio/releases). Users do not need Python, pip or a virtual environment.

| Download | Installation |
|---|---|
| `BatchLens-Bio-0.3.0-macOS-arm64.dmg` | Apple Silicon Mac: open the disk image, drag **BatchLens Bio.app** into Applications, then open it. |
| `BatchLens-Bio-0.3.0-macOS-x86_64.dmg` | Intel Mac: follow the same steps with the Intel build. |
| `BatchLens-Bio-0.3.0-Windows-x64-Setup.exe` | Windows 10 version 2004+ / Windows 11 x64: run the installer, then launch BatchLens Bio from Start. |

macOS 14+ is the desktop release test target. Windows uses Microsoft Edge WebView2. If it is missing, setup installs it using the Microsoft-signed bootstrapper included in the installer; **that first setup requires internet access**. Subsequent audits work offline. Managed computers may require their administrator to install WebView2. Installing a Python package does not install this system runtime.

**Signing status:** the alpha Mac apps are ad-hoc signed and verified, but are not Apple Developer ID signed or notarized. The Windows installer is not Authenticode signed. Gatekeeper or SmartScreen may show an unknown-publisher warning. Do not describe these builds as a notarized or signed public distribution. See the validation record for tested platforms; installation on an unrestricted developer machine is not proof of Gatekeeper approval on a fresh download.

The desktop window uses the same drag/drop fields, examples and downloads as the browser. Close the window to stop its local service. Saved reports remain under your home folder's **BatchLens Audits** directory. The original sample/design files are read into memory, never copied into the saved bundle. Output labels may still identify people; review them before sharing.

## Development and packaging

```sh
uv sync --locked --no-editable --python 3.12 --extra desktop --group desktop-build
uv run --no-editable --extra desktop batchlens desktop
uv run --no-editable --extra desktop --group desktop-build python scripts/build_desktop.py \
  --out artifacts/desktop-new --gui-smoke
```

Choose a new build directory every time. Build outputs are never automatically cleaned. PyInstaller bundles the interpreter, NumPy/pandas, validation libraries, templates, web assets and demo resources. The CLI/browser installation has no desktop dependency. See [PyInstaller bundling](https://pyinstaller.org/en/stable/operating-mode.html) and [platform builds](https://pyinstaller.org/en/latest/usage.html); build each target on that operating system.

On macOS the script verifies the app's ad-hoc code signature, runs seven advanced and three quick demos through the frozen HTTP service, checks report downloads, optionally tests a native window and JavaScript-triggered audit, then creates and verifies the DMG. On Windows it builds the executable directory; `packaging/windows.iss` creates the installer using Inno Setup 6. CI verifies the bootstrapper's Microsoft signature, installs the resulting EXE into a fresh directory, and repeats the audit checks using that installed application.

The release workflow waits for core CI and all three desktop builds, collects installers and validation JSON, and hashes every downloadable asset in `SHA256SUMS`. Existing releases are never replaced. Add Developer ID/notarization and Windows signing through a separately provisioned signing service before claiming trusted-publisher distribution.

The shell uses [pywebview's native engines](https://pywebview.flowrl.com/guide/installation.html), with downloads enabled through its [documented settings](https://pywebview.flowrl.com/api/). Windows runtime detection and installation follow [Microsoft's WebView2 distribution guide](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution).

## Local-service boundary

No account, remote API, analytics, CDN or cloud service is used by the UI. The server binds to `127.0.0.1`, uses a random per-launch URL key, validates Host/Origin, rejects cross-site requests, limits request sizes, and serves only packaged resources and registered completed reports. Raw uploads are held in memory. Report HTML is escaped and displayed in a script-disabled frame. Browser history may retain the launch URL; the key expires when that instance stops. This is a local application, not a multi-user network server.

### macOS build folders

Finder/sync services may attach resource-fork or Finder metadata to bundles under Documents; macOS codesign rejects those attributes and the service can reattach them immediately. The builder copies its newly generated app into a new local scratch directory with `ditto --norsrc --noextattr`, then signs, tests and assembles the disk image there. Only the completed DMG is written to the chosen delivery folder. Scratch folders and original builds remain intact; no files are deleted. The signed app is in the scratch folder and the delivered installer is the verified DMG.
