---
name: takara-devkit
description: >
  Use this skill when the user is analyzing Takara Seeker or Trekker spatial
  transcriptomics data, ICELL8 or PLL-Seq data, or files and metadata that mention
  Takara, Seeker, Trekker, or paired Trekker FASTQs. Also use it for Takara-derived
  H5AD objects that need QC, background removal, normalization, clustering,
  differential expression, or cell typing.
---

# Takara Seeker / Trekker

Use this skill for Takara platform detection, workflow order, step execution, and
helper-library usage.

## Detect this platform when

- the user mentions `Takara`, `Seeker`, or `Trekker`
- paths or filenames contain `Seeker` or `Trekker`
- metadata identifies Seeker 3x3, Seeker 10x10, or Trekker
- the user has paired FASTQs for a Trekker run
- the user has a Takara-derived H5AD for downstream analysis

If the platform is still unclear, ask before executing platform-specific steps.

## First questions

- What tissue and disease conditions describe the data?
- Is the kit type Seeker 3x3, Seeker 10x10, or Trekker?
- Does the H5AD contain one sample or multiple samples?

## Latch setup

If the environment supports `redeem_package`, install the Takara package before analysis:

- `package_code`: `3015c6c63ecc3f2cd410ea340a36af05777`
- `package_version_id`: `192`

If `redeem_package` is unavailable, continue with the repo-local docs and the current environment.

## Workflow overview

Read `main.md` for the step plan, then load each step doc before executing it.

1. Reads to Counts (FastQ only) — [workflow reference](wf/trekker_pipeline_wf.md) and [step details](steps/reads_to_counts.md)
2. Data Loading — [step details](steps/data_loading.md)
3. Background Removal (Seeker only) — [step details](steps/background_removal.md)
4. Quality Control and Filtering — [step details](steps/qc.md)
5. Normalization — [step details](steps/normalization.md)
6. Feature Selection — [step details](steps/feature_selection.md)
7. Dimensionality Reduction — [step details](steps/dimensionality_reduction.md)
8. Clustering — [step details](steps/clustering.md)
9. Differential Gene Expression — [step details](steps/diff_gene_expression.md)
10. Cell Type Annotation — [step details](steps/cell_typing.md)

## Important branches

- Run Reads to Counts only when the user starts from FASTQs.
- Run Background Removal only for Seeker datasets.
- If the user already has a processed H5AD, start at the first downstream step that still applies.

## Helper library usage

If a step requires Takara helper code, import from the skill's `lib/` directory:

```python
import sys
sys.path.insert(0, "<skill-root>/lib")

from takara.background_removal import KitType, remove_background
```

Resolve `<skill-root>` to the directory where this skill is checked out in the current environment.

## Latch-specific execution

If `latch-workflows`, `latch-plots-ui`, or `latch-data-access` are available, prefer them for:

- workflow launching
- Latch widget usage
- plot rendering and AnnData viewers
- Latch Data path handling

If those sibling skills are not available, use the local `wf/`, `steps/`, and `README.md` docs directly.
