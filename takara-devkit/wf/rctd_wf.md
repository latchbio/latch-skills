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

# Do NOT `await execution.wait()` here — RCTD runs for a long time and the user is told they may
# shut the notebook pod down. Check for outputs with the results cell below. See <resuming>.
```

**Resume cell** — generate and run it in the same turn as the launch cell, so the button is on screen
before the user walks away. Clicking it re-runs *this cell in the kernel*; no agent turn is involved,
which matters because nothing in Plots can start one. It reads Latch Data rather than kernel state, so
it also survives a pod restart:
```python
from latch.ldata.path import LPath
from lplots.widgets.button import w_button
from lplots.widgets.text import w_text_output

run_dir = LPath(f"{output_directory_path.rstrip('/')}/{run_name}")   # same values passed in params

resume = w_button(label="Check my RCTD results", key="rctd_resume")

# reading .value makes this cell reactive — the click re-runs it
if resume.value:
    try:
        contents = sorted(p.path for p in run_dir.iterdir())
    except Exception:
        contents = []

    h5ad = next((p for p in contents if p.endswith("_RCTD.h5ad")), None)

    if h5ad is None:
        w_text_output(
            content=(
                f"No `_RCTD.h5ad` under `{run_dir.path}` yet, so the run has not finished writing "
                "its outputs. Check the execution's status in the workflows executions tab; if it is "
                "still running, click this button again once it reaches SUCCEEDED. If it shows "
                "FAILED, tell me and I'll look at the logs."
            ),
            appearance={"message_box": "warning"},
            key="rctd_resume_pending",
        )
    else:
        w_text_output(
            content=(
                f"**RCTD is complete.** Results are in `{run_dir.path}`:\n\n"
                + "\n".join(f"- `{p}`" for p in contents)
                + "\n\nMessage me and I'll merge the per-bead cell types into your working AnnData "
                "and plot them."
            ),
            appearance={"message_box": "success"},
            key="rctd_resume_ready",
        )
```

Unlike the Seeker and Trekker pipelines, the step *after* RCTD is not self-contained — merging
`first_type` / `second_type` / `spot_class` into the working AnnData is analysis code that has to be
written for the specific object in play. So this button confirms the results are ready and tells the
user to message the agent; it cannot finish the step on its own. If `iterdir()` is unavailable in the
runtime, browse the run directory with `w_ldata_browser(dir=run_dir)` instead.
</example>

<long_running_guidance>
After launching the workflow execution, display this message to the user **in full** — do not
shorten it or drop the pod shutdown advice:

"RCTD is now running on Latch compute and will take some time to finish (the fitPixels step is the longest; it logs progress and ETA per batch). It runs independently of this notebook, so it is safe to close this tab — and you may also **shut down the notebook pod while the workflow runs, which stops the notebook compute charges and saves cost**. Shutting the pod down will not interrupt the workflow. You may monitor progress in the workflows executions tab. When the workflow has completed, restart the pod, reopen the notebook, and click **Check my RCTD results** below — it will confirm the results are ready and tell you what happens next."

Because that advice invites the user to shut the pod down, the launch cell must **not** block on
`await execution.wait()` — an await parks the cell in a permanently-running state, binds no result,
and does not survive a pod restart.

Never tell the user that you will "resume and load the results" automatically. Nothing in Plots can
start an agent turn, so that is not true, and it is what leads users to sit waiting and then interrupt
you. Point them at the resume button instead.
</long_running_guidance>

<resuming>
The launch cell does not wait for the execution, and you will not be running when it finishes. The
resume button is what tells the user their results are ready; make sure it is on screen before they
leave. When they then message you — "continue", "is it done?", "RCTD finished", or anything else —
treat that as a resume signal and check Latch Data *before* answering:

- **The notebook is not the source of truth.** The execution runs on Latch compute, outside this pod.
  Never report "RCTD is still running" because a cell looks busy, because `workflow_outputs` is
  undefined, or because you have no record of it completing — none of those are evidence.
- **Check Latch Data.** `<run_name>_RCTD.h5ad` present under `output_directory/<run_name>/` means the
  run finished; nothing there means it is still running or failed, and the user should check the
  workflows executions tab.
- **If kernel state was lost** (pod restarted), do not try to reconstruct `execution` or `res` — they
  are gone and are not needed. Everything downstream is derived from the Latch Data paths.
- Once `<run_name>_RCTD.h5ad` is present, go straight on to step 3 of `steps/rctd.md` and merge the
  labels back into the working AnnData. Do not ask the user to re-confirm that the run finished.
</resuming>
