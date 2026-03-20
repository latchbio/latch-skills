## 10X Xenium Analysis Guideline

<pre_analysis_questions>
- Is an `.h5ad` already present in the attached data?
- Are there multiple samples / batches that need to be integrated?
- Does the attached folder contain raw Xenium outputs (e.g. `transcripts.parquet`, `cell_feature_matrix.h5`) that require preprocessing?
- Does the attached folder contain preprocessing output `analysis.tar.gz`?
</pre_analysis_questions>

<pre_analysis_step>
MANDATORY: Invoke the `redeem_package` tool to install required Xenium tools into the workspace.
  - `package_code`: `7a4f4bd980b3739a825072a975dd9a376c267ff7c84c1c9c59c8da196e58c3bd`
  - `package_version_id`: `401`
</pre_analysis_step>

<plan>
0. Data Preparation — Convert raw Xenium outputs to an `.h5ad` and viewer-ready assets. -> `steps/data_preparation.md`
1. Data Loading — Load `.h5ad`, attach spatial tiles, and render with `w_h5`. -> `steps/data_loading.md`
2. Preprocessing — QC, normalization, PCA, Harmony (if needed), UMAP and Leiden. **only if the user confirms** -> `steps/preprocessing.md`
  - If embeddings or clusters already exist in adata, do not run preprocessing yet. Ask for confirmation in **Step 2** before recomputing.
3. Differential Gene Expression (DGE) — identify marker genes per cluster and eport top marker genes for each cluster and make dot plots with scanpy -> `steps/differential_expression.md`
4. Cell Type Annotation — Use CellGuide markers and vocab configs for clean labels. -> `steps/cell_type_annotation/cell_type_annotation.md`
5. Neighbors Enrichment Analysis — Build spatial neighbor graph and enrichment metrics. -> `steps/spatial_analysis.md`
6. Domain Detection (optional) — Optionally detect tissue domain with workflow. -> `wf/domain_detection_wf.md`
  - Load output h5ad object from workflow and visualize detected domain in spatial embedding. (e.g. `labels_scaled_gaussian_*` in `obs`) in spatial embedding.
7. Cell Segmentation (optional) — Optionally resegment cells using the full-resolution TIFF. -> `steps/cell_segmentation_wf.md`
</plan>

<self_eval_criteria>
- A single coherent `AnnData` object with counts, metadata, and spatial coordinates is available.
- All subsequent steps can run without users supplying explicit file paths.
</self_eval_criteria>

## General Workflow Rules

- **Render figures** using `w_plot` (and table widgets where appropriate).
  - Do **NOT** reuse the variable name `fig`. Use descriptive names: `fig_qc`, `fig_umap`, etc.
  - For non-Scanpy figures, use **Plotly**.
- Keep objects and outputs reproducible: never overwrite without user consent; create new keys/versions.
- Do not use lplots.widgets.number.
