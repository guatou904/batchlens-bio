# Public spatial metadata example

This optional example downloads one 3,355-byte sample-metrics table, not expression data or tissue images. It is not part of installation or the offline synthetic demos.

Source: [LieberInstitute/HumanPilot, pinned sample metrics](https://github.com/LieberInstitute/HumanPilot/blob/044446d6bd8fc154aa74f7be62ec67effb1ec376/Analysis/visium_dlpfc_pilot_sample_metrics.tsv), supporting [spatialLIBD](https://github.com/LieberInstitute/spatialLIBD). Study: Maynard et al., *Transcriptome-scale spatial gene expression in the human dorsolateral prefrontal cortex*, Nature Neuroscience (2021), [DOI](https://doi.org/10.1038/s41593-020-00787-0).

Commit: `044446d6bd8fc154aa74f7be62ec67effb1ec376`. Raw SHA256: `950dd0c64da4faeeee1d0899be3b1ab3e73ce6202423db48c9194327991edffa`. Checked 2026-09-11. The repository includes an [Artistic-2.0 license](https://github.com/LieberInstitute/HumanPilot/blob/044446d6bd8fc154aa74f7be62ec67effb1ec376/LICENSE); downloaded data retain their original provenance/terms. BatchLens does not relicense or bundle this table as MIT synthetic data. No copied data file is committed here.

```sh
python examples/public_spatiallibd.py --out public-spatiallibd
```

Requires BatchLens installed. Run from the repository root or use an absolute script path. Choose a new output directory. The script verifies the upstream hash before using data and retains the source locally.

Mapping: column headers → sample IDs; `Brain.Number` → declared experimental unit; `Position` → position label; `Replicate` → technical-replicate index. All 12 samples are retained. No labels are invented; sex/age/outcome are not used in the audit.

**Limitation:** `Replicate` is an explicitly declared illustrative technical factor, not a verified sequencing run, processing date, or slide batch. The original table does not establish those technical batches. This is a hierarchy/unsupported-design check, not a claim of confounding in the original study or a biological position effect.

Expected: **3 subjects, 12 samples, NOT_ASSESSED** because four samples per unit exceed the independent contract. No spot rows are linked, so the observation count is zero, not the study's total spot count. The report demonstrates that twelve sections are not twelve independent people.

The script asserts those counts and status. Network access is opt-in; default CI uses synthetic fixtures. Public metadata are not a statistical ground truth for batch effects.
