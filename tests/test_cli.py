import hashlib
import json
import subprocess
import sys

import pytest
from test_science import audit, case

from batchlens.cli import main
from batchlens.reporting import write_bundle


@pytest.mark.parametrize(
    "case_name,code",
    [
        ("balanced", 0),
        ("confounded-time", 3),
        ("spatial-replicates", 0),
    ],
)
def test_demo_end_to_end(tmp_path, case_name, code):
    out = tmp_path / "audit"
    assert main(["demo", "--case", case_name, "--out", str(out)]) == code
    assert (out / "COMPLETE").is_file()
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset"]["kind"] == "SYNTHETIC"
    for path, digest in manifest["outputs"].items():
        assert hashlib.sha256((out / path).read_bytes()).hexdigest() == digest
    assert str(tmp_path) not in (out / "manifest.json").read_text(encoding="utf-8")
    assert "http://" not in (out / "report.html").read_text(encoding="utf-8")
    before = (out / "result.json").read_bytes()
    assert main(["demo", "--out", str(out)]) == 2
    assert (out / "result.json").read_bytes() == before


def test_strict_unsupported_and_validate(tmp_path, capsys):
    assert (
        main(
            [
                "demo",
                "--case",
                "spatial-replicates",
                "--out",
                str(tmp_path / "out"),
                "--fail-on",
                "warning",
            ]
        )
        == 3
    )
    folder = "src/batchlens/resources/demo/balanced/"
    assert (
        main(["validate", "--samples", folder + "samples.tsv", "--design", folder + "design.yaml"])
        == 0
    )
    assert "have not been assessed" in capsys.readouterr().out


def test_module_and_help():
    proc = subprocess.run(
        [sys.executable, "-m", "batchlens", "--help"], capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Exit codes" in proc.stdout


def test_privacy_and_html_escaping(tmp_path):
    inputs, spec = case("balanced")
    inputs.samples["sample_id"] = [f"SECRET_PATIENT_{i}" for i in range(8)]
    inputs.samples["unit_id"] = [f"SECRET_UNIT_{i}" for i in range(8)]
    inputs.samples["private_note"] = "DO_NOT_EXPORT"
    data = spec.model_dump()
    data["contrasts"][0]["id"] = '<script>alert("attack")</script>'
    spec = type(spec).model_validate(data)
    result = audit(inputs, spec)
    out = tmp_path / "out"
    write_bundle(result, {}, out)
    for path in out.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert "SECRET_PATIENT" not in text
            assert "SECRET_UNIT" not in text
            assert "DO_NOT_EXPORT" not in text
    html = (out / "report.html").read_text(encoding="utf-8")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_deterministic_result(tmp_path):
    result = audit(*case("confounded-time"))
    write_bundle(result, {}, tmp_path / "one")
    write_bundle(result, {}, tmp_path / "two")
    assert (tmp_path / "one/result.json").read_bytes() == (
        tmp_path / "two/result.json"
    ).read_bytes()


def test_incomplete_output_has_no_complete_marker(tmp_path, monkeypatch):
    import batchlens.reporting as report

    result = audit(*case("balanced"))
    original = report.os.rename
    called = 0

    def fail_after_one(source, target):
        nonlocal called
        called += 1
        if called > 1:
            raise OSError("simulated write failure")
        original(source, target)

    monkeypatch.setattr(report.os, "rename", fail_after_one)
    with pytest.raises(OSError):
        write_bundle(result, {}, tmp_path / "out")
    assert not (tmp_path / "out/COMPLETE").exists()
