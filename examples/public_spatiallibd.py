"""Opt-in public metadata example; no expression or tissue images downloaded."""

import argparse
import csv
import hashlib
import io
import json
import urllib.request
from pathlib import Path

from batchlens.audit import audit
from batchlens.config import StudySpec
from batchlens.metadata import load_inputs
from batchlens.reporting import write_bundle

SOURCE = (
    "https://raw.githubusercontent.com/LieberInstitute/HumanPilot/"
    "044446d6bd8fc154aa74f7be62ec67effb1ec376/"
    "Analysis/visium_dlpfc_pilot_sample_metrics.tsv"
)
SHA256 = "950dd0c64da4faeeee1d0899be3b1ab3e73ce6202423db48c9194327991edffa"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New work directory")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Output already exists; choose a new directory")
    with urllib.request.urlopen(SOURCE, timeout=30) as response:
        raw = response.read()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError("Upstream checksum mismatch; no analysis performed")
    source = list(csv.reader(io.StringIO(raw.decode()), delimiter="\t"))
    samples = source[0][1:]
    by_field = {row[0]: row[1:] for row in source[1:]}
    assert len(samples) == 12 and len(set(by_field["Brain.Number"])) == 3
    args.out.mkdir()
    (args.out / "source.tsv").write_bytes(raw)
    with (args.out / "samples.tsv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(["sample_id", "unit_id", "position", "technical_replicate"])
        writer.writerows(
            zip(
                samples,
                by_field["Brain.Number"],
                by_field["Position"],
                by_field["Replicate"],
                strict=True,
            )
        )
    config = {
        "schema_version": "1.0",
        "design_mode": "independent",
        "sample_id": "sample_id",
        "unit_id": "unit_id",
        "target": "position",
        "adjust_for": ["technical_replicate"],
        "variables": {
            "position": {
                "role": "target",
                "type": "categorical",
                "levels": ["0 µm", "300 µm"],
                "reference": "0 µm",
            },
            "technical_replicate": {
                "role": "batch",
                "type": "categorical",
                "levels": ["1", "2"],
                "reference": "1",
            },
        },
        "contrasts": [{"id": "position_300_vs_0", "numerator": "300 µm", "denominator": "0 µm"}],
    }
    spec = StudySpec.model_validate(config)
    (args.out / "design.yaml").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    inputs = load_inputs(args.out / "samples.tsv", spec)
    result = audit(inputs, spec)
    assert result["counts"]["experimental_units"] == 3
    assert result["counts"]["samples"] == 12
    assert result["contrasts"][0]["status"] == "NOT_ASSESSED"
    inputs.provenance["upstream"] = {"url": SOURCE, "sha256": SHA256}
    write_bundle(
        result,
        inputs.provenance,
        args.out / "audit",
        {
            "kind": "PUBLIC METADATA / DESCRIPTIVE EXAMPLE",
            "title": "HumanPilot / spatialLIBD: repeated sections from three subjects",
            "limitation": "Technical replicate is an illustrative technical factor, not a known "
            "sequencing run. No batch-effect or position-effect conclusion is made.",
        },
    )
    print("Verified public metadata: 3 subjects, 12 samples; NOT_ASSESSED (repeated sampling).")
    print(args.out / "audit/report.html")


if __name__ == "__main__":
    main()
