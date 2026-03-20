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

### Raw Data Paths
**Internal Workspace (13502)**:
- Fragments: `/chromap_outs/[Run_ID]/chromap_output/fragments.tsv.gz`
- Spatial: `/Images_spatial/[Run_ID]/spatial`
- Downstream-analysis ready: `/snap_outs/[project_name]/`

**Collaborator Workspaces**:
- Fragments: `.../Raw_Data/[Run_ID]/chromap_output/fragments.tsv.gz`
- Spatial: `.../Raw_Data/[Run_ID]/spatial`
- Downstream-analysis ready: `.../Processed_Data/[project_name]`

**Key Analysis Files**
- `combined_sm_ge.h5ad`: **Gene activity scores** for all spots/cells across all samples. **Recommended for analyses**
  - .X matrix: gene activity (imputed from chromatin accessibility)
  - Used for: gene expression analysis, cell type annotation
- `combined_sm_motifs.h5ad`: **Motif enrichment scores** for all spots/cells
  - .X matrix: TF motif enrichment scores (870 motifs)
  - Used for: transcription factor activity analysis
- `*_ArchRProject/`: ArchR project directory for R-based analysis

Additional outputs:
- `combined_ge.h5ad`: Gene activity without smoothing
- `combined.h5ad`: Original peak/tile matrix
- `[sample]_g_converted.h5ad`: Per-sample gene activity
- `[sample]_m_converted.h5ad`: Per-sample motif enrichment
- `compare_config.json`: Example grouping file for comparisons
- `cluster_coverages/`, `condition_coverages/`, `sample_coverages/`: BigWig coverage tracks
- `figures/`: QC and analysis plots
- `tables/`: Summary statistics

</data_structure>
