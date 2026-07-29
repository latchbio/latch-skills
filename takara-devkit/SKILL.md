---
name: takara-devkit
description: >
  Use this skill when the user is analyzing Takara Seeker or Trekker spatial
  transcriptomics data, ICELL8 or PLL-Seq data, or files and metadata that mention
  Takara, Seeker, Trekker, or paired Trekker FASTQs. Also use it for Takara-derived
  H5AD objects that need QC, background removal, normalization, clustering,
  differential expression, or cell typing.
---

# Takara Seeker / Trekker

Use this skill for Takara platform detection, workflow order, step execution, and
helper-library usage.

## Detect this platform when

- the user mentions `Takara`, `Seeker`, or `Trekker`
- paths or filenames contain `Seeker` or `Trekker`
- metadata identifies Seeker 3x3, Seeker 10x10, or Trekker
- the user has paired FASTQs for a Trekker or Seeker primary analysis run
- the user has a Takara-derived H5AD for secondary exploratory analysis

If the platform is still unclear, ask before executing platform-specific steps.

## First questions

- What tissue and disease conditions describe the data?
- Is the kit type Seeker 3x3, Seeker 10x10, or Trekker?
- Does the H5AD contain one sample or multiple samples?

## Workflow overview

Read `main.md` for the step plan, then load each step doc before executing it.

1. Reads to Counts (FastQ only) — [Trekker workflow](wf/trekker_pipeline_wf.md) or [Seeker workflow](wf/seeker_pipeline_wf.md) depending on kit type, and [step details](steps/reads_to_counts.md)
2. Data Loading — [step details](steps/data_loading.md)
2b. Image Overlay (always offer after loading; e.g. H&E) — [step details](steps/image_overlay.md)
3. Background Removal (Seeker only) — [step details](steps/background_removal.md)
4. Quality Control and Filtering — [step details](steps/qc.md)
5. Normalization — [step details](steps/normalization.md)
6. Feature Selection — [step details](steps/feature_selection.md)
7. Dimensionality Reduction — [step details](steps/dimensionality_reduction.md)
8. Clustering — [step details](steps/clustering.md)
9. Differential Gene Expression — [step details](steps/diff_gene_expression.md)
10. Cell Type Annotation — [step details](steps/cell_typing.md)

RCTD Cell Type Deconvolution (Seeker only, optional) — runs after QC as a separate reference-based track — [step details](steps/rctd.md), [RCTD workflow](wf/rctd_wf.md), [reference builder workflow](wf/rctd_reference_builder_wf.md)

## Important branches

- Run Reads to Counts only when the user starts from FASTQ files.
- Run Background Removal only for Seeker datasets.
- Run RCTD only for Seeker datasets, optionally, after QC. It is a separate track from clustering/DEG/annotation; its per-bead labels complement — and do not replace — marker-based cell-type annotation. The reference can be the user's own `.rds` or one the agent finds and builds from a tissue description.
- If the user already has a processed H5AD, start at the Data Loading step.
- Always ask, right after Data Loading, whether the user has an H&E or other pathology image to overlay — don't wait for them to bring it up. If yes, the image is almost always a separate file from the H5AD; load it and use the viewer's alignment tool to register it. Loading the H5AD alone does not align an image. Open the H5AD viewer with `sync_to` set to its `LPath` (see `steps/data_loading.md`) so the alignment persists back to the file automatically.

## Helper library usage

If a step requires Takara helper code, import from the skill's `lib/` directory:

```python
import sys
sys.path.insert(0, "<skill-root>/lib")

from takara.background_removal import KitType, remove_background
```

Resolve `<skill-root>` to the directory where this skill is checked out in the current environment.

## Requesting files from the user

Whenever a step needs a single file or directory the agent does not already have (e.g. a tissue
image, a reference, an h5ad data file), give the user **both** ways to provide it:

1. Render a `w_ldata_picker` widget so they can select it from Latch Data — set
   `file_type="file"` or `file_type="dir"` to match what the step needs (see the
   `latch-data-access` skill for the full API).
2. Tell them in the same message that they may instead use the **attach button in the Agent
   text interface** if they'd rather, or if the file isn't in Latch Data yet.

Either route is acceptable — use whichever the user supplies first. Render the picker
unconditionally so it is always visible, and always check `.value` for `None` before using it.
The picker returns an `LPath`: use `picker.value.path` when constructing `LatchFile(...)` or
`LatchDir(...)`, and the `LPath` itself for `download(...)` / `sync_to`.

```python
from lplots.widgets.ldata import w_ldata_picker

h5ad_picker = w_ldata_picker(label="H5AD file", file_type="file", key="h5ad_input")

if h5ad_picker.value is not None:
    h5ad_path = h5ad_picker.value          # LPath
```

If neither route works, fall back to asking the user for the Latch Data path directly.

This applies to **simple, single file or directory inputs only**. It does not apply to the
multi-parameter entry for `seeker_pipeline_wf` and `trekker_pipeline_wf` — for those pipelines
build the full parameter entry widget set **and the launch cell at the same time**, exactly as
those workflow docs specify. Never withhold the `w_workflow` cell waiting for the user to confirm
in chat: that cell renders the launch button, so if it isn't generated the customer has no way to
start the pipeline.

## Long-running workflows

Every workflow in `wf/` runs on **Latch compute**, separately from this notebook pod. As soon as
an execution starts, the user must get the `<long_running_guidance>` message from that workflow's
doc — verbatim and in full. This is not optional; if the doc has no such block, say the same thing
in your own words.

**Where the message goes depends on how the workflow is launched:**

- `automatic=True` (the workflow fires when you run the cell): the execution starts inside your
  own turn, so post the message to chat right after running the cell.
- `automatic=False` — the click-to-launch pattern used by `seeker_pipeline_wf` and
  `trekker_pipeline_wf`: the user clicks the button *after your turn has ended*. You are not
  running then and cannot post anything, so the notice must be rendered **by the launch cell
  itself** with `w_text_output(...)`, inside `if execution is not None:`. Also state it in chat
  when you present the cells, worded for what is about to happen.

The message must always tell the user that they may **shut down the notebook pod while the
workflow runs to save on compute costs**, and that doing so will not interrupt the execution.
They restart the pod, reopen the notebook, and the agent resumes when the workflow finishes.

**Never block on `await execution.wait()` in a cell whose workflow the user has been told they may
shut the pod down for.** An `await` parks the cell in a permanently-running state, binds no result,
and does not survive a pod restart — the notebook then looks busy forever and the agent reports
"still running" long after the workflow has succeeded. End the launch cell at the notice, and put
completion checking in a separate results cell. This covers every workflow carrying the pod-shutdown
advice: `seeker_pipeline_wf`, `trekker_pipeline_wf`, `rctd_wf`, `trekker_fxflex_demux_wf`,
`trekker_qp_demux_wf`. The short workflows without that advice (`trekker_merger_wf`,
`fastq_concatenator_wf`, `h5ad_merger_wf`, `rctd_reference_builder_wf`) launch with
`automatic=True` inside your own turn and may keep their in-turn `await` — but do not tell the user
to shut the pod down during one of those.

**Determining that a workflow has finished.** The execution runs on Latch compute, outside this pod,
so the notebook can never tell you its status. Never claim a workflow is still running because a cell
looks busy, because an output variable is undefined, or because you have no record of it completing.
Check **Latch Data** for the expected outputs under the run's output directory, and point the user at
the workflows executions tab for status. After a pod restart, kernel state (`execution`, `res`,
`workflow_outputs`) is gone and is not needed — widget values persist by `key`, and every downstream
step derives from Latch Data paths. See the `<resuming>` block in `wf/seeker_pipeline_wf.md` and
`wf/trekker_pipeline_wf.md`.

This applies only to `wf/` workflow executions. Analyses that run *in* the notebook pod
(`steps/background_removal.md`, `steps/feature_selection.md`,
`steps/dimensionality_reduction.md`, `steps/clustering.md`) have the opposite requirement — the
user must leave the notebook open until they complete.

## Latch-specific execution

If `latch-workflows`, `latch-plots-ui`, or `latch-data-access` are available, prefer them for:

- workflow launching
- Latch widget usage
- plot rendering and AnnData viewers
- Latch Data path handling

If those sibling skills are not available, use the local `wf/`, `steps/`, and `README.md` docs directly.
