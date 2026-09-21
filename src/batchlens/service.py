"""One audit/bundle pipeline shared by command-line, browser and desktop entry points."""

import hashlib
import json
from importlib import resources
from pathlib import Path
from typing import Any

from batchlens.audit import audit
from batchlens.config import InputError, read_spec
from batchlens.metadata import load_inputs
from batchlens.reporting import write_bundle
from batchlens.sources import Source, Upload

CASES = [
    "balanced",
    "confounded-time",
    "partial-overlap",
    "redundant-nuisance",
    "paired",
    "spatial-replicates",
    "mixed-assays",
]


def demo_sources(case: str) -> dict[str, Upload]:
    if case not in CASES:
        raise InputError("Unknown synthetic demo")
    folder = resources.files("batchlens").joinpath("resources/demo", case)
    return {
        name.split(".")[0]: Upload(name, folder.joinpath(name).read_bytes())
        for name in ["samples.tsv", "design.yaml", "observations.tsv", "assays.tsv"]
        if folder.joinpath(name).is_file()
    }


def run_audit(
    samples: Source,
    design: Source,
    out: Path,
    observations: Source | None = None,
    assays: Source | None = None,
    dataset: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    language: str = "en",
) -> dict[str, Any]:
    spec = read_spec(design)
    inputs = load_inputs(samples, spec, observations, assays)
    result = audit(inputs, spec)
    if context is not None:
        result["input_adapter"] = context
        inputs.provenance["cell_table_adapter"] = context
    inputs.provenance["design"] = {
        "sha256": hashlib.sha256(design.read_bytes()).hexdigest(),
        "canonical_sha256": hashlib.sha256(
            json.dumps(spec.model_dump(), sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
    }
    write_bundle(result, inputs.provenance, out, dataset, language=language)
    return result
