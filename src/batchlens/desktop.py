"""Native desktop shell. Packaged builds include Python and all audit dependencies."""

import argparse
import json
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

from batchlens import __version__
from batchlens.service import CASES
from batchlens.web import AuditServer


def smoke_test(server: AuditServer, destination: Path) -> None:
    """Exercise HTTP, bundled resources, every scientific demo and downloads after freezing."""
    checks = []
    for case in CASES:
        request = urllib.request.Request(
            server.url + f"api/demo/{case}",
            data=b"{}",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
        for name in ["report.html", "result.json", "bundle.zip"]:
            with urllib.request.urlopen(
                server.url + f"reports/{result['id']}/{name}", timeout=30
            ) as response:
                assert response.status == 200 and response.read()
        checks.append({"case": case, "status": result["contrasts"][0]["status"]})
    for name in ["", "app.js", "app.css", "api/info"]:
        with urllib.request.urlopen(server.url + name, timeout=10) as response:
            assert response.status == 200 and response.read()
    expected = [
        "ESTIMABLE",
        "NON_ESTIMABLE",
        "ESTIMABLE",
        "ESTIMABLE",
        "ESTIMABLE",
        "NOT_ASSESSED",
        "NOT_ASSESSED",
    ]
    assert [check["status"] for check in checks] == expected
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(
            {
                "version": __version__,
                "frozen": bool(getattr(sys, "frozen", False)),
                "checks": checks,
                "http_and_downloads": "passed",
            },
            stream,
            indent=2,
        )


def show_error(message: str) -> None:
    if sys.stderr is not None:
        print(message, file=sys.stderr)
    if sys.platform == "darwin":
        script = (
            'on run argv\ndisplay alert "BatchLens Bio could not start" '
            "message (item 1 of argv) as critical\nend run"
        )
        subprocess.run(["osascript", "-e", script, message], check=False)
    elif sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, "BatchLens Bio", 0x10)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BatchLens Bio desktop")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--smoke-test", type=Path, help="Write frozen runtime validation JSON")
    parser.add_argument(
        "--smoke-gui", type=Path, help="Run a visible example and exit after rendering"
    )
    args = parser.parse_args(argv)
    try:
        with AuditServer(args.out) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                if args.smoke_test:
                    smoke_test(server, args.smoke_test)
                    return 0
                import webview

                webview.settings["ALLOW_DOWNLOADS"] = True
                webview.settings["ALLOW_FILE_URLS"] = False
                window = webview.create_window(
                    "BatchLens Bio",
                    server.url,
                    width=1240,
                    height=900,
                    min_size=(760, 640),
                    background_color="#f5f6f1",
                    text_select=True,
                )
                if window is None:
                    raise RuntimeError("Could not create native window")
                gui_success = threading.Event()

                def finish_gui_smoke() -> None:
                    window.run_js("document.getElementById('demo').click()")

                if args.smoke_gui:
                    window.events.loaded += finish_gui_smoke

                def watch_server() -> None:
                    if args.smoke_gui:
                        deadline = time.monotonic() + 90
                        while time.monotonic() < deadline and worker.is_alive():
                            if server.bundles:
                                # Report rendering is then checked manually in native UI QA.
                                with args.smoke_gui.open("x", encoding="utf-8") as stream:
                                    json.dump(
                                        {
                                            "version": __version__,
                                            "native_window": "loaded",
                                            "javascript_audit": "passed",
                                        },
                                        stream,
                                    )
                                gui_success.set()
                                break
                            time.sleep(0.2)
                        window.destroy()
                    else:
                        worker.join()
                        window.destroy()

                webview.start(watch_server, gui="edgechromium" if sys.platform == "win32" else None)
                if args.smoke_gui and not gui_success.is_set():
                    raise RuntimeError("Native window smoke check did not complete")
            finally:
                server.shutdown()
                worker.join(timeout=10)
        return 0
    except Exception as exc:
        if args.smoke_test or args.smoke_gui:
            # CI uses exit status and the missing completion JSON, never a blocking dialog.
            evidence = args.smoke_test or args.smoke_gui
            try:
                with evidence.with_suffix(".error.json").open("x", encoding="utf-8") as stream:
                    json.dump({"error_type": type(exc).__name__, "message": str(exc)}, stream)
            except OSError:
                pass
            if sys.stderr is not None:
                print(f"Desktop smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        else:
            message = "Check that your home folder is writable and restart the application."
            if isinstance(exc, ModuleNotFoundError):
                message = "Install the desktop extra with pip install 'batchlens-bio[desktop]', "
                message += "or download the desktop installer from the GitHub release."
            if sys.platform == "win32":
                message += " On Windows, use the installer to set up Microsoft WebView2."
            show_error(f"{message}\n\nError type: {type(exc).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
