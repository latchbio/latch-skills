<goal>
Convert one chosen single-cell reference into an RCTD-compatible spacexr `Reference` `.rds`. The input is a single reference — a `.h5ad` or `.rds` file (attached from LData) **or** a download URL to one. The output is a spacexr `Reference` `.rds` ready to pass to `wf/rctd_wf.md`.
</goal>

<scope>
This workflow is a **pure converter** (resolve → standardize → build → validate → save). It does **not** search any atlas. Deciding *which* reference to use — interpreting the user's tissue, searching CELLxGENE / Tabula Sapiens / Allen / GEO / TOME / others, presenting candidates, and disambiguating — happens conversationally in `steps/rctd.md` **before** this workflow is launched. Arrive here only once a single reference (file or URL) is chosen.

Why a dedicated workflow rather than converting inline: the RCTD reference must be an R-serialized spacexr `Reference` object built under the **same pinned Seurat 4.4.0 / SeuratObject 4.1.4** stack the RCTD image uses. The Plots notebook is a Python kernel with no R/spacexr, and web references ship as AnnData or Seurat v5 (which 4.4.0 cannot deserialize). This workflow rebuilds the object under the RCTD image's R stack to emit a version-compatible object regardless of the original format.
</scope>

<parameters>
Provide **exactly one** reference source (`reference_file` or `reference_url`):
- **`run_name`** (`str`, **required**) — Names the run and output subdirectory. No spaces.
- **`reference_file`** (`LatchFile`, optional) — A reference from LData: an AnnData (`.h5ad`) or an R object (`.rds` — a spacexr `Reference` or a Seurat object). Use this for user-supplied references, whether they picked it with a `w_ldata_picker` (`file_type="file"`) or attached it with the attach button.
- **`reference_url`** (`str`, optional) — A direct download URL to a `.h5ad` or `.rds`. The workflow downloads it in compute (robust for large atlases). Use this for references you found on the web (CELLxGENE/TOME/MOCA/etc.) or a URL the user pasted. The URL **path** must end in `.h5ad`/`.h5`/`.rds` (a trailing `?signed-query-string` is fine); if a source only offers an extension-less link (e.g. some figshare `ndownloader` links), have the user download it to LData and supply it via `reference_file` instead — either by selecting it in a `w_ldata_picker` you render or with the attach button in the Agent interface (or by providing its Latch Data path).
- **`cell_type_column`** (`str`, default `"cell_type"`) — The cell-type column: an `.obs` column for `.h5ad`, or a `meta.data` column for a Seurat `.rds`. CELLxGENE uses `cell_type`. If it isn't found the builder tries a short list of synonyms (`celltype`, `annotation`, `cell_ontology_class`, …) and otherwise fails with the available columns listed, so you can correct it and relaunch. **Cluster columns (`louvain`, `leiden`, `cluster`, `seurat_clusters`) are never substituted automatically** — cluster IDs are not cell types, and a reference labelled `1..63` would build fine and then deconvolve into meaningless labels. Name one explicitly if that really is the annotation.
- **`max_cells_per_type`** (`int`, default `1000`) — Per-cell-type downsample cap (controls RCTD memory). Each type is randomly downsampled to at most this many cells.
- **`min_cells_per_type`** (`int`, default `25`) — Cell types with fewer cells than this are dropped (RCTD needs a minimum per type).
- **`output_directory`** (`LatchOutputDir`, **required**) — Latch directory for outputs. The reference lands in `output_directory/<run_name>/`. Collect it with a `w_ldata_picker` (`file_type="dir"`), prefilled with a directory the user chose earlier in the session if there is one — see `<instructions>` and "Asking for an output directory" in `SKILL.md`.

Notes:
- The file type is detected by extension: `.h5ad`/`.h5` → AnnData path (standardized in Python, then built in R); `.rds` → read directly in R (a spacexr `Reference` is re-validated; a Seurat object has its counts + `cell_type_column` extracted). A Seurat **v5** `.rds` cannot be read by SeuratObject 4.1.4 — if that fails, ask the user for a `.h5ad` instead — via a `w_ldata_picker`, the attach button in the Agent interface, or its Latch Data path.
- For `.h5ad`, the builder picks the rawest counts (`.layers['counts']` → `.raw.X` → `.X`) and a gene-symbol var column when present — but it now **verifies by value, not by name**, before the read: each matrix is classified as raw / log-normalized / scaled, a matrix classified non-raw is skipped even if it is called `counts`, and a file where nothing is raw fails in seconds with `NO_RAW_COUNTS` naming what it found. Figure objects (`Fig1_*`, `*_processed`, an HVG subset of a few thousand genes) fail here; see `<failure_recovery>` tier 2.
</parameters>

<outputs>
Written to `output_directory/<run_name>/`:
- `<run_name>_reference.rds` — the spacexr `Reference` object. **This is the file to pass as `reference_data` to `wf/rctd_wf.md`.**
- `<run_name>_reference_summary.txt` — per-cell-type counts, gene count, and the source (filename or URL).
- `<run_name>_reference_celltypes.png` — bar plot of cells per cell type after curation.
- `<run_name>_reference_FAILED.txt` — **written only when the build fails**, and uploaded before the
  task errors. It carries `error code:`, what went wrong, what to try next, the parameters, a
  **`reference facts:`** block, a resource snapshot, and the last 80 log lines of the failing stage.
  `reference facts:` is what the file turned out to hold — each matrix with its value range (`raw` /
  `normalized` / `scaled`), the `.obs` columns, and any cluster-like columns — and it is what lets
  you tell "wrong column name, relaunch" from "this reference can never work" without opening the
  console log. A failed Latch task uploads no other outputs, so this file is how you diagnose a
  failure from the notebook without asking the user to paste console logs. Read it — do not guess at
  the cause. See `<failure_recovery>`.
</outputs>

<instructions>
Confirm the resolved source and cell-type column with the user before launching, echoing them back:
> "I'll convert this reference into an RCTD-compatible object: source=<file or URL>, cell-type column=<cell_type_column>, capped at <max_cells_per_type> cells/type. Ready?"

After it completes, hand `<run_name>_reference.rds` to `wf/rctd_wf.md` as `reference_data` — derive
that path from the parameters you already have rather than asking the user for it again.

**Have `output_directory` and `run_name` before you generate anything.** Ask for the output directory
with a `w_ldata_picker` (`file_type="dir"`) — never as free text alone — rendered back in
`steps/rctd.md` step 1, in the same message that presents the reference candidates. The user's reply
choosing a reference is the turn in which you read the picker's `.value`, so nothing is left waiting
on a widget: render the picker on its own with "let me know when you've picked one" and you get the
stall this step has already produced, because nothing in Plots can start an agent turn. Prefill
`default=` with a directory the user chose earlier in the session if there is one, and offer no
default if there isn't. See "Asking for an output directory" in `SKILL.md`.

By the time you generate the two cells below, `OUTPUT_DIR` is a resolved `latch://` string — from the
picker or from the user's message — not a placeholder to be filled in later.

> ⚠️ Confirm the registered `wf_name`/`version` against the Latch workflows registry before launching (the reference-builder is a separate registration from RCTD). Do that lookup in cell 1, which cannot launch anything.

Generate **two cells** — resolve, then launch. The split exists because the launch cell fires an
execution every time it runs, and in Plots editing a cell runs it; keeping the `wf_name` lookup and
the parameter fixes in a cell with no `w_workflow` in it means a retry costs nothing. The full
reasoning is in the `<launch_discipline>` block of `wf/rctd_wf.md`, and it applies here too.
</instructions>

<example>
**Cell 1, resolve and validate — cannot launch anything.** Every retry lives here.
```python
from latch.types import LatchFile, LatchDir

WF_NAME = "wf.__init__.rctd_reference_builder_wf"  # confirm against the registered workflow
VERSION = "0.4.0-0b7745"                           # confirm against the registered version;
                                                   # 0.3.0+ writes the failure report below,
                                                   # 0.4.0+ adds `reference facts:` to it and
                                                   # fails fast with NO_RAW_COUNTS
RUN_NAME = ""                                      # required — no spaces
OUTPUT_DIR = "latch://..."                         # required — the directory the user selected in the
                                                   # output-directory picker (or gave you in chat)

params = {
    "run_name": RUN_NAME,
    # Provide exactly ONE of the next two:
    "reference_url": "https://.../reference.h5ad",    # a .h5ad/.rds URL you found, or the user pasted
    # "reference_file": LatchFile("latch://..."),     # a user-attached .h5ad/.rds in LData
    "cell_type_column": "cell_type",                 # confirm for non-CELLxGENE sources / user files
    "max_cells_per_type": 1000,
    "min_cells_per_type": 25,
    "output_directory": LatchDir(OUTPUT_DIR),        # required
}

print("WORKFLOW PARAMETERS:")
for k, v in params.items():
    print(f"  {k}: {v}")

assert RUN_NAME and " " not in RUN_NAME, "run_name is required and must not contain spaces"
assert ("reference_url" in params) != ("reference_file" in params), "provide exactly one source"
```

**Cell 2, launch.** This workflow is short, so the in-turn `await` is fine — but only when the guard
actually launched something.
```python
# resolve takara/lib per SKILL.md "Helper library usage", then:
from takara.launch import LaunchStatus, launch_workflow_once

res = launch_workflow_once(
    wf_name=WF_NAME,
    version=VERSION,
    params=params,
    label="RCTD Reference Builder",
    key_prefix="rctd_ref_builder",   # key is derived — do NOT pass a hand-written key
    run_name=RUN_NAME,
    output_dir=OUTPUT_DIR,
    automatic=True,
)
print(res.status.value, res.message)

reference_rds = None
build_failure = None
if res.status is LaunchStatus.LAUNCHED:
    done = await res.execution.wait()

    if done is not None and done.status == "SUCCEEDED":
        # <run_name>_reference.rds is under output_directory/<run_name>/. This path is exactly what
        # wf/rctd_wf.md takes as `reference_data` — hand it over, do not re-ask the user for it.
        reference_rds = f"{OUTPUT_DIR.rstrip('/')}/{RUN_NAME}/{RUN_NAME}_reference.rds"
        workflow_outputs = list(done.output.values())
    elif done is not None:
        # The failure report is the diagnosis. Print it — every recovery decision comes from it,
        # and the user can read it too.
        from pathlib import Path

        from latch.ldata.path import LPath

        print(f"Reference build {done.status}.")
        remote = f"{OUTPUT_DIR.rstrip('/')}/{RUN_NAME}/{RUN_NAME}_reference_FAILED.txt"
        try:
            local = Path("/tmp") / f"{RUN_NAME}_reference_FAILED.txt"
            LPath(remote).download(local)
            build_failure = local.read_text()
            print(build_failure)
        except Exception as e:
            # No report means the task died before it could write one (an infra failure, or a
            # pod that vanished). Fall back to the console log.
            print(f"No failure report at {remote} ({e}).")
            print(f"Open the execution log on the Latch console: {res.execution.id}")
elif res.status is LaunchStatus.BLOCKED_RUNNING:
    # Already building. Do not relaunch, and do not re-run this cell to check on it.
    print(res.existing.describe())
```
</example>

<failure_recovery>
**A failed build is a fork in the conversation, not a dead end — and never a silent retry.** When
`done.status` is anything but `SUCCEEDED`:

1. **Read `<run_name>_reference_FAILED.txt`** (the cell above prints it). Two parts matter: the
   `error code:` line, which picks the recovery tier below, and the **`reference facts:`** block,
   which describes what the file actually holds — every matrix with its value range, the `.obs`
   columns, and any cluster-like columns. Between them you can diagnose without the console log.
   Never relaunch on a guess, and never relaunch the exact same parameters — that reproduces the
   same failure and burns another wait.
2. **Tell the user what happened in one or two plain sentences**, naming the reference that failed.
   Not "the workflow failed" — "the mouse embryo reference from CELLxGENE is 1.4M cells and ran out
   of memory while loading".
3. **Offer the recovery that matches the code.** For tiers 2 and 3, do the searching *before* you
   write the message so it carries actual candidates — see step 4 below and `steps/rctd.md` **1f**.

Codes fall into four tiers. The tier decides the recovery — read it off the report, don't improvise.

**Tier 1 — the reference is fine, fix a parameter and relaunch. Do not search.**

| `error code:` | What it means | What to offer |
|---|---|---|
| `CELL_TYPE_COLUMN_NOT_FOUND` | The column name was wrong. The report lists the available `.obs` columns, and names any cluster-like columns (`louvain`/`leiden`/…) separately — those are never used automatically, because cluster IDs are not cell types. | Pick the right column from that list yourself, name it, and ask to relaunch. If the *only* labels are cluster IDs, treat the reference as unannotated and go to tier 3 instead — unless the user confirms those clusters are their annotation, in which case pass the column explicitly. |
| `TOO_FEW_CELL_TYPES`, `CELL_TYPE_BELOW_MIN` | Curation left < 2 types — usually `min_cells_per_type` is too high for a small reference. | Offer the lowered threshold **and** a different, richer reference; let the user choose. |
| `NO_LABELED_CELLS` | The column exists but holds no labels. | Another column from the list, or tier 3. |

**Tier 2 — the dataset may be right, the *file* was wrong. Look for another distribution of the same dataset first.**

| `error code:` | What it means | What to offer |
|---|---|---|
| `NO_RAW_COUNTS` | Every matrix in the file holds scaled or normalized values — detected in preflight, before the read. `reference facts:` names each matrix and its value range. Typical of figure/analysis objects (`Fig1_*`, `*_processed`, an HVG subset of a few thousand genes). | The **same dataset's raw-counts distribution**: the download labelled "raw counts"/"DGE"/"UMI counts", a GEO supplementary count matrix, or an object with `layers['counts']`/`.raw`. Never a parameter change. |
| `NON_INTEGER_COUNTS` | The R-stage backstop for the same thing, reached mainly on the `.rds` path. Reports the full value range and whether it is scaled or normalized. | Same as above. |
| `SEURAT_COUNTS_MISSING`, `RDS_UNSUPPORTED_CLASS`, `RDS_UNREADABLE`, `H5AD_UNREADABLE` | Wrong container: a Seurat v5 `.rds` SeuratObject 4.1.4 cannot deserialize, an object with no counts slot, a corrupt file. | The same dataset as `.h5ad` rather than `.rds`, or another export of it. |
| `DOWNLOAD_HTTP_ERROR`, `DOWNLOAD_FAILED`, `DOWNLOAD_NOT_A_REFERENCE`, `H5AD_NOT_HDF5` | The URL didn't yield the data file — expired signed link, a landing page, an auth wall. | A fresh direct link to the *same* dataset; failing that, ask the user to download it to LData and attach it. |

Before relaunching on a tier-2 find, check the builder can actually ingest it: it takes **one**
`.h5ad` or `.rds`. A tar of per-tissue text files, or a matrix plus a separate annotation CSV, is not
ingestible — that means tier 2 is exhausted, so go to tier 3.

**Tier 3 — a different dataset.**

| `error code:` | What it means | What to offer |
|---|---|---|
| `REFERENCE_TOO_LARGE`, `OOM_KILLED`, `OUT_OF_MEMORY` | The reference does not fit in the task's memory. | **A smaller reference.** Not a parameter fix: `max_cells_per_type` caps cells *after* the whole file is read, so it cannot rescue a file too big to load. |
| *(tier 2 exhausted)* | The source has no distribution the builder can use. | Search again per `steps/rctd.md` **1b**, with the constraint the failure taught you stated in the message. |

**Tier 4 — a builder bug. Do not go searching for a new reference.**

| `error code:` | What it means | What to offer |
|---|---|---|
| `STAGE_SIGNALED`, `UNHANDLED`, `UNHANDLED_R_ERROR`, `MISSING_*`, `ROUND_TRIP_FAILED`, `SHAPE_MISMATCH`, `BARCODE_CELLTYPE_MISMATCH` | A builder bug, not a bad choice by the user. | Say so plainly, offer a different reference as a workaround, and tell them the execution log is worth sending to support. |

4. **Search first, then present — don't ask into a void.** Finding a replacement is the recovery the
   user cannot start themselves; they do not know which atlases you can search. So for tiers 2 and 3,
   do the search *before* you write the message (`steps/rctd.md` **1b**, with the constraint the
   failure taught you), and put the candidates in the message alongside the explanation. The user's
   answer is then a choice, not a yes/no that costs a whole extra turn:

   > The mouse embryo reference I picked (CELLxGENE, ~1.4M cells) ran out of memory while loading —
   > it's too large for the builder. I found three under ~300k cells covering E9.5–E13.5: … Which
   > should I rebuild with? I can also use one you supply instead.

   The confirmation still gates the pivot — changing datasets is the user's call — and for a size
   failure prefer per-tissue or per-stage subsets, stating each candidate's cell count so they can
   see it is smaller. Then relaunch: fix the parameters in **cell 1**, then re-run cell 2.
5. **Never repeat a failure, and cap the loop.** Keep a running list of what has been tried (source,
   file, failure code), state it when presenting replacements, and never re-offer anything on it.
   **After two failed builds, stop searching** — summarize everything tried and hand the choice back
   to the user rather than burning a third wait on a third guess.
6. **Use a new `run_name` for the retry** (e.g. `<run>_v2`) when the source changed. The failed run's
   directory already holds `<run_name>_reference_FAILED.txt`; a fresh name keeps the failed and the
   good attempt distinguishable, and gives the launch guard a genuinely new fingerprint. A pure
   parameter fix (`cell_type_column`) can keep the same `run_name` — the changed parameter is enough
   for the guard to treat it as a new run.
7. **Never move on to `wf/rctd_wf.md` after a failed build.** There is no `.rds` to pass. And never
   end the turn on a failure without both the explanation and the question — a failure the user has
   to notice by themselves is the same stall as an unattended picker.

If the user declines a new reference, say that RCTD needs one to run, note that the rest of the
analysis is unaffected, and continue at `steps/normalization.md` per the skip path in
`steps/rctd.md`.
</failure_recovery>

