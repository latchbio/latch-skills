---
name: atrandi-devkit
description: >
  Use this skill when the user is analyzing Atrandi RNA:DNA co-sequencing data,
  or files and metadata that mention Atrandi, uniflow, or the RNA:DNA co-seq
  pipeline. Also use it for Atrandi-derived .h5mu (MuData) objects with
  gene_expression, amplicon, or snp modalities that need cell calling, QC,
  filtering, normalization, clustering, cell typing, or amplicon diagnostics.
---

# Atrandi RNA:DNA Co-Sequencing

Use this skill for Atrandi platform detection, workflow order, step execution, and
helper-library usage.

## Detect this platform when

- the user mentions `Atrandi`, `uniflow`, or `RNA:DNA co-seq` / `co-sequencing`
- paths or filenames point to `.h5mu` (MuData) objects, or to uniflow pipeline
  outputs like `counts/counts.h5mu` or `dev/full_read_RNA.parquet`
- metadata or an object contains `gene_expression`, `amplicon`, or `snp`
  modalities sharing partially overlapping barcodes
- the user references an amplicon panel alongside single-cell RNA data
- the user has per-read STAR-tagged parquet files (GN, UR, UB, CB) for
  saturation recalculation

If the platform is still unclear, ask before executing platform-specific steps.

## First questions

- What tissue type and disease condition describe the samples?
- How many samples, and are they from the same experiment?
- Has the uniflow RNA:DNA co-seq pipeline already been run (i.e., are there
  `.h5mu` files)? If so, which pipeline version?
- What amplicon panel is being used and how many targets does it contain?
- What organism is the data from (human, mouse, other)? Affects gene annotation.
- Is batch integration expected (multiple sequencing runs or library preps)?
- What is the expected number of cells per sample (guides cell-calling thresholds)?

## Workflow overview

Read `main.md` for the full plan and the `<data_structure>` / `<self_eval_criteria>`
fields, then load each step doc before executing it.

1. Sample Aggregation — [step details](steps/sample_aggregation.md)
2. Cell Calling — [step details](steps/cell_calling.md)
3. Saturation Analysis — [step details](steps/saturation_analysis.md)
4. Barcode QC — [step details](steps/barcode_qc.md)
5. Doublets and Ambient RNA — [step details](steps/doublets_and_ambient.md)
6. Amplicon QC — [step details](steps/amplicon_qc.md)
7. Filtering — [step details](steps/filtering.md)
8. Normalization — [step details](steps/normalization.md)
9. Dimensionality Reduction — [step details](steps/dimensionality_reduction.md)
10. Clustering — [step details](steps/clustering.md)
11. Cell Type Annotation — [step details](steps/cell_typing.md)
12. Amplicon Diagnostics — [step details](steps/amplicon_diagnostics.md)

## Important branches

- The uniflow pipeline ([workflow doc](wf/uniflow_pipeline.md)) runs **upstream**
  and is **not invoked** by this devkit. Its `.h5mu` outputs are fetched from S3
  in the Sample Aggregation step. Start there if the user already has pipeline
  outputs.
- The `snp` modality may be **absent** in early pipeline versions. Treat it as
  optional.
- The `amplicon` modality may not be present. Run Amplicon QC and Amplicon
  Diagnostics only when it is.
- Modalities can have different barcode sets with only partial overlap.
  Cross-modality operations (e.g., amplicon reads vs RNA UMIs) require explicitly
  filling missing `obs_names` with 0.
- Cell Type Annotation uses SCimilarity when available; otherwise fall back to
  marker-gene annotation.
- Steps depending on optional modalities or tools should degrade gracefully
  (skip with a note, not fail).

## Helper library usage

Atrandi step code imports from the skill's `lib/` package. Insert the skill root
on `sys.path` first (this is the `<pre_analysis_step>` in `main.md`):

```python
import sys
sys.path.insert(0, "<skill-root>")

from lib.common_const import Modality, LibraryType
from lib.barcode.filtering import knee_point, knee_cells_from_umis
```

Key modules:

- `common_const.py` — shared enums/constants (barcode positions, modality names, library types)
- `library_qc.py` — saturation curve computation/plotting against 10x references
- `dataframe_toolkit.py` — Polars/AnnData conversion utilities
- `barcode/` — Hamming-distance barcode correction and knee-point cell calling
- `bam_tools/` — parallel BAM-to-Parquet extraction (STAR tags)
- `modality/dna/` — SNP pileup and variant filtering via pysam
- `metrics/` — YAML-based metrics collection and aggregation
- `plotting/` — upset plots, amplicon alignment plots, barcode QC plots

Resolve `<skill-root>` to the directory where this skill is checked out. On a
Latch pod that is:
`/opt/latch/plots-faas/runtime/mount/agent_config/context/technology_docs/atrandi`

## Latch-specific execution

If `latch-workflows`, `latch-plots-ui`, or `latch-data-access` are available,
prefer them for:

- workflow launching
- Latch widget usage
- plot rendering and AnnData / MuData viewers
- Latch Data path handling

If those sibling skills are not available, use the local `wf/`, `steps/`, and
`README.md` docs directly.

