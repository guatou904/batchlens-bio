# Browser and desktop guide

Both interfaces run the same metadata validation, audit and report pipeline as the CLI. They make no network requests for analysis. The scientific scope and the meanings of `ESTIMABLE`, `NON_ESTIMABLE` and `NOT_ASSESSED` are unchanged.

## Local browser

Install BatchLens Bio 0.2.0 (or install this checkout with `python -m pip install .`), then run:

```sh
batchlens serve
```

The default browser opens a URL like `http://localhost:54321/<session-key>/`. Keep the entire URL, including its session key. A free port is chosen automatically; the service listens only on this computer. Options:

```sh
batchlens serve --port 8765
batchlens serve --no-browser
batchlens serve --out "/path/to/reports"
```

1. Drop `samples.csv` (or `.tsv`) and `design.yaml` (or `.yml`) into the large drop area. You can also click it to choose multiple files, or use each named field.
2. Add optional observations or assays under **Optional metadata**. For a combined drop, filenames starting with `observations`, `cells`, `spots` or `assays` are assigned to the corresponding optional field; otherwise drop them into the named field explicitly. Use one file per field.
3. Click **Run Audit**. The full HTML report appears on the page, including findings and numerical evidence. A non-estimable contrast is a completed audit with findings, not a failed execution.
4. Use **Save HTML** or **Download report bundle** to export results. The complete bundle is also saved automatically to a new folder under `~/BatchLens Audits`, or your chosen `--out` parent. Closing the app does not erase completed reports.

The seven **Run example** scenarios require no input files. Their downloadable templates are synthetic and must be adapted to the actual study. Consult the [input schema](input-schema.md) when writing a design.

Files must be UTF-8 encoded, total at most 32 MiB, and the design file at most 1 MB. Use `batchlens audit` for larger optional tables. The existing 100,000-sample / 256-model-column guard still applies. One audit runs at a time per application instance.

Stop the local service with **Quit BatchLens** or Ctrl+C. If a browser cannot be opened automatically, copy the printed URL into one. After restarting, previous reports can be opened directly from their saved folders; the new session does not expose old reports over HTTP.

## Desktop installation

Desktop installers are built by the [Desktop installers workflow](https://github.com/guatou904/batchlens-bio/actions/workflows/desktop.yml) and attached to a validated [GitHub release](https://github.com/guatou904/batchlens-bio/releases). Users do not need Python, pip or a virtual environment.

| Download | Installation |
|---|---|
| `BatchLens-Bio-0.2.0-macOS-arm64.dmg` | Apple Silicon Mac: open the disk image, drag **BatchLens Bio.app** into Applications, then open it. |
| `BatchLens-Bio-0.2.0-macOS-x86_64.dmg` | Intel Mac: follow the same steps with the Intel build. |
| `BatchLens-Bio-0.2.0-Windows-x64-Setup.exe` | Windows 10 version 2004+ / Windows 11 x64: run the installer, then launch BatchLens Bio from Start. |

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

On macOS the script verifies the app's ad-hoc code signature, runs all seven demos through the frozen HTTP service, checks report downloads, optionally tests a native window and JavaScript-triggered audit, then creates and verifies the DMG. On Windows it builds the executable directory; `packaging/windows.iss` creates the installer using Inno Setup 6. CI verifies the bootstrapper's Microsoft signature, installs the resulting EXE into a fresh directory, and repeats the audit checks using that installed application.

The release workflow waits for core CI and all three desktop builds, collects installers and validation JSON, and hashes every downloadable asset in `SHA256SUMS`. Existing releases are never replaced. Add Developer ID/notarization and Windows signing through a separately provisioned signing service before claiming trusted-publisher distribution.

The shell uses [pywebview's native engines](https://pywebview.flowrl.com/guide/installation.html), with downloads enabled through its [documented settings](https://pywebview.flowrl.com/api/). Windows runtime detection and installation follow [Microsoft's WebView2 distribution guide](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution).

## Local-service boundary

No account, remote API, analytics, CDN or cloud service is used by the UI. The server binds to `127.0.0.1`, uses a random per-launch URL key, validates Host/Origin, rejects cross-site requests, limits request sizes, and serves only packaged resources and registered completed reports. Raw uploads are held in memory. Report HTML is escaped and displayed in a script-disabled frame. Browser history may retain the launch URL; the key expires when that instance stops. This is a local application, not a multi-user network server.
