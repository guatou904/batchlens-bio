"""Loopback-only UI, with a per-launch capability URL and bounded in-memory uploads."""

import base64
import binascii
import io
import json
import secrets
import threading
import webbrowser
import zipfile
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path
from typing import Any

from batchlens import __version__
from batchlens.config import InputError
from batchlens.service import CASES, demo_sources, run_audit
from batchlens.sources import Upload

MAX_UPLOAD_BYTES = 32 * 1024 * 1024
MAX_REQUEST_BYTES = 45 * 1024 * 1024
FIELDS = {"samples", "design", "observations", "assays"}


def decode_uploads(payload: Any) -> dict[str, Upload]:
    if not isinstance(payload, dict) or set(payload) != {"files"}:
        raise InputError("Supply samples and design files")
    files = payload["files"]
    if not isinstance(files, dict) or not {"samples", "design"} <= files.keys():
        raise InputError("Both samples and design are required")
    if files.keys() - FIELDS:
        raise InputError("Unknown file field")
    uploads = {}
    total = 0
    for role, value in files.items():
        if not isinstance(value, dict) or set(value) != {"name", "data"}:
            raise InputError(f"{role}: invalid file")
        name, content = value["name"], value["data"]
        if not isinstance(name, str) or not 1 <= len(name) <= 255:
            raise InputError(f"{role}: invalid filename")
        if any(c in name for c in ("/", "\\", "\x00", "\r", "\n")):
            raise InputError(f"{role}: use a filename without a directory")
        extensions = {".yaml", ".yml"} if role == "design" else {".csv", ".tsv"}
        if Path(name).suffix.lower() not in extensions:
            raise InputError(f"{role}: expected {' or '.join(sorted(extensions))}")
        if not isinstance(content, str):
            raise InputError(f"{role}: invalid file encoding")
        try:
            raw = base64.b64decode(content, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise InputError(f"{role}: invalid file encoding") from exc
        total += len(raw)
        if total > MAX_UPLOAD_BYTES:
            raise InputError(
                "Files exceed the combined 32 MiB limit; use the CLI for larger inputs"
            )
        if not raw:
            raise InputError(f"{role}: file is empty")
        if role == "design" and len(raw) > 1_000_000:
            raise InputError("Design configuration exceeds 1 MB")
        uploads[role] = Upload(name, raw)
    return uploads


class AuditServer(ThreadingHTTPServer):
    # Wait for active audit writes when closing; every connection has a read timeout.
    daemon_threads = False
    allow_reuse_address = False

    def __init__(self, out: Path | None = None, port: int = 0) -> None:
        if not 0 <= port <= 65535:
            raise InputError("Port must be between 0 and 65535")
        self.out = (out or Path.home() / "BatchLens Audits").expanduser().resolve()
        self.out.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.token = secrets.token_urlsafe(32)
        self.busy = threading.Lock()
        self.bundles: dict[str, Path] = {}
        super().__init__(("127.0.0.1", port), AuditHandler)
        self.origin = f"http://localhost:{self.server_port}"
        self.url = f"{self.origin}/{self.token}/"

    def run(self, files: dict[str, Upload], case: str | None = None) -> dict[str, Any]:
        run_id = datetime.now().strftime("audit-%Y%m%d-%H%M%S-") + secrets.token_hex(6)
        out = self.out / run_id
        result = run_audit(
            files["samples"],
            files["design"],
            out,
            files.get("observations"),
            files.get("assays"),
            {"kind": "SYNTHETIC", "title": case} if case else None,
        )
        self.bundles[run_id] = out
        return {
            "id": run_id,
            "counts": result["counts"],
            "contrasts": result["contrasts"],
            "findings": result["findings"],
            "saved_to": str(out),
            "synthetic": case,
        }


class AuditHandler(BaseHTTPRequestHandler):
    server: AuditServer
    server_version = "BatchLens"
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, format: str, *args: Any) -> None:
        # URLs contain a capability token; inputs/errors may contain sensitive metadata.
        pass

    def respond(
        self, status: int, data: bytes, mime: str = "application/json", filename: str | None = None
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; frame-src 'self'; "
            "frame-ancestors 'self'; base-uri 'none'; form-action 'none'",
        )
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass  # The audit bundle is still saved if its browser closes.

    def json(self, status: int, value: Any) -> None:
        self.respond(status, json.dumps(value, allow_nan=False).encode())

    def route(self) -> str | None:
        hosts = {f"localhost:{self.server.server_port}", f"127.0.0.1:{self.server.server_port}"}
        origins = {f"http://{host}" for host in hosts}
        if (
            self.headers.get("Host") not in hosts
            or self.headers.get("Origin", self.server.origin) not in origins
            or self.headers.get("Sec-Fetch-Site") == "cross-site"
        ):
            self.json(403, {"error": "Only this local BatchLens window may access the service"})
            return None
        prefix = f"/{self.server.token}/"
        if not self.path.startswith(prefix):
            self.json(404, {"error": "Open the complete URL printed by BatchLens"})
            return None
        return self.path[len(prefix) :]

    def do_GET(self) -> None:
        route = self.route()
        if route is None:
            return
        if route in {"", "app.css", "app.js"}:
            name = route or "index.html"
            mime = {
                "index.html": "text/html; charset=utf-8",
                "app.css": "text/css",
                "app.js": "text/javascript",
            }[name]
            self.respond(
                200, resources.files("batchlens").joinpath("resources/web", name).read_bytes(), mime
            )
        elif route == "api/info":
            self.json(
                200,
                {
                    "version": __version__,
                    "cases": CASES,
                    "output": str(self.server.out),
                    "max_upload_bytes": MAX_UPLOAD_BYTES,
                },
            )
        elif route.startswith("examples/"):
            parts = route.split("/")
            if len(parts) != 3 or parts[1] not in CASES:
                self.json(404, {"error": "Unknown example"})
                return
            files = demo_sources(parts[1])
            source = next((file for file in files.values() if file.name == parts[2]), None)
            if source is None:
                self.json(404, {"error": "Unknown example file"})
                return
            self.respond(200, source.data, "application/octet-stream", source.name)
        elif route.startswith("reports/"):
            self.report(route)
        else:
            self.json(404, {"error": "Not found"})

    def report(self, route: str) -> None:
        parts = route.split("/")
        folder = self.server.bundles.get(parts[1]) if len(parts) == 3 else None
        if folder is None or not (folder / "COMPLETE").is_file():
            self.json(404, {"error": "Report not found in this session"})
            return
        name = parts[2]
        try:
            if name == "bundle.zip":
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
                    for path in sorted(folder.rglob("*")):
                        if path.is_file() and not path.is_symlink():
                            archive.write(
                                path, f"{folder.name}/{path.relative_to(folder).as_posix()}"
                            )
                self.respond(200, buffer.getvalue(), "application/zip", f"{folder.name}.zip")
            elif name in {"report.html", "download.html", "result.json"}:
                actual = "report.html" if name == "download.html" else name
                mime = "application/json" if actual.endswith("json") else "text/html; charset=utf-8"
                download = actual if name != "report.html" else None
                self.respond(200, (folder / actual).read_bytes(), mime, download)
            else:
                self.json(404, {"error": "Unknown report file"})
        except OSError:
            self.json(500, {"error": "Cannot read saved report; check the output folder"})

    def do_POST(self) -> None:
        route = self.route()
        if route is None:
            return
        if route != "api/audit" and route != "api/quit" and not route.startswith("api/demo/"):
            self.json(404, {"error": "Not found"})
            return
        if not self.server.busy.acquire(blocking=False):
            self.json(409, {"error": "An audit is already running. Please wait for it to finish."})
            return
        try:
            if self.headers.get_content_type() != "application/json":
                self.json(415, {"error": "Expected application/json"})
                return
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
                self.json(400, {"error": "A valid Content-Length is required"})
                return
            length = int(lengths[0])
            if self.headers.get("Transfer-Encoding") or not 0 < length <= MAX_REQUEST_BYTES:
                self.json(413, {"error": "Request is too large; files may total at most 32 MiB"})
                return
            body = self.rfile.read(length)
            if len(body) != length:
                raise InputError("Incomplete upload. Please try again.")
            payload = json.loads(body)
            if route == "api/quit":
                self.json(200, {"stopped": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            if route.startswith("api/demo/"):
                case = route.removeprefix("api/demo/")
                files = demo_sources(case)
            else:
                case = None
                files = decode_uploads(payload)
            self.json(200, self.server.run(files, case))
        except (InputError, ValueError, UnicodeError, RecursionError) as exc:
            message = str(exc) if isinstance(exc, InputError) else "Invalid JSON request"
            self.json(400, {"error": message})
        except TimeoutError:
            self.json(408, {"error": "Upload timed out. Please try again."})
        except OSError:
            self.json(
                500, {"error": "Cannot save report. Check free space and folder permissions."}
            )
        except Exception:
            self.json(
                500,
                {
                    "error": "Internal error. No successful audit is claimed. "
                    "Please report a minimal, de-identified reproducer."
                },
            )
        finally:
            self.server.busy.release()


def serve(port: int = 0, out: Path | None = None, open_browser: bool = True) -> int:
    with AuditServer(out, port) as server:
        print(f"BatchLens Bio: {server.url}", flush=True)
        print(f"Reports: {server.out}\nPress Ctrl+C or use Quit BatchLens to quit.", flush=True)
        if open_browser:
            try:
                if not webbrowser.open(server.url):
                    print("Browser did not open. Open the URL above manually.", flush=True)
            except webbrowser.Error:
                print("Browser did not open. Open the URL above manually.", flush=True)
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            print("\nBatchLens stopped. Saved reports remain in the output folder.")
    return 0
