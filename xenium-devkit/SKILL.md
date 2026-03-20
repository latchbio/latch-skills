---
name: xenium-devkit
description: >
  Use this skill when the user is analyzing 10x Genomics Xenium in situ data,
  or files such as transcripts.csv, transcripts.parquet, cells.csv,
  cell_feature_matrix.h5, or Xenium output directories. Use it for data
  preparation, preprocessing, differential expression, cell type annotation,
  spatial analysis, domain detection, and cell segmentation.
---

# 10x Xenium Analysis

Use this skill for Xenium platform detection, workflow order, step execution,
and helper-library usage.

## Detect this platform when

- the user mentions `Xenium` or `10x Xenium`
- files include `transcripts.csv`, `transcripts.parquet`, `cells.csv`, or `cell_feature_matrix.h5`
- paths or metadata contain `Xenium`
- directory contains `analysis.tar.gz` from Xenium preprocessing

If the platform is still unclear, ask before executing platform-specific steps.

## First questions

- Is an `.h5ad` already present in the attached data?
- Are there multiple samples/batches that need to be integrated?
- Does the attached folder contain raw Xenium outputs that require preprocessing?
- Does the attached folder contain preprocessing output `analysis.tar.gz`?

## Latch setup

If the environment supports `redeem_package`, install the Xenium package before analysis:

- `package_code`: `7a4f4bd980b3739a825072a975dd9a376c267ff7c84c1c9c59c8da196e58c3bd`
- `package_version_id`: `401`

If `redeem_package` is unavailable, continue with the repo-local docs and the current environment.

## Workflow overview

Read `main.md` for the step plan, then load each step doc before executing it.

0. Data Preparation — Convert raw Xenium outputs to `.h5ad` and viewer-ready assets — [step details](steps/data_preparation.md)
1. Data Loading — Load `.h5ad`, attach spatial tiles, and render with `w_h5` — [step details](steps/data_loading.md)
2. Preprocessing — QC, normalization, PCA, Harmony (if needed), UMAP and Leiden (**only if user confirms**) — [step details](steps/preprocessing.md)
3. Differential Gene Expression — Identify marker genes per cluster, dot plots — [step details](steps/differential_expression.md)
4. Cell Type Annotation — CellGuide markers and vocab configs — [step details](steps/cell_type_annotation/cell_type_annotation.md)
5. Neighbors Enrichment Analysis — Spatial neighbor graph and enrichment — [step details](steps/spatial_analysis.md)
6. Domain Detection (optional) — Tissue domain detection via workflow — [wf/domain_detection_wf.md](wf/domain_detection_wf.md)
7. Cell Segmentation (optional) — Resegment cells using full-resolution TIFF — [step details](steps/cell_segmentation.md)

## Important branches

- If embeddings or clusters already exist in adata, do not run preprocessing. Ask for confirmation before recomputing.
- Steps 6 and 7 are optional.

## Helper library usage

If a step requires Xenium helper code, import from the skill's `lib/` directory:

```python
import sys
sys.path.insert(0, "<skill-root>/lib")

from xenium_cell_type import ...
```

Resolve `<skill-root>` to the directory where this skill is checked out in the current environment.

## General rules

- Render figures using `w_plot`. Do NOT reuse the variable name `fig` — use descriptive names like `fig_qc`, `fig_umap`.
- For non-Scanpy figures, use Plotly.
- Never overwrite data without user consent; create new keys/versions.

## Latch-specific execution

If `latch-workflows`, `latch-plots-ui`, or `latch-data-access` are available, prefer them for:

- workflow launching
- Latch widget usage
- plot rendering and AnnData viewers
- Latch Data path handling

If those sibling skills are not available, use the local `wf/`, `steps/`, and `README.md` docs directly.
