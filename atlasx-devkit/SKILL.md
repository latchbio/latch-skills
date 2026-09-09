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

Secondary-analysis objects live under `anndata/` in the output directory.

- `combined_ge.h5ad`: **Full** gene activity scores for all spots/cells. `.X` contains gene activity imputed from chromatin accessibility. **Use this for analysis** — DE, marker detection, cell typing, re-clustering.
- `combined_motifs.h5ad`: **Full** motif enrichment scores (870 motifs). `.X` contains TF motif enrichment.
- `combined_sm_ge.h5ad` / `combined_sm_motifs.h5ad`: **Reduced (`_sm`) — visualization only.** These are built for fast loading in Plots: `.X` is cast to `float16` and raw counts/layers are stripped. Do **not** compute on them (differential analysis, marker detection, re-clustering); precision loss makes results unreliable. Load them for viewers/plots, then use the full objects above for any computation.

### Data paths

Workspaces are organized **by Workflow output** — one top-level directory per
Workflow, with a subdirectory per run or project:

- Fragments (from FASTQ): `/fastq2frags/[Run_ID]/chromap_output/fragments.tsv.gz`
- Fragments (from CRAM): `/cram2frags/[project_name]/fragments.sort.bed.gz`
- Spatial: `/spatials/[Run_ID]/spatial`
- Downstream-ready (SnapATAC2): `/epi_analysis_snap/[project_name]/`
- Downstream-ready (ArchR): `/epi_analysis_archr/[project_name]/`
- Optimization sweeps: `/epi_optimize_snap/[project_name]/`, `/epi_optimize_archr/[project_name]/`
- Comparisons: `/compare_outs/[project_name]/`

Raw FASTQs are not delivered by default; the **filtered** FASTQs from
preprocessing are under `/fastq2frags/[Run_ID]/filtered_fastqs/`.

<details>
<summary>Legacy paths (older workspaces, pre-restructure)</summary>

Older data may still use the previous naming. If the current paths above are
absent, fall back to these:

| Legacy | Current |
|---|---|
| `/chromap_outs/[Run_ID]/chromap_output/` | `/fastq2frags/[Run_ID]/chromap_output/` |
| `/Images_spatial/[Run_ID]/spatial` | `/spatials/[Run_ID]/spatial` |
| `/snap_outs/[project_name]/` | `/epi_analysis_snap/[project_name]/` |
| `/snap_opts/[project_name]/` | `/epi_optimize_snap/[project_name]/` |
| `/ArchRProjects/[project_name]/` | `/epi_analysis_archr/[project_name]/` |
| `/optimize_outs/[project_name]/` | `/epi_optimize_archr/[project_name]/` |
| `/atac_optimize_snap/[project_name]/` | `/epi_optimize_snap/[project_name]/` |
| `/atac_optimize_archr/[project_name]/` | `/epi_optimize_archr/[project_name]/` |

The `atac_optimize_*` names were live only briefly, so few projects use them.
Note there is **no** `atac_analysis_*` to fall back on — the analysis Workflows
went straight from the legacy names to `epi_analysis_*`, so don't go looking for
one.

Collaborator workspaces previously grouped by stage rather than Workflow:
- Fragments: `.../Raw_Data/[Run_ID]/chromap_output/fragments.tsv.gz`
- Spatial: `.../Raw_Data/[Run_ID]/spatial`
- Downstream-ready: `.../Processed_Data/[project_name]`

In legacy outputs the `.h5ad` and `.rds` objects sit at the top of the project
directory rather than under `anndata/` and `seurat_objects/`.

</details>

## Latch-specific execution

If `latch-workflows`, `latch-plots-ui`, or `latch-data-access` are available, prefer them for:

- workflow launching
- Latch widget usage
- plot rendering and AnnData viewers
- Latch Data path handling

If those sibling skills are not available, use the local `wf/`, `steps/`, and `README.md` docs directly.
