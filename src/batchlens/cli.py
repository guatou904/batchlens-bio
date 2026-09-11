"""Command-line interface. Exit 3 means findings, not execution failure."""

import argparse
import hashlib
import json
import sys
from importlib import resources
from pathlib import Path

from batchlens import __version__
from batchlens.audit import audit, policy_exit
from batchlens.config import InputError, read_spec
from batchlens.metadata import load_inputs
from batchlens.reporting import write_bundle

CASES = [
    "balanced",
    "confounded-time",
    "partial-overlap",
    "redundant-nuisance",
    "paired",
    "spatial-replicates",
    "mixed-assays",
]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="batchlens",
        description="Audit experimental units and declared batch-confounded contrasts.",
        epilog="Exit codes: 0 completed; 1 internal failure; 2 input/output error; "
        "3 findings threshold. "
        "No expression correction. See docs/input-schema.md and docs/interpretation.md.",
    )
    result.add_argument("--version", action="version", version=f"batchlens {__version__}")
    sub = result.add_subparsers(dest="command", required=True)
    for name in ["validate", "audit", "demo"]:
        command = sub.add_parser(name)
        if name == "demo":
            command.add_argument("--case", choices=CASES, default="confounded-time")
        else:
            command.add_argument(
                "--samples", required=True, type=Path, help="CSV/TSV; unique sample ID"
            )
            command.add_argument(
                "--design", required=True, type=Path, help="Strict YAML model contract"
            )
            command.add_argument("--observations", type=Path, help="Optional cells/spots metadata")
            command.add_argument("--assays", type=Path, help="Optional sample-to-assay links")
        if name != "validate":
            command.add_argument(
                "--out", required=True, type=Path, help="New directory; parent must exist"
            )
            command.add_argument(
                "--fail-on", choices=["critical", "warning", "none"], default="critical"
            )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        dataset = None
        if args.command == "demo":
            folder = Path(str(resources.files("batchlens").joinpath("resources/demo", args.case)))
            args.samples, args.design = folder / "samples.tsv", folder / "design.yaml"
            args.observations = (
                folder / "observations.tsv" if (folder / "observations.tsv").is_file() else None
            )
            args.assays = folder / "assays.tsv" if (folder / "assays.tsv").is_file() else None
            dataset = {"kind": "SYNTHETIC", "title": args.case}
        spec = read_spec(args.design)
        inputs = load_inputs(args.samples, spec, args.observations, args.assays)
        if args.command == "validate":
            print("Metadata valid. Model support and contrast estimability have not been assessed.")
            return 0
        result = audit(inputs, spec)
        inputs.provenance["design"] = {
            "sha256": hashlib.sha256(args.design.read_bytes()).hexdigest(),
            "canonical_sha256": hashlib.sha256(
                json.dumps(spec.model_dump(), sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest(),
        }
        write_bundle(result, inputs.provenance, args.out, dataset)
        print(
            f"BatchLens audit completed: {result['counts']['experimental_units']} "
            "experimental units; "
            f"{result['counts']['samples']} samples"
        )
        for comparison in result["contrasts"]:
            print(f"{comparison['id']}: {comparison['status']}")
        print(f"Report: {args.out / 'report.html'}")
        print(f"JSON: {args.out / 'result.json'}")
        return policy_exit(result, args.fail_on)
    except (InputError, OSError) as exc:
        print(f"Input/output error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            f"Internal error ({type(exc).__name__}). No successful audit is claimed. "
            "Please report a minimal, de-identified reproducer.",
            file=sys.stderr,
        )
        return 1
