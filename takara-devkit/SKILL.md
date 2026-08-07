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
import hashlib
import importlib
import sys
from pathlib import Path

# This skill is checked out under `.claude/skills/` — the same convention `latch-curation`
# uses. Resolve it rather than hard-coding, and never fall back to `technology_docs/takara`;
# see <legacy_technology_docs_path> below for why that path is poison.
_SKILLS_ROOT = Path("/opt/latch/plots-faas/.claude/skills")


def _resolve_takara_lib() -> Path:
    """The `lib/` directory to put on sys.path. Raises rather than silently importing stale code."""
    for cand in (
        _SKILLS_ROOT / "takara-devkit" / "lib",
        _SKILLS_ROOT / "latch-skills" / "takara-devkit" / "lib",
    ):
        if (cand / "takara" / "background_removal.py").is_file():
            return cand
    # Layout changed under us. The skills tree is small, so a search is cheap and beats failing.
    for hit in _SKILLS_ROOT.rglob("takara/background_removal.py"):
        return hit.parent.parent
    raise RuntimeError(
        f"takara lib not found under {_SKILLS_ROOT}. Do NOT substitute the "
        f"technology_docs/takara path — it is a frozen pre-monorepo snapshot."
    )


TAKARA_LIB = str(_resolve_takara_lib())

# Whichever `takara` is imported first pins its __path__ for the rest of the session, so a bare
# sys.path.insert does nothing. Drop the cached package AND refresh the path finders.
for _name in [m for m in sys.modules if m == "takara" or m.startswith("takara.")]:
    del sys.modules[_name]
while TAKARA_LIB in sys.path:
    sys.path.remove(TAKARA_LIB)
sys.path.insert(0, TAKARA_LIB)
importlib.invalidate_caches()

from takara.background_removal import KitType, remove_background
```

Four rules. The first three exist because getting them wrong produces a confusing
`ModuleNotFoundError` naming a *submodule* (`No module named 'takara.optimize_html_images'`) even
though `takara` itself imported fine — the signature of a different `takara` winning the import.
The fourth exists because getting it wrong produces no error at all:

1. **Verify the path before using it.** Never trust a hard-coded lib directory blind —
   `sys.path.insert` of a non-existent directory is a silent no-op.
2. **Purge `sys.modules` and call `importlib.invalidate_caches()`.** The purge handles a package
   bound to another path; `invalidate_caches()` handles cached directory listings that otherwise
   keep a newly-added path's contents invisible.
3. **Use one path convention everywhere in this skill.** Two paths for the same package means
   whichever imports first wins for the session.
4. **Resolve under `.claude/skills/`, never under `technology_docs/`.** The wrong one of those
   two imports successfully and runs months-old code.

For imports that are optional — `takara.optimize_html_images`, used only to shrink report images —
use the non-raising `_load_takara_optimize()` helper in `<takara_lib_import>` at the end of
`wf/seeker_pipeline_wf.md` instead, so a missing library degrades the output rather than failing the
cell.

<legacy_technology_docs_path>
`/opt/latch/plots-faas/runtime/mount/agent_config/context/technology_docs/takara/` is **not** this
skill. It is a frozen snapshot of takara-devkit from before it moved into the latch-skills monorepo,
retained only so older notebooks that hard-code it keep importing. Nothing merged since the move has
ever reached it.

It is dangerous specifically because it looks healthy:

- **`import takara` succeeds from it.** There is no error to notice — you get a real package with
  `remove_background` and `KitType`, just an old one.
- **Its files carry today's mtimes.** The copy job re-runs on pod start, so `ls -l` shows a
  timestamp from minutes ago on content that is months old. Freshness of mtime says nothing.
- **The branch you launch the pod from does not change it.** It is a snapshot, not a checkout, so
  launching from a feature branch leaves it exactly as it was.

Its contents are the takara-devkit tree at the migration commit, minus `SKILL.md` — 15 files,
`lib/takara/` holding only `__init__.py` (178 bytes) and `background_removal.py` (3,040 bytes). If
you see two `.py` files in `lib/takara/`, you are in the snapshot.

This cost a full investigation: a 3-billion-read run was benchmarked "old code vs new code" at 3.5 h
and 5 h, and both numbers were the *same* old code — the optimizations under test had never
executed. **Confirm the build id before trusting any timing measurement**; `steps/background_removal.md`
has the check.
</legacy_technology_docs_path>

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

**Never end your turn waiting for a widget to be filled in.** Nothing in Plots can start an agent
turn, so a picker you render and then walk away from produces a dead notebook: the user selects a
file, nothing happens, and after a few minutes they conclude you have hung and interrupt you. This
has already happened at the RCTD reference-builder step. Either

- ask for the value **in chat** and read it from their reply, or
- render the picker in the **same cell** as the button that consumes it, so their selection arms a
  click they can make themselves.

The reactive kernel re-runs that cell when the widget value changes, so the button enables on its
own — see the pattern in `wf/seeker_pipeline_wf.md`. A widget whose value only *you* can act on is a
widget the user cannot use.

This applies to **simple, single file or directory inputs only**. It does not apply to the
multi-parameter entry for `seeker_pipeline_wf` and `trekker_pipeline_wf` — for those pipelines
build the full parameter entry widget set **and the launch cell at the same time**, exactly as
those workflow docs specify. Never withhold the launch cell waiting for the user to confirm
in chat: that cell renders the launch button, so if it isn't generated the customer has no way to
start the pipeline.

## Telling the user where results appeared

Plots opens a **new tab for each analysis** — reads to counts, the H5AD viewer, QC filtering,
normalization, feature selection, DEG, and so on. This is platform behavior and cannot be changed
from this skill. The tab is created, but the notebook **does not switch to it**: the user keeps
looking at the tab they were already on and sees nothing happen. To them the agent has stalled.

**So every time a step produces a new tab, say so in your chat message.** Two rules make this work:

1. **Put the pointer in chat, not only in the notebook.** A `w_text_output` that says "your results
   are in a new tab" renders *inside that new tab* — the one the user hasn't clicked. It is invisible
   to exactly the person who needs it. The chat panel is the only surface that is always in view.
   Notebook-rendered notices are still useful for the user who *has* clicked through; they are never
   a substitute for saying it in chat.
2. **Name the tab and say what is in it**, so the user knows which tab to click and what they are
   looking for when they get there. If you control the tab or cell name, name it for the step
   ("Clustering"); if you don't, describe the result concretely enough to recognize.

Template — adapt the specifics, keep the structure:

> Clustering is done. The results opened in a **new tab** named **Clustering** — click
> that tab in the notebook to see the UMAP and spatial embeddings. The notebook doesn't switch to it
> automatically.

Say it **every time**, including for steps later in the same session. Users do not reliably
generalize from the first one, and a missed tab reads as a broken agent rather than a missed click.

In **chat**, never place things with "above", "below", or "in the cell I just ran" — relative to the
tab the user is looking at, they are somewhere else entirely. Say which tab, then place things within
it. Inside a notebook-rendered `w_text_output`, "below" is fine and often clearer, because that text
sits next to the thing it is pointing at. Either way, never imply the view will change on its own.

This applies to `steps/` analyses and to the `wf/` parameter-entry, launch, and resume-button cells
alike. It matters most for anything the user must **click** — a launch button or a resume button
sitting in an unopened tab is the same as no button at all.

## Launching a workflow at most once

A Seeker test session started **two RCTD deconvolutions ten seconds apart**, both of which ran to
completion on Latch compute at full cost. Nobody asked for two. The sequence was:

```
Cell "Launch RCTD" failed          ← the registered wf_name was wrong, as its doc warns
Edited cell "Launch RCTD"          ← the edit RE-RAN the cell → execution #1
Ran cell "Launch RCTD"             ← the agent, unsure it had launched → execution #2, 8s later
```

Nothing about that is exotic — it is what fixing a broken cell looks like. The trap is that
`w_workflow(automatic=True)` launches on *every* run of its cell, and **in Plots, editing a cell
runs it**. Five rules:

1. **Call `launch_workflow_once` from `takara.launch`, never `w_workflow` directly**, for anything
   in `wf/`. It derives the widget key from a hash of the parameters and asks Latch whether a
   matching execution is already in flight before it renders anything, so a repeat launch is a no-op
   with an explanation instead of a second run. Widget keys alone cannot do this: they do not
   survive the agent rewriting the cell, a pod restart, or a second agent turn.
2. **Keep the fix-and-retry loop out of the launch cell.** Resolve `wf_name`/`version`, build
   `params`, and validate them in a *separate earlier cell* that contains no launch call. Iterate
   there freely — it starts nothing. This is the one rule that would have prevented the incident
   above on its own.
3. **Editing a launch cell runs it.** Never follow an edit of a launch cell with an explicit run.
4. **Never re-run a launch cell to find out whether it worked.** Read the workflows executions tab,
   Latch Data, or `takara.launch.find_live_executions(wf_name)` — all of which observe without
   launching. A launch cell that "ran successfully" has launched.
5. **One launch cell per workflow per notebook.** If it needs changing, edit that cell. Never create
   a second `w_workflow` cell for the same workflow and never invent a fresh key (`rctd_run_2`,
   `rctd_run_final`) to force a relaunch — a changed *parameter* is what authorizes a new run.

Read `res.status` and respond to what it says rather than assuming a launch happened:
`LAUNCHED` (started), `BLOCKED_RUNNING` (already in flight — name the existing execution, do not
retry), `ALREADY_COMPLETE` (point at the resume button), `DEGRADED` (the duplicate check could not
reach Latch, so the button rendered disarmed — the user clicks it), `LAUNCH_ARMED` (`automatic=False`,
waiting on a click).

**A repeated confirmation is not a request for a second run.** "Yes", "go ahead", "continue", and
"is it running?" all arrive when a user cannot see what is happening. Check for a live execution
before acting on any of them.

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

**Always render a resume button next to the launch cell.** Nothing in Plots can start an agent turn —
`w_button`, `w_workflow` and the reactive `.value` mechanism all re-run *cells in the kernel*, and none
of them posts to the agent chat. So when a long workflow finishes hours later, you are not running and
cannot act. Without a button already on screen, the user's only recourse is to interrupt you and type
"continue", which is confusing and undiscoverable. Every workflow carrying the pod-shutdown advice
therefore gets a `w_button` rendered in the same turn as its launch cell, gated on `if button.value:`,
that reads Latch Data and either reports the outputs or says the run is not done yet. Where the next
step is self-contained — the Seeker and Trekker QC report — the button performs it in full, so the
happy path needs no agent turn at all. Never promise the user that you will "resume from where you
left off": you cannot, and saying so is what makes them sit and wait.

**Never construct an output path from a guess.** Each workflow doc's `<outputs>` section records the
directory layout that workflow actually writes, verified against the deployment source in
`latch_platform/`. Read it before looking for a result file. Two rules follow from it:

- **Anchor at the output directory the user chose** and search downward for the file by suffix
  (`_Report.html`, `_RCTD.h5ad`, `.fastq.gz`), rather than assembling a full path from the
  parameters. Run directories are nested more deeply than the parameters suggest — Trekker puts
  `<analysis_date>_<sample_id>/trekker_<sample_id>/output/` between `output_dir` and the report — and
  a constructed path that is wrong reports "the pipeline hasn't finished" for a run that succeeded.
- **Filenames are not always what the parameter names imply.** Trekker's report is
  `<sample_id>_Trekker_Report.html` for the standard report and `<sample_id>_Report.html` only for the
  extended one, so match a suffix and prefer the expected variant.

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
