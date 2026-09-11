"""Install wheel and sdist into separate new environments, outside the source tree."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import venv
from pathlib import Path


def run(command, cwd, expected=0):
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    process = subprocess.run(command, cwd=cwd, env=environment, text=True, capture_output=True)
    if process.returncode != expected:
        raise RuntimeError(
            f"{command[0]} failed ({process.returncode}):\n{process.stdout}\n{process.stderr}"
        )
    return process.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    artifacts = sorted(args.dist.resolve().glob("*.whl")) + sorted(
        args.dist.resolve().glob("*.tar.gz")
    )
    if len(artifacts) != 2:
        raise ValueError("Expected exactly one wheel and one sdist")
    args.out.mkdir(parents=False, exist_ok=False)
    results = []
    for number, artifact in enumerate(artifacts):
        work = args.out.resolve() / f"install-{number}"
        work.mkdir()
        env = work / "env"
        venv.EnvBuilder(with_pip=True).create(env)
        bin_dir = env / ("Scripts" if os.name == "nt" else "bin")
        python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        cli = bin_dir / ("batchlens.exe" if os.name == "nt" else "batchlens")
        run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", str(artifact)],
            work,
        )
        version = run([str(cli), "--version"], work).strip()
        assert version == "batchlens 0.1.0"
        location = run([str(python), "-c", "import batchlens;print(batchlens.__file__)"], work)
        assert str(env) in location
        run([str(cli), "--help"], work)
        resource_root = run(
            [
                str(python),
                "-c",
                "from importlib.resources import files; "
                "print(files('batchlens').joinpath('resources/demo/balanced'))",
            ],
            work,
        ).strip()
        inputs = [
            "--samples",
            str(Path(resource_root) / "samples.tsv"),
            "--design",
            str(Path(resource_root) / "design.yaml"),
        ]
        run([str(cli), "validate", *inputs], work)
        run([str(cli), "audit", *inputs, "--out", "explicit-audit"], work)
        assert (work / "explicit-audit" / "COMPLETE").exists()
        cases = [
            ("balanced", "ESTIMABLE", 0),
            ("confounded-time", "NON_ESTIMABLE", 3),
            ("partial-overlap", "ESTIMABLE", 0),
            ("redundant-nuisance", "ESTIMABLE", 0),
            ("paired", "ESTIMABLE", 0),
            ("spatial-replicates", "NOT_ASSESSED", 0),
            ("mixed-assays", "NOT_ASSESSED", 0),
        ]
        for name, status, code in cases:
            run([str(cli), "demo", "--case", name, "--out", name], work, code)
            report = json.loads((work / name / "result.json").read_text())
            assert report["contrasts"][0]["status"] == status
            assert (work / name / "COMPLETE").exists()
        run([str(python), "-m", "pip", "check"], work)
        results.append(
            {
                "artifact": artifact.name,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "python": sys.version.split()[0],
                "version": version,
                "demo_cases": len(cases),
                "explicit_validate_audit": "passed",
                "status": "passed",
            }
        )
    (args.out / "smoke-results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
