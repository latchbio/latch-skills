---
name: atlasx-devkit
description: >
  Use this skill when the user is analyzing AtlasXomics spatial epigenomics data,
  including spatial ATAC-seq, gene activity matrices, motif enrichment, fragment
  files, or data mentioning AtlasXomics, DBiT-seq, or spatial chromatin
  accessibility. Use it for QC, clustering, differential analysis, and cell type
  annotation of spatial ATAC data.
---

# AtlasXomics Analysis

Use this skill for AtlasXomics platform detection, workflow order, step execution,
and spatial ATAC-seq analysis.

## Detect this platform when

- the user mentions `AtlasXomics`, `DBiT-seq`, or spatial ATAC
- files include `gene_activity`, `motif`, or `.fragments` files
- data contains `combined_sm_ge.h5ad`, `combined_sm_motifs.h5ad`, or ArchR project directories
- ATAC-seq related spatial data files are present

If the platform is still unclear, ask before executing platform-specific steps.

## First questions

- What organism is your data from (Human - hg38, Mouse - mm10, Rat - rnor6)?
- What tissue and experimental conditions describe your data?
- Do you have raw fragment files and spatial directories, or pre-processed H5AD?

## Latch setup

If the environment supports `redeem_package`, install the AtlasXomics package before analysis:

- `package_code`: `2428814b149447a4c354b3cb4520095b77955bf99cb3eedfef20b920a2a7d3d7`
- `package_version_id`: `405`

If `redeem_package` is unavailable, continue with the repo-local docs and the current environment.

## Workflow overview

Read `main.md` for the step plan, then load each step doc before executing it.

1. Quality Control + Filtering — [step details](steps/qc.md)
2. Clustering — [step details](steps/clustering.md)
3. Differential Analysis — [step details](steps/de.md)
4. Cell Type Annotation — [overview](steps/cell_type_annotation/overview.md)

## Workflow references

- Compare Workflow — [wf/compare_workflow.md](wf/compare_workflow.md)
- Opt Workflow — [wf/opt_workflow.md](wf/opt_workflow.md)

## Data structure

### Key analysis files

- `combined_sm_ge.h5ad`: Gene activity scores for all spots/cells. **Recommended for analyses.** `.X` matrix contains gene activity imputed from chromatin accessibility.
- `combined_sm_motifs.h5ad`: Motif enrichment scores (870 motifs). `.X` matrix contains TF motif enrichment.

### Raw data paths

**Internal Workspace (13502)**:
- Fragments: `/chromap_outs/[Run_ID]/chromap_output/fragments.tsv.gz`
- Spatial: `/Images_spatial/[Run_ID]/spatial`
- Downstream-ready: `/snap_outs/[project_name]/`

**Collaborator Workspaces**:
- Fragments: `.../Raw_Data/[Run_ID]/chromap_output/fragments.tsv.gz`
- Spatial: `.../Raw_Data/[Run_ID]/spatial`
- Downstream-ready: `.../Processed_Data/[project_name]`

## Latch-specific execution

If `latch-workflows`, `latch-plots-ui`, or `latch-data-access` are available, prefer them for:

- workflow launching
- Latch widget usage
- plot rendering and AnnData viewers
- Latch Data path handling

If those sibling skills are not available, use the local `wf/`, `steps/`, and `README.md` docs directly.
