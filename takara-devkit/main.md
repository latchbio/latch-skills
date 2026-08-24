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
   - Always run Data Loading (step 1) first, opening the viewer with `sync_to` set to the H5AD's `LPath` per `steps/data_loading.md`. After loading, **always** ask the user whether they have an H&E or other pathology image they'd like to overlay (→ `steps/image_overlay.md` if yes), then **always** ask: "Would you like to continue with full secondary analysis?"
   - If yes → proceed with the full Secondary Analysis plan (steps 2–9).
   - If no → follow the Visualization Only plan. Even so, offer secondary analysis again at the end.
   - The image overlay offer is not conditional on the user mentioning "H&E"/"overlay" themselves — ask proactively every time spatial data is loaded, since the image is almost always a separate file from the H5AD and needs to be loaded and registered with the viewer's alignment tool. This is not automatic from loading the H5AD alone.

3. **Multiple H5AD files** — the user has 2 or more H5AD files they wish to combine.
   - Ask: are the files from **adjacent spatial tiles of the same biological sample** (e.g., two Seeker slides from the same tissue), or from **distinct biological conditions** (e.g., experimental vs control)?
   - **Same biological sample (tile stitching):** follow `wf/h5ad_merger_wf.md` first to merge the tiles, then proceed with the Secondary Analysis plan on the merged output.
   - **Distinct biological conditions:** run the full Secondary Analysis plan independently on each H5AD. After all per-sample analyses are complete, optionally follow `wf/h5ad_merger_wf.md` to merge the analyzed files for unified spatial visualization.
   - Do **not** merge distinct biological samples before secondary analysis — the pipeline has no batch correction and joint analysis would confound biological signal with technical variation between samples.
</pre_analysis_questions>

<pre_analysis_step>
Applies to every step in every plan below: each analysis opens in its **own tab** in Plots, and the
notebook does not switch to it. Whenever a step produces a tab, say so in your chat message — name
the tab and say what is in it — before moving on. See "Telling the user where results appeared" in
`SKILL.md` for the wording, and each step doc's `<new_tab_notice>` for a step-specific example.

A step that renders more than one plot into its tab must give each figure its own variable. A shared
`fig` makes every plot in the tab show the last one, with no error — see "Rendering figures — one
variable per plot" in `SKILL.md`.
</pre_analysis_step>

<plan id="primary_analysis" label="Primary Analysis">
1. Reads to Counts (*FastQ ONLY*) -> `steps/reads_to_counts.md`
2. View Report -> `steps/view_report.md`
</plan>

<plan id="secondary_analysis" label="Secondary Analysis">
1. Data Loading -> `steps/data_loading.md`
1b. Image Overlay (*always offer, optional*) -> `steps/image_overlay.md`
2. Background Removal (*Seeker ONLY*) -> `steps/background_removal.md`
3. Quality Control + Filtering -> `steps/qc.md`
3b. RCTD Cell Type Deconvolution (*Seeker ONLY, recommended — user may skip*) -> `steps/rctd.md`
4. Normalization -> `steps/normalization.md`
5. Feature Selection -> `steps/feature_selection.md`
6. Dimensionality Reduction -> `steps/dimensionality_reduction.md`
7. Clustering -> `steps/clustering.md`
8. Differential Gene Expression -> `steps/diff_gene_expression.md`
9. Cell Type Annotation -> `steps/cell_typing.md`

Step 3b (RCTD) is a **Seeker-only** reference-based track that runs on the QC-filtered raw counts. **Always recommend it, and always at this position** — after step 3 (QC + Filtering) and before step 4 (Normalization) — because RCTD needs raw counts and normalization overwrites `.X`. Recommend it in the same message that offers the skip: the user may decline, and if they do, go straight to step 4 without re-asking. Steps 4–9 (normalization → clustering → DEG → annotation) are a separate track and run unchanged either way. When RCTD is run, its per-bead labels are written into `adata.obs` and consumed at step 9 to label and validate Leiden clusters — complementing, not replacing, marker-based annotation. **Once RCTD is launched, stop the track at step 3b until it finishes** — do not start step 4. Steps 4–8 would run correctly, but they end at step 9, which needs RCTD's labels, and they fill the kernel with results that a pod shutdown would lose. Pausing at 3b costs nothing: the QC-filtered object is already on Latch, so the user can shut the pod down while RCTD runs and reload one file on return. See `<hard_stop>` in `steps/rctd.md`; the user may override and work ahead if they ask. Step 9 enforces the precondition in code either way — `takara.annotation.require_rctd_for_annotation` raises for Seeker data with RCTD outstanding, and warns for Seeker data annotated without it (`<guard>` in `steps/cell_typing.md`). For Trekker data none of this applies: RCTD is not recommended there, its absence is not a shortfall, and step 9 proceeds on markers alone with no waiting and no warning.
</plan>

<plan id="visualization_only" label="Visualization Only">
1. Data Loading -> `steps/data_loading.md`
1b. Image Overlay (*optional*) -> `steps/image_overlay.md`
2. Ask the user if they would like to proceed with full secondary analysis. If yes, continue with the Secondary Analysis plan starting at step 2.
</plan>

<self_eval_criteria>
- No tab renders two plots with identical content — every `w_plot` in a multi-plot tab draws a
  distinctly named figure variable, and no figure is bound to `fig`
</self_eval_criteria>
