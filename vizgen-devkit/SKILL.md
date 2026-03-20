---
name: vizgen-devkit
description: >
  Use this skill when the user is analyzing Vizgen MERFISH spatial transcriptomics
  data, or files such as detected_transcripts.csv, cell_boundaries.parquet,
  cell_metadata.csv, or MERFISH output directories. Use it for cell segmentation,
  data loading, preprocessing, QC, spatial analysis, and secondary analysis
  (cell typing, domain detection).
---

# Vizgen MERFISH Analysis

Use this skill for Vizgen MERFISH platform detection, workflow order, step execution,
and cell segmentation routing.

## Detect this platform when

- the user mentions `Vizgen`, `MERFISH`, or `MERSCOPE`
- files include `detected_transcripts.csv`, `cell_boundaries.parquet`, or `cell_metadata.csv`
- directory structure matches Vizgen/MERFISH output layout

If the platform is still unclear, ask before executing platform-specific steps.

## First questions

- Is the data already segmented, or do you need to run cell segmentation?
- Does the H5AD have one or multiple samples/regions?

## Workflow overview

Read `main.md` for the step plan, then load each step doc before executing it.

1. Cell Segmentation (if needed) — [step details](steps/cell_segmentation.md)
2. Data Loading — [step details](steps/data_loading.md)
3. Preprocessing — [step details](steps/preprocessing.md)
4. Quality Control + Filtering — [step details](steps/qc.md)
5. Spatial Analysis — [step details](steps/spatial_analysis.md)
6. Secondary Analysis (Cell Type Annotation + Domain Detection) — [step details](steps/vizgen_secondary_analysis.md)

## Workflow references

- Domain Detection — [wf/domain_detection_wf.md](wf/domain_detection_wf.md)
- RAPIDS preprocessing — [wf/rapids_wf.md](wf/rapids_wf.md)
- Cell Segmentation — [wf/vizgen_cell_segmentation_wf.md](wf/vizgen_cell_segmentation_wf.md)

## Latch-specific execution

If `latch-workflows`, `latch-plots-ui`, or `latch-data-access` are available, prefer them for:

- workflow launching
- Latch widget usage
- plot rendering and AnnData viewers
- Latch Data path handling

If those sibling skills are not available, use the local `wf/`, `steps/`, and `README.md` docs directly.
