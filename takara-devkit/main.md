<pre_analysis_questions>
There are exactly two valid starting points:

1. **Primary Analysis** — starting with raw FASTQ files (the Seeker or Trekker pipeline has not been run yet).
   - Is the kit type Seeker or Trekker?
   - If Seeker → follow `wf/seeker_pipeline_wf.md`
   - If Trekker → follow `wf/trekker_pipeline_wf.md`
   - Then proceed with the Primary Analysis plan.

2. **Secondary Analysis** — starting with an H5AD file (either produced by a completed Seeker/Trekker pipeline run or provided directly).
   - A successful primary analysis pipeline run always produces an H5AD; if no H5AD is present the primary analysis pipeline did not complete successfully and the user must re-run it (starting point 1).
   - Does the H5AD have one or multiple samples?
   - What tissue and disease conditions describe your data?
   - Proceed with the Secondary Analysis plan.
</pre_analysis_questions>

<pre_analysis_step>
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
