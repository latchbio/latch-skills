<pre_analysis_questions>
There are exactly three valid starting points:

1. **Primary Analysis** — starting with raw FASTQ files (the Seeker or Trekker pipeline has not been run yet).
   - Is the kit type Seeker or Trekker?
   - If Seeker → follow `wf/seeker_pipeline_wf.md`
   - If Trekker → follow `wf/trekker_pipeline_wf.md`
   - Then proceed with the Primary Analysis plan.

2. **Secondary Analysis, Visualization, or Image Overlay** — starting with a single H5AD file (either produced by a completed Seeker/Trekker pipeline run or provided directly).
   - A successful primary analysis pipeline run always produces an H5AD; if no H5AD is present the primary analysis pipeline did not complete successfully and the user must re-run it (starting point 1).
   - What tissue and disease conditions describe your data?
   - Triggers: "analyze my h5ad", "secondary analysis", "visualize my h5ad", "explore my h5ad", "H&E", "overlay".
   - Always run Data Loading (step 1) first. After loading, **always** ask the user: "Would you like to continue with full secondary analysis?"
   - If yes → proceed with the full Secondary Analysis plan (steps 2–9).
   - If no → follow the Visualization Only plan. Even so, offer secondary analysis again at the end.
   - Image overlay is a built-in feature of the data viewer — loading the data is sufficient for this use case.

3. **Multiple H5AD files** — the user has 2 or more H5AD files they wish to combine.
   - Ask: are the files from **adjacent spatial tiles of the same biological sample** (e.g., two Seeker slides from the same tissue), or from **distinct biological conditions** (e.g., experimental vs control)?
   - **Same biological sample (tile stitching):** follow `wf/h5ad_merger_wf.md` first to merge the tiles, then proceed with the Secondary Analysis plan on the merged output.
   - **Distinct biological conditions:** run the full Secondary Analysis plan independently on each H5AD. After all per-sample analyses are complete, optionally follow `wf/h5ad_merger_wf.md` to merge the analyzed files for unified spatial visualization.
   - Do **not** merge distinct biological samples before secondary analysis — the pipeline has no batch correction and joint analysis would confound biological signal with technical variation between samples.
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

<plan id="visualization_only" label="Visualization Only">
1. Data Loading -> `steps/data_loading.md`
2. Ask the user if they would like to proceed with full secondary analysis. If yes, continue with the Secondary Analysis plan starting at step 2.
</plan>

<self_eval_criteria>
</self_eval_criteria>
