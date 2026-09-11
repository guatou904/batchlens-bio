import base64
import hashlib
import http.client
import io
import json
import threading
import zipfile
from pathlib import Path

import pytest

from batchlens.cli import main
from batchlens.config import InputError
from batchlens.desktop import smoke_test
from batchlens.service import CASES, demo_sources, run_audit
from batchlens.web import AuditServer, decode_uploads


@pytest.fixture
def server(tmp_path):
    with AuditServer(tmp_path / "audits") as instance:
        worker = threading.Thread(target=instance.serve_forever)
        worker.start()
        try:
            yield instance
        finally:
            instance.shutdown()
            worker.join(timeout=5)


def request(server, route="", payload=None, method=None, headers=None, prefix=True):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=20)
    body = json.dumps(payload).encode() if payload is not None else None
    actual_headers = {"Content-Type": "application/json"} if body else {}
    actual_headers.update(headers or {})
    path = f"/{server.token}/{route}" if prefix else route
    connection.request(method or ("POST" if body else "GET"), path, body, actual_headers)
    response = connection.getresponse()
    data = response.read()
    result = (response.status, dict(response.getheaders()), data)
    connection.close()
    return result


def uploads(case="balanced"):
    return {
        "files": {
            role: {"name": source.name, "data": base64.b64encode(source.data).decode()}
            for role, source in demo_sources(case).items()
        }
    }


@pytest.mark.parametrize("case", CASES)
def test_http_matches_shared_cli_pipeline_and_zip(server, tmp_path, case):
    code, _, body = request(server, "api/audit", uploads(case))
    assert code == 200, body
    data = json.loads(body)
    sources = demo_sources(case)
    expected = run_audit(**sources, out=tmp_path / "expected")
    prefix = f"reports/{data['id']}/"
    code, _, body = request(server, prefix + "result.json")
    assert code == 200 and json.loads(body) == expected
    code, headers, body = request(server, prefix + "bundle.zip")
    assert code == 200 and headers["Content-Type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        root = data["id"] + "/"
        manifest = json.loads(archive.read(root + "manifest.json"))
        for path, digest in manifest["outputs"].items():
            assert hashlib.sha256(archive.read(root + path)).hexdigest() == digest
        assert archive.read(root + "COMPLETE")
        assert not any(name.endswith(("samples.tsv", "design.yaml")) for name in archive.namelist())
    assert Path(data["saved_to"]).parent == server.out


def test_csv_upload_and_native_frozen_smoke(server, tmp_path):
    payload = uploads()
    source = demo_sources("balanced")["samples"].data.replace(b"\t", b",")
    payload["files"]["samples"] = {"name": "samples.csv", "data": base64.b64encode(source).decode()}
    assert request(server, "api/audit", payload)[0] == 200
    smoke_test(server, tmp_path / "smoke.json")
    assert len(json.loads((tmp_path / "smoke.json").read_text())["checks"]) == 7


@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "evil.example"},
        {"Origin": "https://evil.example"},
        {"Origin": "null"},
        {"Sec-Fetch-Site": "cross-site"},
    ],
)
def test_foreign_origins_and_hosts_blocked(server, headers):
    assert request(server, headers=headers)[0] == 403
    assert request(server, "api/audit", uploads(), headers=headers)[0] == 403
    assert not server.bundles


def test_capability_traversal_and_resource_headers(server):
    assert server.server_address[0] == "127.0.0.1"
    assert request(server, "/", prefix=False)[0] == 404
    assert request(server, "api/info")[0] == 200
    for path in [
        "../pyproject.toml",
        "%2e%2e/pyproject.toml",
        "reports/unknown/report.html",
        "examples/../../pyproject.toml",
        "examples/balanced/../../cli.py",
    ]:
        assert request(server, path)[0] == 404
    for path in ["", "app.js", "app.css"]:
        code, headers, body = request(server, path)
        assert code == 200 and body
        assert headers["Cache-Control"] == "no-store"
        assert "frame-ancestors 'self'" in headers["Content-Security-Policy"]
        assert headers["Referrer-Policy"] == "no-referrer"
    code, headers, data = request(server, "examples/balanced/design.yaml")
    assert code == 200 and data == demo_sources("balanced")["design"].data
    assert "attachment" in headers["Content-Disposition"]


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"files": {}},
        {"files": {"samples": []}},
        {"files": {"samples": {}, "design": {}, "unknown": {}}},
    ],
)
def test_malformed_upload_shapes(payload):
    with pytest.raises(InputError):
        decode_uploads(payload)


@pytest.mark.parametrize(
    "name,data",
    [
        ("../samples.csv", "YQ=="),
        ("C:\\samples.csv", "YQ=="),
        ("samples.exe", "YQ=="),
        ("samples.csv", "!!!"),
        ("samples.csv", ""),
        ("samples.csv", 5),
    ],
)
def test_bad_file_names_and_encoding(server, name, data):
    payload = uploads()
    payload["files"]["samples"] = {"name": name, "data": data}
    assert request(server, "api/audit", payload)[0] == 400
    assert not server.bundles and not list(server.out.iterdir())


def test_upload_limit_busy_and_errors_recover(server, monkeypatch):
    import batchlens.web as web

    monkeypatch.setattr(web, "MAX_UPLOAD_BYTES", 4)
    assert request(server, "api/audit", uploads())[0] == 400
    monkeypatch.setattr(web, "MAX_UPLOAD_BYTES", 32 * 1024 * 1024)
    with server.busy:
        assert request(server, "api/audit", uploads())[0] == 409
        assert request(server, "api/quit", {})[0] == 409
    assert request(server, "api/audit", uploads(), headers={"Content-Type": "text/plain"})[0] == 415
    assert request(server, "api/demo/invalid", {})[0] == 400
    payload = uploads()
    payload["files"]["design"]["data"] = base64.b64encode(b"not: a valid design").decode()
    assert request(server, "api/audit", payload)[0] == 400
    code, _, body = request(server, "api/demo/confounded-time", {})
    assert code == 200 and json.loads(body)["contrasts"][0]["status"] == "NON_ESTIMABLE"


def test_request_size_and_output_error(server, monkeypatch):
    import batchlens.web as web

    monkeypatch.setattr(web, "MAX_REQUEST_BYTES", 1)
    assert request(server, "api/audit", uploads())[0] == 413
    monkeypatch.setattr(web, "MAX_REQUEST_BYTES", 45 * 1024 * 1024)

    def fail(*args, **kwargs):
        raise OSError("private path must not be sent to browser")

    monkeypatch.setattr(web, "run_audit", fail)
    code, _, body = request(server, "api/audit", uploads())
    assert code == 500 and b"private path" not in body and not server.bundles


def test_html_in_uploaded_labels_is_escaped(server):
    payload = uploads()
    design = json.loads(demo_sources("balanced")["design"].data)
    design["contrasts"][0]["id"] = '<script>alert("x")</script>'
    payload["files"]["design"]["data"] = base64.b64encode(json.dumps(design).encode()).decode()
    code, _, body = request(server, "api/audit", payload)
    assert code == 200
    code, _, report = request(server, f"reports/{json.loads(body)['id']}/report.html")
    assert code == 200 and b"<script>" not in report and b"&lt;script&gt;" in report


def test_serve_options_and_browser_failure(tmp_path, monkeypatch, capsys):
    import batchlens.web as web

    opened = []
    monkeypatch.setattr(web.webbrowser, "open", lambda url: opened.append(url) or False)
    monkeypatch.setattr(web.AuditServer, "serve_forever", lambda *args, **kwargs: None)
    assert main(["serve", "--out", str(tmp_path / "out")]) == 0
    assert opened[0].startswith("http://localhost:")
    assert "Open the URL above manually" in capsys.readouterr().out
    assert main(["serve", "--no-browser", "--out", str(tmp_path / "out")]) == 0
    assert len(opened) == 1
    assert main(["serve", "--port", "65536"]) == 2


def test_stop_server_retains_reports(server):
    _, _, body = request(server, "api/demo/balanced", {})
    folder = Path(json.loads(body)["saved_to"])
    assert request(server, "api/quit", {})[0] == 200
    assert (folder / "COMPLETE").is_file()
