"""Command-line interface. Exit 3 means findings, not execution failure."""

import argparse
import sys
from pathlib import Path

from batchlens import __version__
from batchlens.audit import policy_exit
from batchlens.config import InputError, read_spec
from batchlens.metadata import load_inputs
from batchlens.service import CASES, demo_sources, run_audit


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
    serve = sub.add_parser("serve", help="Open the local browser interface")
    serve.add_argument("--port", type=int, default=0, help="Local port; 0 picks a free port")
    serve.add_argument("--no-browser", action="store_true", help="Print URL without opening it")
    serve.add_argument("--out", type=Path, help="Report parent folder; default: ~/BatchLens Audits")
    sub.add_parser("desktop", help="Open the native window (requires the desktop extra)")
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
        if args.command == "serve":
            from batchlens.web import serve

            return serve(port=args.port, out=args.out, open_browser=not args.no_browser)
        if args.command == "desktop":
            from batchlens.desktop import main as desktop_main

            return desktop_main([])
        dataset = None
        if args.command == "demo":
            sources = demo_sources(args.case)
            args.samples, args.design = sources["samples"], sources["design"]
            args.observations, args.assays = sources.get("observations"), sources.get("assays")
            dataset = {"kind": "SYNTHETIC", "title": args.case}
        if args.command == "validate":
            spec = read_spec(args.design)
            load_inputs(args.samples, spec, args.observations, args.assays)
            print("Metadata valid. Model support and contrast estimability have not been assessed.")
            return 0
        result = run_audit(
            args.samples, args.design, args.out, args.observations, args.assays, dataset
        )
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
