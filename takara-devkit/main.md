<pre_analysis_questions>
- Are you starting with raw fastq files or do you already have an H5AD file ready for secondary analysis?

If **raw fastq**:
  - Is the kit type Seeker 3x3, Seeker 10x10 or Trekker?
  - If Seeker → run Seeker workflow
  - If Trekker → run Trekker workflow
  - Then proceed with the Primary Analysis plan.

If **H5AD** (secondary analysis):
  - Is the kit type Seeker 3x3, Seeker 10x10 or Trekker? (*ONLY ask if not yet known*)
  - Does the H5AD have one or multiple samples?
  - What tissue and disease conditions describe your data?
  - Proceed with the Secondary Analysis plan.
</pre_analysis_questions>

<pre_analysis_step>
MANDATORY: Invoke the `redeem_package` tool to install required Takara tools into the workspace.
  - `package_code`: `3015c6c63ecc3f2cd410ea340a36af05777`
  - `package_version_id`: `192`
</pre_analysis_step>

<plan id="primary_analysis" label="Primary Analysis">
1. Reads to Counts (*FastQ ONLY*) -> `steps/reads_to_counts.md`
2. View Report -> `steps/view_report.md`
</plan>

<plan id="secondary_analysis" label="Secondary Analysis">
1. Data Loading -> `steps/data_loading.md`
2. Background Removal (*Seeker ONLY*) -> `steps/background_removal.md`
3. Quality Control + Filtering -> `steps/qc.md`
4. Normalization -> `steps/normalization.md`
5. Feature Selection -> `steps/feature_selection.md`
6. Dimensionality Reduction -> `steps/dimensionality_reduction.md`
7. Clustering -> `steps/clustering.md`
8. Differential Gene Expression -> `steps/diff_gene_expression.md`
9. Cell Type Annotation -> `steps/cell_typing.md`
</plan>

<self_eval_criteria>
</self_eval_criteria>
