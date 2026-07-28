<goal>
Run Robust Cell Type Deconvolution (RCTD) on a Seeker spatial dataset against a single-cell reference, assigning a cell type (and a possible second cell type) to every bead.
</goal>

<scope>
**Seeker only.** RCTD is appropriate for Seeker data, where each bead captures ~1–3 cells, and the workflow runs in **doublet mode** (each bead → singlet / doublet / reject). Do **not** run it on Trekker data.

This workflow is the deconvolution engine. Acquiring the reference `.rds` (either the user's own file or one built automatically from a tissue description) is handled in `steps/rctd.md`; build the reference there **before** launching this workflow.
</scope>

<parameters>
- **`run_name`** (`str`, **required**) — Names the run and the output subdirectory. No spaces. Must be provided — do not use a placeholder.
- **`input_data`** (`LatchFile`, **required**) — The **query** spatial dataset: the QC-filtered AnnData (raw counts in `.X`, spatial coordinates in `.obsm["spatial"]` or `.obsm["X_spatial"]`) written to Latch as `.h5ad`. A Seurat `.rds` with an `RNA` assay and a `SPATIAL` reduction is also accepted. Use the **QC-filtered, pre-normalization** object — RCTD models raw counts.
- **`reference_data`** (`LatchFile`, **required**) — The single-cell reference `.rds`: a spacexr `Reference` object (preferred — what `wf/rctd_reference_builder_wf.md` produces) or a Seurat object with a `cell_type` metadata column. Mouse Ensembl gene IDs are auto-mapped to symbols.
- **`output_directory`** (`LatchOutputDir`, **required**) — Latch directory for outputs. Results land in `output_directory/<run_name>/`. Default `latch:///RCTD_Output`; ask the user for an explicit path.

Advanced parameters (defaults are tuned for Seeker — only surface them if the user asks):

| Parameter | Default | Description |
|---|---|---|
| `UMI_min` | `100` | Minimum UMIs per bead included in the analysis (filters empty beads). |
| `UMI_min_sigma` | `100` | Minimum UMIs for a bead to enter sigma estimation. |
| `gene_count_min` | `0` | Minimum gene count threshold. |
| `gene_cutoff` / `fc_cutoff` | `0.000125` / `0.5` | Gene expression / log-fold-change cutoffs for platform-effect normalization. |
| `gene_cutoff_reg` / `fc_cutoff_reg` | `0.0002` / `0.75` | Gene expression / log-fold-change cutoffs for the RCTD regression step. |
| `max_cores` | `8` | Cores for `create.RCTD` / `choose_sigma_c` (negligible scaling beyond 8). |
| `max_sigma_iter` | `3` | Safety ceiling on sigma optimization iterations (exits early on convergence). |
| `max_cand` | `5` | Max candidate cell types per bead in doublet scoring. `5` suits Seeker (1–2 cells/bead); raise to 10–15 only for denser platforms. |
| `fitpixels_cores` | `24` | Cores for the (longest) `fitPixels` step; auto-reduced to fit RAM. |
| `fitpixels_batch_size` | `25000` | Beads per `fitPixels` batch; smaller = more frequent progress logs + lower per-worker memory. |

Note: there is **no `mode` parameter** — doublet mode is built in. State this to the user; do not attempt to pass a mode.
</parameters>

<outputs>
Written to `output_directory/<run_name>/`:
- `<run_name>_RCTD.rds` — full spacexr `RCTD` object.
- `<run_name>_RCTD_annotation.txt` — tab-separated `Barcode`, `First_Cell_Type`, `Second_Cell_Type`, `Confidence_Level`.
- `<run_name>_RCTD_seurat.rds` — input Seurat object + RCTD metadata (`first_type`, `second_type`, `spot_class`).
- `<run_name>_RCTD_spatial.png` — spatial scatter coloured by `first_type`.
- `<run_name>_RCTD.h5ad` — **AnnData version of the annotated object** (`first_type` / `second_type` / `spot_class` in `.obs`). This is the file `steps/rctd.md` loads to merge labels back into the working AnnData.
</outputs>

<instructions>
After the reference `.rds` and the QC-filtered query `.h5ad` are both staged on Latch, confirm with the user before launching:
> "Reference and query are ready. RCTD will run in doublet mode on Latch compute. Let me know when you're ready to start."

Only generate and execute the code cell once the user confirms.

> ⚠️ Confirm the registered workflow name and version before launching. As of writing the RCTD deployment registers under display name "RCTD" (function `rctd_wf`, version `1.0.2`); the `.latch/workflow_name` file currently reads `wf.__init__.RCTD_workflow`. If the launch fails with an unknown-workflow error, look up the exact `wf_name`/`version` from the Latch workflows registry and use those.
</instructions>

<example>
```python
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir

params = {
    "run_name": "",                                  # required — set by user, no spaces
    "input_data": LatchFile("latch://..."),          # required — QC-filtered query .h5ad on Latch
    "reference_data": LatchFile("latch://..."),      # required — reference .rds (builder output or user's own)
    "output_directory": LatchDir("latch://..."),     # required — set by user
    # advanced params default to Seeker-tuned values; only add if the user changes them
}

w = w_workflow(
    wf_name="wf.__init__.rctd_wf",   # confirm against the registered RCTD workflow (see instructions)
    key="rctd_run_1",
    version="1.0.2-9e8dc3",          # confirm against the registered version
    params=params,
    automatic=True,
    label="RCTD",
)
execution = w.value

if execution is not None:
    res = await execution.wait()

    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        # outputs (including <run_name>_RCTD.h5ad) are under output_directory/<run_name>/
        workflow_outputs = list(res.output.values())
```
</example>

<long_running_guidance>
After launching the workflow execution, display this message to the user **in full** — do not
shorten it or drop the pod shutdown advice:

"RCTD is now running on Latch compute and will take some time to finish (the fitPixels step is the longest; it logs progress and ETA per batch). It runs independently of this notebook, so it is safe to close this tab — and you may also **shut down the notebook pod while the workflow runs, which stops the notebook compute charges and saves cost**. Shutting the pod down will not interrupt the workflow. You may monitor progress in the workflows executions tab. When the workflow has completed, restart the pod, reopen the notebook, and the agent will resume and load the results."
</long_running_guidance>
