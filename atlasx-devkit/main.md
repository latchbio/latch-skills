<pre_analysis_questions>
- What organism is your data from (Human - hg38, Mouse - mm10, Rat - rnor6)?
- What tissue and experimental conditions describe your data?
- Do you have raw fragment files and spatial directories, or pre-processed H5AD?
</pre_analysis_questions>

<pre_analysis_step>

MANDATORY: Invoke the `redeem_package` tool to install required AtlasXomics tools into the workspace.
  - `package_code`: `2428814b149447a4c354b3cb4520095b77955bf99cb3eedfef20b920a2a7d3d7`
  - `package_version_id`: `405`

</pre_analysis_step>

<plan>
1. Quality Control + Filtering -> `steps/qc.md`
2. Clustering -> `steps/clustering.md`
3. Differential Analysis -> `steps/de.md`
4. Cell Type Annotation -> `steps/cell_type_annotation/overview.md`
</plan>

<self_eval_criteria>
</self_eval_criteria>

<data_structure>

### Data Paths

Workspaces are organized **by Workflow output** — one top-level directory per
Workflow, with a subdirectory per run or project.

- Fragments (from FASTQ): `/fastq2frags/[Run_ID]/chromap_output/fragments.tsv.gz`
- Fragments (from CRAM): `/cram2frags/[project_name]/fragments.sort.bed.gz`
- Spatial: `/spatials/[Run_ID]/spatial`
- Downstream-analysis ready (SnapATAC2): `/atac_analysis_snap/[project_name]/`
- Downstream-analysis ready (ArchR): `/atac_analysis_archr/[project_name]/`
- Optimization sweeps: `/atac_optimize_snap/[project_name]/`, `/atac_optimize_archr/[project_name]/`
- Comparisons: `/compare_outs/[project_name]/`

Raw FASTQs are not delivered by default; the **filtered** FASTQs from
preprocessing are under `/fastq2frags/[Run_ID]/filtered_fastqs/`.

### Output Layout

```
atac_analysis_snap/[project_name]/
├── anndata/            # all .h5ad objects
├── seurat_objects/     # all .rds objects
├── tables/             # analysis tables, medians, params, embeddings
├── figures/
└── Launch_Plots/artifact.json

atac_analysis_archr/[project_name]/
├── [project_name]_ArchRProject/          # ArchR project (R-based analysis)
├── anndata/, seurat_objects/
├── {cluster,sample,condition}_coverages/ # BigWig tracks
├── {cluster,sample,condition}_peak_beds/
├── tables/, figures/
└── Launch_Plots/artifact.json
```

**Key Analysis Files** (under `anndata/`)

- `combined_ge.h5ad`: **Full gene activity scores** across all spots/cells and samples. **Use this for analysis.**
  - .X matrix: gene activity (imputed from chromatin accessibility)
  - Used for: differential analysis, marker detection, cell type annotation
- `combined_motifs.h5ad`: **Full motif enrichment scores**
  - .X matrix: TF motif enrichment scores (870 motifs)
  - Used for: transcription factor activity analysis
- `combined_sm_ge.h5ad`, `combined_sm_motifs.h5ad`: **Reduced (`_sm`) — visualization only.**
  `.X` is cast to `float16` with raw counts/layers stripped for fast loading in
  Plots. Do **not** compute on these; use the full objects above.
- `*_ArchRProject/`: ArchR project directory for R-based analysis

Additional outputs:
- `combined.h5ad`: Original peak/tile matrix
- `[sample]_g_converted.h5ad`: Per-sample gene activity
- `[sample]_m_converted.h5ad`: Per-sample motif enrichment
- `compare_config.json`: Example grouping file for comparisons
- `cluster_coverages/`, `condition_coverages/`, `sample_coverages/`: BigWig coverage tracks
- `figures/`: QC and analysis plots
- `tables/`: Summary statistics

<details>
<summary>Legacy paths (older workspaces, pre-restructure)</summary>

| Legacy | Current |
|---|---|
| `/chromap_outs/[Run_ID]/chromap_output/` | `/fastq2frags/[Run_ID]/chromap_output/` |
| `/Images_spatial/[Run_ID]/spatial` | `/spatials/[Run_ID]/spatial` |
| `/snap_outs/[project_name]/` | `/atac_analysis_snap/[project_name]/` |
| `/snap_opts/[project_name]/` | `/atac_optimize_snap/[project_name]/` |
| `/ArchRProjects/[project_name]/` | `/atac_analysis_archr/[project_name]/` |
| `/optimize_outs/[project_name]/` | `/atac_optimize_archr/[project_name]/` |

Collaborator workspaces previously grouped by stage:
- Fragments: `.../Raw_Data/[Run_ID]/chromap_output/fragments.tsv.gz`
- Spatial: `.../Raw_Data/[Run_ID]/spatial`
- Downstream-analysis ready: `.../Processed_Data/[project_name]`

In legacy outputs the `.h5ad` and `.rds` objects sit at the top of the project
directory rather than under `anndata/` and `seurat_objects/`.

</details>

</data_structure>
