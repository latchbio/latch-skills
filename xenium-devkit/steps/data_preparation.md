# Step 0 — Data Preparation / Data Transform

<goal>
Convert raw Xenium output directories into an `.h5ad` plus viewer-ready assets (e.g. pmtiles) for downstream analysis.
</goal>

<method>
Auto-detect raw Xenium outputs and launch `xenium_preprocess_workflow` via `w_workflow` when no `.h5ad`, `pmtiles` are attached.
</method>

<workflows>
- `wf/xenium_preprocess_wf.md`
</workflows>

<library>
- `lplots.widgets.workflow`
- `latch.ldata.path`
</library>

<self_eval_criteria>
- All expected Xenium raw files are present in the input directory.
- When this step is run, the attached Xenium output directory contains the following files:
    - `morphology_focus.ome.tif`
    - `morphology_mip.ome.tif`
    - `analysis.tar.gz`
    - `transcripts.parquet`
    - `cell_boundaries.parquet`
    - `cell_feature_matrix.h5`
    - `cells.parquet`
- Workflow completes and produces a processed `.h5ad` and viewer assets.
</self_eval_criteria>
