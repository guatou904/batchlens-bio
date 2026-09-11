"""Publish a self-contained audit bundle without replacing existing output."""

import csv
import hashlib
import json
import os
import platform
import tempfile
from datetime import UTC, datetime
from importlib import metadata, resources
from pathlib import Path
from typing import Any

from jinja2 import Environment, select_autoescape

from batchlens.config import InputError


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def write_bundle(
    result: dict[str, Any],
    provenance: dict[str, Any],
    out: Path,
    dataset: dict[str, Any] | None = None,
) -> None:
    # Requiring a new directory also avoids replacing an empty directory raced by another writer.
    if out.exists() or out.is_symlink():
        raise InputError("Output already exists; choose a new directory. Nothing was overwritten.")
    if not out.parent.is_dir():
        raise InputError("Output parent directory must already exist")
    stage = Path(tempfile.mkdtemp(prefix=f".{out.name}-", dir=out.parent))
    try:
        (stage / "result.json").write_text(json_text(result), encoding="utf-8")
        template = resources.files("batchlens").joinpath("resources/report.html.j2").read_text()
        environment = Environment(autoescape=select_autoescape(default=True))
        html = environment.from_string(template).render(result=result, dataset=dataset)
        (stage / "report.html").write_text(html, encoding="utf-8")
        tables = stage / "tables"
        tables.mkdir()
        for name in ["coverage", "target_counts", "observation_coverage", "units"]:
            rows = result[name]
            if rows:
                with (tables / f"{name}.tsv").open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t")
                    writer.writeheader()
                    for row in rows:
                        # Prevent spreadsheet formula interpretation on exported user labels.
                        values = {
                            k: json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v
                            for k, v in row.items()
                        }
                        writer.writerow(
                            {
                                k: "'" + v
                                if isinstance(v, str)
                                and v.startswith(("=", "+", "-", "@", "\t", "\r"))
                                else v
                                for k, v in values.items()
                            }
                        )
        manifest = {
            "created_at": datetime.now(UTC).isoformat(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "inputs": provenance,
            "dataset": dataset,
            "versions": {
                name: metadata.version(name)
                for name in ["batchlens-bio", "numpy", "pandas", "pydantic", "PyYAML", "Jinja2"]
            },
            "outputs": {
                p.relative_to(stage).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(stage.rglob("*"))
                if p.is_file()
            },
        }
        (stage / "manifest.json").write_text(json_text(manifest), encoding="utf-8")
        # Reserve the final name exclusively; publish only after all files are materialized.
        # A concurrent writer cannot acquire the same directory with mkdir(exist_ok=False).
        out.mkdir()
        for item in stage.iterdir():
            os.rename(item, out / item.name)
        (out / "COMPLETE").write_text("Audit bundle complete. Verify manifest.json for hashes.\n")
        # Keep the now-empty staging directory: no automatic directory deletion.
    except Exception:
        # Incomplete bundles lack COMPLETE and must never be interpreted as successful.
        raise
