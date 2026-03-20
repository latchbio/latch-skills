<pre_analysis_questions>
- What tissue and disease conditions describe your data?
- Is the kit type Seeker 3x3, Seeker 10x10 or Trekker?
- Does the H5AD have one or multiple samples?
</pre_analysis_questions>

<pre_analysis_step>
MANDATORY: Invoke the `redeem_package` tool to install required Takara tools into the workspace.
  - `package_code`: `3015c6c63ecc3f2cd410ea340a36af05777`
  - `package_version_id`: `192`
</pre_analysis_step>

<plan>
1. Reads to Counts (*FastQ ONLY*) -> `steps/reads_to_counts.md`
2. Data Loading -> `steps/data_loading.md`
3. Background Removal (*Seeker ONLY*) -> `steps/background_removal.md`
4. Quality Control + Filtering -> `steps/qc.md`
5. Normalization -> `steps/normalization.md`
6. Feature Selection -> `steps/feature_selection.md`
7. Dimensionality Reduction -> `steps/dimensionality_reduction.md`
8. Clustering -> `steps/clustering.md`
9. Differential Gene Expression  -> `steps/diff_gene_expression.md`
10. Cell Type Annotation -> `steps/cell_typing.md`
</plan>

<self_eval_criteria>
</self_eval_criteria>
