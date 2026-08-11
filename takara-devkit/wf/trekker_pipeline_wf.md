<goal>
Turn reads (FastQs) into counts
</goal>

<pre_pipeline_questions>
Before collecting any pipeline parameters, ask the user the following questions **in order**:

1. **Which single-cell platform was used?**
   Present the full `sc_platform` table from the parameters section below and ask the user to identify their platform.
   - If the selected platform is **TrekkerFX_FLEX** or **TrekkerQ_P**: run the corresponding preprocessing (partitioning) workflow first (see the platform-specific notes in the parameters section), then return here to continue with questions 2 and 3.
   - All other platforms (including **TrekkerU_PIP**, whose PIPSeeker conversion is now built into the Trekker pipeline): proceed directly to question 2 and 3.

2. **Multiple reactions?**
   > "Was the experiment for this Trekker tile split into multiple single-nuclei reactions (i.e. processed with different sample indices during sequencing)?"
   - If **yes**: ask the user whether all reactions share the **same tile ID** or span **multiple tile IDs**.
     - **Same tile ID**: recommend to launch all Trekker pipeline executions in parallel (one per reaction), then — once every reaction's outputs are present in Latch Data (see `<resuming>`) — run a **single** `wf/trekker_merger_wf.md` to merge all outputs.
     - **Multiple tile IDs**: recommend to launch all Trekker pipeline executions in parallel, then — once their outputs are present — run a **separate** `wf/trekker_merger_wf.md` for **each tile ID group** — only merge outputs that share the same tile ID. Inform the user that they will need one merged sample ID and output directory per tile group.
   - Inform the user now so they can plan sample IDs, tile IDs, and output directories for each reaction.

3. **Multiple lanes / multiple FASTQ files?**
   > "Do you have multiple R1 (or R2) FASTQ files for this sample — for example, from sequencing the same reaction across multiple lanes?"
   - If **yes**: concatenate R1 files into one file and R2 files into one file using `wf/fastq_concatenator_wf.md` **before** proceeding. Use the merged FASTQs as inputs.

Only proceed to collect the remaining Trekker pipeline parameters after all three questions are resolved and any required preprocessing or concatenation is complete.
</pre_pipeline_questions>

<parameters>
- Every Trekker sample has **two FASTQ files** (paired-end sequencing).
  - **Read 1** → maps to workflow param `fastq_cb`
  - **Read 2** → maps to workflow param `fastq_tags`
  These must be provided by the user and wrapped as `LatchFile(latch://...)`.
- **Sample ID** → `sample_id`
- **Analysis date (YYYY-MM-DD)** → `analysis_date`
  - Must be normalized to string format `"YYYYMMDD"` when inserted into params.
- **Tile ID** → `tile_id`
- **Single-cell platform** → `sc_platform`
  - This should already be known from the pre-pipeline questions. Map the user's platform to the correct string below.
  - Two platforms require a partitioning (preprocessing) workflow before Trekker can run — these are called out first:

    **Platforms requiring preprocessing (must be run before Trekker):**

    | String value | Platform | Preprocessing workflow |
    |---|---|---|
    | `"TrekkerFX_FLEX"` | 10x Chromium GEM-X Flex (v1 and v2 APEX) | `wf/trekker_fxflex_demux_wf.md` |
    | `"TrekkerQ_P"` | Parse Evercode WT v3 | `wf/trekker_qp_demux_wf.md` |

    > **Note:** As of Trekker v1.4.11, `TrekkerU_PIP` (PIPSeeker) no longer needs a separate preprocessing workflow — the PIPSeeker-to-Trekker conversion is performed inside the Trekker pipeline. Select `TrekkerU_PIP` and provide the standard inputs directly.

    **All platforms:**

    *10x Chromium*

    | String value | Platform |
    |---|---|
    | `"TrekkerU_C"` | 10x Chromium Next GEM 3'v3.1 |
    | `"TrekkerU_CX"` | 10x Chromium GEM-X 3'v4 |
    | `"Trekker5C_CX"` | 10x Chromium, 5' |
    | `"TrekkerFX_FLEX"` | 10x Chromium GEM-X Flex, v1 and v2 APEX ⚠️ |
    | `"TrekkerU_M"` | 10x Chromium Multiome ATAC + Gene Expression |

    *BD Rhapsody*

    | String value | Platform |
    |---|---|
    | `"TrekkerU_R"` | BD Rhapsody WTA |
    | `"TrekkerU_RVDJ"` | BD Rhapsody TCR/BCR Next + mRNA WTA |
    | `"TrekkerU_RATAC"` | BD Rhapsody ATAC-Seq + mRNA WTA |

    *Illumina*

    | String value | Platform |
    |---|---|
    | `"TrekkerU_IL"` | Illumina Single Cell 3' RNA Prep (DRAGEN) |
    | `"TrekkerU_PIP"` | Illumina Single Cell 3' RNA Prep (PIPSeeker) |

    *Parse*

    | String value | Platform |
    |---|---|
    | `"TrekkerQ_P"` | Parse Evercode WT v3 ⚠️ |

- **Input directory** (directory on Latch Data that stores the output of the single-cell platform used during the Trekker experiment) → `sc_outdir` (`LatchDir`)
- **Output directory** (where to save Trekker workflow results) → `output_dir` (`LatchDir`)

**Platforms requiring preprocessing — run the relevant workflow first, then use its outputs as Trekker inputs:**

- **`TrekkerFX_FLEX`** → follow `wf/trekker_fxflex_demux_wf.md` before running Trekker.
  - The preprocessing workflow demultiplexes the pooled FASTQs into per-sample pairs. It supports both FLEX v1 and FLEX v2 (APEX) chemistries — **ask the user which FLEX version they used**. Sample labeling is optional: the user may enter sample names and barcodes manually, supply a manifest file, or skip labeling (outputs are then named by barcode ID). See that workflow's doc.
  - Use each output `_R1.fastq.gz` as `fastq_cb` and `_R2.fastq.gz` as `fastq_tags` for Trekker.
  - The Trekker pipeline auto-detects the FLEX barcode version, so v1 and v2 demultiplexed outputs are launched the same way here.
  - Run a separate Trekker execution for each demultiplexed sample.

- **`TrekkerU_PIP`** → **no preprocessing workflow required.** As of Trekker v1.4.11 the PIPSeeker-to-Trekker conversion runs inside the pipeline. Select `TrekkerU_PIP` as `sc_platform` and provide the standard inputs directly: the R1 FASTQ as `fastq_cb`, the R2 FASTQ as `fastq_tags`, and the PIPseeker single-cell output directory (`barcodes.tsv.gz`, `features.tsv.gz`, `matrix.mtx.gz`) as `sc_outdir`.

- **`TrekkerQ_P`** → follow `wf/trekker_qp_demux_wf.md` before running Trekker.
  - The preprocessing workflow demultiplexes the pooled FASTQs into per-group pairs.
  - Use each output `_R1.fastq.gz` as `fastq_cb` and `_R2.fastq.gz` as `fastq_tags` for Trekker.
  - Run a separate Trekker execution for each demultiplexed group.

**Platform-specific additional inputs — prompt the user only if the selected platform requires them:**

- **`TrekkerU_RVDJ` only** → `scmulti_file` (`LatchFile`, **required**)
  - A Seurat `.rds` file produced by the BD Rhapsody TCR/BCR Next pipeline.
  - Must be provided by the user — do not proceed without it.

- **`TrekkerU_RATAC` only** → `scmulti_dir` (`LatchDir`, **required**)
  - A directory containing exactly these three files:
    - `atac-barcodes.tsv.gz`
    - `atac-features.tsv.gz`
    - `atac-matrix.mtx.gz`
  - Must be provided by the user — do not proceed without it.

- **`subsample_update`** (`str`, optional, all platforms)
  - This optional parameter should not be modified unless the user indicates their sample has more than 5 million nuclei.
  - If nuclei count **exceeds 5 million**: recommend setting this to `"yes"` and add it to params.
  - If nuclei count is **5 million or fewer**, do nothing (Trekker will automatically default to `"no"` if not input is provided).
</parameters>

<outputs>
Verified against the deployment source (`latch_platform/curiotrekker`), not inferred. The task returns
`LatchOutputDir(out_dir, f"{output_dir.remote_path}/{analysis_date}_{sample_id}")`
(`wf/trekker_wf.py:184`), and the pipeline script builds the tree below it
(`wf/nuclei_locater_docker.sh:62-66`):

```
<output_dir>/
└── <analysis_date>_<sample_id>/          # analysis_date is the YYYYMMDD form passed in params
    ├── log/
    └── trekker_<sample_id>/
        ├── output/                       # ← the results you want
        │   ├── <sample_id>_Trekker_Report.html     # the QC report
        │   ├── <sample_id>_summary_metrics.csv
        │   ├── <sample_id>_variable_features_clusters.csv
        │   ├── <sample_id>_variable_features_spatial_moransi.txt
        │   ├── <sample_id>_ConfPositioned_seurat_spatial.rds
        │   └── intermediates/
        └── misc/<tile_id>/
```

**Report filename.** `genreport.R:22-27` emits `<sample_id>_Trekker_Report.html` for the standard
report and `<sample_id>_Report.html` for the extended one — so match on the `_Report.html` **suffix**
rather than an exact name, and prefer the `_Trekker_` variant.

Two things here are easy to get wrong and have already caused a failed run: the
`<analysis_date>_<sample_id>` directory sits between `output_dir` and everything else, and the report
is two levels below that. Search from `output_dir` rather than constructing a path.
</outputs>

<instructions>
Once the pre-pipeline questions are resolved, **immediately generate and run both cells below** — the
parameter widget cell and the launch cell. Do **not** wait for the user to confirm in chat before
generating the launch cell, and do not ask them to tell you when to launch. The user launches the
pipeline by clicking the button that the launch cell renders.

Rules for the launch cell:

- Call `launch_workflow_once(...)` — never `w_workflow` directly — **unconditionally at the top
  level of the cell.** Never place it inside an `if`, a `try`, or a loop body that can be skipped,
  and never withhold it because the widget values still look empty. An unrendered launch call is a
  missing launch button — that is the failure mode this pattern exists to prevent. The helper guards
  against launching a run that is already in flight, and skips that check entirely while
  `readonly=True`, so it costs nothing on the reactive re-runs this cell does on every keystroke.
  See "Launching a workflow at most once" in `SKILL.md`.
- Pass `automatic=False` so the workflow launches on click instead of firing the moment the cell
  runs. **This deliberately overrides the `automatic=True` default in `latch-workflows/SKILL.md`**,
  which assumes params are hard-coded rather than entered through widgets. For the Trekker and
  Seeker pipelines, `automatic=False` is correct.
- Gate only the button's *enabled state* with `readonly=not params_ready`, never the call itself.
- Collect the file and directory parameters with `w_ldata_picker` (`file_type="file"` / `"dir"`).
  Its `.value` is an `LPath` or `None` — build `LatchFile` / `LatchDir` conditionally from
  `.value.path` (see the example). Calling `.path` on `None`, or `LatchFile("")`, raises and kills
  the cell before the launch call is reached, which removes the button.
- **The output directory is a picker like any other, and never a guess.** If the user named an output
  directory earlier in this session, pass it as `w_output_dir`'s `default=` and say so in chat; if
  they did not, leave `default` unset rather than filling in a plausible path. With multiple
  reactions, each gets its own picker (and its own key) — reactions may share a directory, but that
  is the user's call to make, not yours. See "Asking for an output directory" in `SKILL.md`.
- Include the `w_text_output(...)` long-running notice inside `if execution is not None:`. The click
  lands after your turn ends, so a chat message you would "display after launching" never happens —
  the cell has to render it. See `<long_running_guidance>`.
- **Never call `await execution.wait()` (or `await asyncio.gather(...)`) in the launch cell.** The
  Trekker pipeline runs for hours, and the notice explicitly invites the user to shut the notebook pod
  down while it runs. An `await` parks the cell in a permanently-running state, binds no result, and
  survives no pod restart — it is the reason the agent gets stuck reporting "still running" after the
  pipeline has finished. With multiple reactions a `gather` is worse still: it blocks on the slowest
  reaction, so no reaction's results become available until every one of them is done.
- **Generate all three cells in the same turn**, including the resume cell (cell 3). Nothing in Plots
  can start an agent turn, so when the pipeline finishes hours later there is no way for you to be
  running. The resume button is what the user clicks instead; if it is not already on screen when
  they leave, their only recourse is to interrupt you and type "continue", which is exactly the
  confusing flow this pattern exists to remove. See `<resuming>`.

- **Name the tab when you hand off.** These cells render in a **new tab** that the notebook does not
  switch to, and every one of them needs a click. A launch button the user never finds is the same as
  no launch button, and the resume button is worse — they come back hours later, see nothing, and
  conclude the run was lost. With multiple reactions, say which tab holds which reaction's buttons.
  See "Telling the user where results appeared" in `SKILL.md`.

After all three cells render, tell the user:
> "The parameter form and the **Launch Trekker workflow** button are in a **new tab** in this
> notebook — click that tab, fill in the fields, then click Launch. When the pipeline finishes —
> however long that takes, and even if you shut the pod down in between — come back to that same tab
> and click **Show my QC report**; the report link appears right there. You don't need to message me
> for that step."

The cell re-runs reactively as widget values change, so the button enables on its own once every
required field is set.
</instructions>

<example>
Single reaction — **cell 1, parameter entry widgets:**
```python
from lplots.widgets.text import w_text_input
from lplots.widgets.select import w_select
from lplots.widgets.ldata import w_ldata_picker

w_sample_id = w_text_input(label="Sample ID", key="trekker_sample_id")
w_analysis_date = w_text_input(
    label="Analysis date", key="trekker_analysis_date",
    appearance={"placeholder": "YYYY-MM-DD"},
)
w_tile_id = w_text_input(label="Tile ID", key="trekker_tile_id")
w_sc_platform = w_select(
    label="Single-cell platform",
    options=[
        "TrekkerU_C", "TrekkerU_CX", "Trekker5C_CX", "TrekkerFX_FLEX", "TrekkerU_M",
        "TrekkerU_R", "TrekkerU_RVDJ", "TrekkerU_RATAC",
        "TrekkerU_IL", "TrekkerU_PIP", "TrekkerQ_P",
    ],
    key="trekker_sc_platform",
)
w_fastq_cb = w_ldata_picker(
    label="Read 1 FASTQ (fastq_cb)", file_type="file", key="trekker_fastq_cb",
)
w_fastq_tags = w_ldata_picker(
    label="Read 2 FASTQ (fastq_tags)", file_type="file", key="trekker_fastq_tags",
)
w_sc_outdir = w_ldata_picker(
    label="Single-cell platform output directory (sc_outdir)", file_type="dir",
    key="trekker_sc_outdir",
)
# add default="latch://..." only when the user has already chosen an output directory this session
w_output_dir = w_ldata_picker(
    label="Output directory", file_type="dir", key="trekker_output_dir",
)
```

The user may select the FASTQs in the pickers or attach them with the attach button — if they
attach, set the picker's `default` to the attached `latch://` path so the cell stays in sync.

**Cell 2, launch:**
```python
# resolve takara/lib per SKILL.md "Helper library usage", then:
from takara.launch import LaunchStatus, launch_workflow_once
from lplots.widgets.text import w_text_output
from latch.types import LatchFile, LatchDir

sample_id_v = w_sample_id.value or ""
analysis_date_v = w_analysis_date.value or ""
tile_id_v = w_tile_id.value or ""
sc_platform_v = w_sc_platform.value or ""

# picker values are LPath or None — never call .path on None
fastq_cb_v = w_fastq_cb.value
fastq_tags_v = w_fastq_tags.value
sc_outdir_v = w_sc_outdir.value
output_dir_v = w_output_dir.value

params_ready = (
    all([sample_id_v, analysis_date_v, tile_id_v, sc_platform_v])
    and all(v is not None for v in (fastq_cb_v, fastq_tags_v, sc_outdir_v, output_dir_v))
)

params = {
    "sample_id": sample_id_v,
    "analysis_date": analysis_date_v.replace("-", ""),      # normalized to "YYYYMMDD"
    "tile_id": tile_id_v,
    "fastq_cb": LatchFile(fastq_cb_v.path) if fastq_cb_v is not None else None,
    "fastq_tags": LatchFile(fastq_tags_v.path) if fastq_tags_v is not None else None,
    "sc_outdir": LatchDir(sc_outdir_v.path) if sc_outdir_v is not None else None,
    "sc_platform": sc_platform_v,
    "output_dir": LatchDir(output_dir_v.path) if output_dir_v is not None else None,
}

# ALWAYS called — never inside a conditional, or the launch button will not render
res = launch_workflow_once(
    wf_name="wf.__init__.trekker_pipeline_wf",
    version="1.4.11-909971",
    params=params,
    label="Launch Trekker workflow",
    key_prefix="trekker_workflow",  # key is derived from params — do NOT pass a hand-written key
    run_name=f"{params['analysis_date']}_{params['sample_id']}",   # the run dir Trekker writes
    output_dir=params["output_dir"],
    automatic=False,                # user clicks the button to launch
    readonly=not params_ready,      # button disabled until every field is set
)
execution = res.execution

if execution is not None:
    # The long-running notice MUST be rendered here, by the cell itself. The click happens
    # after the agent's turn has ended, so the agent is not running and cannot post it to chat.
    w_text_output(
        content=(
            "The Trekker pipeline is now running on Latch compute and will take some time to "
            "finish. It runs independently of this notebook, so you may **shut down the "
            "notebook pod while the workflow runs, which stops the notebook compute charges "
            "and saves cost**. Shutting the pod down will "
            "not interrupt the workflow. You may monitor the progress of the workflow in the "
            "workflows executions tab. When the workflow has completed, restart the pod, reopen "
            "the notebook, and click **Show my QC report** below — that is all you need to do, "
            "and you do not have to message the agent for it."
        ),
        appearance={"message_box": "info"},
        key="trekker_long_running_notice",
    )

# The cell ENDS here. Do not `await execution.wait()` — see <resuming>.
```

**Cell 3, resume** — generate and run this in the same turn as cells 1 and 2, so the button is on
screen before the user walks away. Clicking it re-runs *this cell in the kernel*; no agent turn is
involved, which is what makes the whole post-pipeline step work without the user having to message
the agent. It reads Latch Data rather than kernel state, so it also survives a pod restart:
```python
from pathlib import Path

from latch.ldata.path import LPath
from lplots.widgets.button import w_button
from lplots.widgets.text import w_text_output

resume = w_button(label="Show my QC report", key="trekker_resume")

# Re-derived from the widgets, not from the launch cell's variables. Picker values are LPath or
# None, and after a pod restart the parameter cell may not have been re-run at all — so never call
# .path unguarded (same rule as the launch cell).
try:
    out_root = LPath(w_output_dir.value.path.rstrip("/"))
    sample_v = w_sample_id.value or ""
    date_v = (w_analysis_date.value or "").replace("-", "")      # params use YYYYMMDD
except (AttributeError, NameError):
    out_root, sample_v, date_v = None, "", ""

# reading .value makes this cell reactive — the click re-runs it
if resume.value and out_root is None:
    w_text_output(
        content=(
            "I don't have the output directory for this run. Re-run the parameter cell above, set "
            "**Output directory**, **Sample ID** and **Analysis date**, then click this button again."
        ),
        appearance={"message_box": "warning"},
        key="trekker_resume_no_params",
    )
elif resume.value:

    def _reports(root: LPath, depth: int) -> list[LPath]:
        """Every *_Report.html at or below root. Bounded; tolerates files and missing dirs."""
        found: list[LPath] = []
        try:
            entries = list(root.iterdir())
        except Exception:          # not a directory, or not created yet
            return found
        for p in entries:
            name = p.path.rsplit("/", 1)[-1]
            if name.endswith("_Report.html"):
                found.append(p)
            elif depth > 1:
                found.extend(_reports(p, depth - 1))
        return found

    # Fast path: the layout the deployed workflow actually writes (see <outputs>). Falls back to a
    # bounded search from output_dir, so a layout change costs speed, not correctness.
    known = LPath(f"{out_root.path}/{date_v}_{sample_v}/trekker_{sample_v}/output")
    hits = _reports(known, 1) or _reports(out_root, 6)

    # Prefer this sample's report, and the standard "_Trekker_Report.html" over the extended one.
    # Rank on the FILENAME, not the full path — the run directory itself usually contains the
    # sample id, so matching on the path makes every candidate tie.
    def _rank(p: LPath) -> tuple[bool, bool]:
        name = p.path.rsplit("/", 1)[-1]
        return (not name.startswith(f"{sample_v}_"), "_Trekker_Report.html" not in name)

    hits.sort(key=_rank)
    report = hits[0] if hits else None

    if report is None:
        w_text_output(
            content=(
                f"No `*_Report.html` found under `{out_root.path}`, so the pipeline has not "
                "finished writing its outputs. Check the execution's status in the workflows "
                "executions tab; if it is still running, click this button again once it reaches "
                "SUCCEEDED. If it shows FAILED, tell me and I'll look at the logs."
            ),
            appearance={"message_box": "warning"},
            key="trekker_resume_pending",
        )
    else:
        # Image optimization is a nice-to-have; the link is the deliverable. If the helper library
        # cannot be imported, link the original report rather than failing the whole cell.
        link, note = report, ""
        optimize, why = _load_takara_optimize()

        if optimize is None:
            note = f"\n\n_Images were not optimized ({why}), so the report may load slowly._"
        else:
            try:
                report_dir = report.path.rsplit("/", 1)[0]
                optimize(src=report, ldata_dst_dir=report_dir)
                link = LPath(report_dir) / (Path(report.path).stem + ".optimized.html")
            except Exception as e:
                note = f"\n\n_Images were not optimized ({e!r}), so the report may load slowly._"

        w_text_output(
            content=(
                "**Trekker pipeline complete.** "
                f"[Open the QC report](https://console.latch.bio/data/{link.node_id()})\n\n"
                "Message me when you've looked it over and we'll continue with secondary analysis."
                + note
            ),
            appearance={"message_box": "success"},
            key="trekker_resume_report",
        )
```

`_load_takara_optimize()` is the shared helper defined in `<takara_lib_import>` at the end of this
doc — paste it into the cell above the button. Four notes:

- **A failed import must never cost the user their report link.** `optimize` only shrinks embedded
  images; if it is unavailable the original report still opens. That is why the import is resolved
  through a helper that returns `None` instead of raising.
- The helper locates the library by **verifying `optimize_html_images.py` exists** before putting a
  directory on `sys.path`, rather than trusting a hard-coded path. A `ModuleNotFoundError: No module
  named 'takara.optimize_html_images'` means a *different* `takara` package won the import — the
  helper's purge plus `importlib.invalidate_caches()` is what prevents that.
- **Never construct the report path from a guess.** The `<outputs>` section below records the layout
  the deployed workflow actually writes; the fast path uses it and the bounded search is the safety
  net. Matching an exact filename you assembled yourself is what produced
  "No `continue_3_Report.html` under .../continue_3/continue_3" — two wrong guesses at once.
- If `iterdir()` is unavailable in the runtime, replace `_reports` with `w_ldata_browser(dir=out_root)`
  and have the user select the report; everything downstream is unchanged.

**Multiple reactions:** render **one resume button per reaction**, each with its own
`key=f"trekker_resume_{i}"`, label `f"Show my QC report — reaction {i}"`, and that reaction's own
`output_dir` / `sample_id`. Reactions finish at different times, so each must be independently
clickable — never one button that waits for all of them.

Multiple reactions (one button per reaction, each launching independently). Build one set of parameter
entry widgets per reaction in cell 1 — same widgets as above, with `key` suffixed by the
reaction number — then in cell 2:
```python
# resolve takara/lib per SKILL.md "Helper library usage", then:
from takara.launch import LaunchStatus, launch_workflow_once
from lplots.widgets.text import w_text_output
from latch.types import LatchFile, LatchDir

# one dict per reaction, each built from that reaction's widgets as in the single-reaction example
all_params = [
    {
        "sample_id": w_sample_id_1.value or "",
        "analysis_date": (w_analysis_date_1.value or "").replace("-", ""),
        "tile_id": w_tile_id_1.value or "",
        "fastq_cb": LatchFile(w_fastq_cb_1.value.path) if w_fastq_cb_1.value is not None else None,
        "fastq_tags": LatchFile(w_fastq_tags_1.value.path) if w_fastq_tags_1.value is not None else None,
        "sc_outdir": LatchDir(w_sc_outdir_1.value.path) if w_sc_outdir_1.value is not None else None,
        "sc_platform": w_sc_platform_1.value or "",
        "output_dir": LatchDir(w_output_dir_1.value.path) if w_output_dir_1.value is not None else None,
    },
    # add one entry per reaction
]

executions = []
for i, params in enumerate(all_params, start=1):
    ready_i = all(v not in (None, "") for v in params.values())

    # ALWAYS called for every reaction — one button each. Each reaction's params differ, so the
    # derived keys differ too; do not add `i` to key_prefix to force that.
    res_i = launch_workflow_once(
        wf_name="wf.__init__.trekker_pipeline_wf",
        version="1.4.11-909971",
        params=params,
        label=f"Launch Trekker workflow — reaction {i}",
        key_prefix="trekker_workflow",
        run_name=f"{params['analysis_date']}_{params['sample_id']}",
        output_dir=params["output_dir"],
        automatic=False,
        readonly=not ready_i,
    )
    if res_i.execution is not None:
        executions.append(res_i.execution)

        # one notice per launched reaction — rendered by the cell, not by the agent
        w_text_output(
            content=(
                f"Reaction {i}: the Trekker pipeline is now running on Latch compute and will "
                "take some time to finish. It runs independently of this notebook, so you may "
                "**shut down the notebook pod while the workflow runs, which stops the notebook "
                "compute charges and saves cost**. "
                "Shutting the pod down will not interrupt the workflow. You may monitor the "
                "progress of the workflow in the workflows executions tab. When the workflow "
                f"has completed, restart the pod, reopen the notebook, and click **Show my QC "
                f"report — reaction {i}** below. You do not have to message the agent for it."
            ),
            appearance={"message_box": "info"},
            key=f"trekker_long_running_notice_{i}",
        )

# The cell ENDS here. No `await asyncio.gather(...)` — reactions finish at different times, and
# blocking on all of them is what strands the notebook. Use one results cell per reaction instead,
# keyed by that reaction's own output directory.
```
</example>

<long_running_guidance>
Because `automatic=False`, the user clicks **Launch** after your turn has ended. You are not
running at that moment and cannot post anything to chat, so this message has to be delivered in
**two** places — do both, and never shorten it or drop the pod shutdown advice:

1. **In the launch cell**, as the `w_text_output(...)` inside `if execution is not None:` shown in
   the example above. This is what the user actually sees on click, and it is the only delivery
   that survives the agent's turn ending. Nothing may follow it in the cell that blocks — an
   `await execution.wait()` would withhold everything after it until the pipeline finishes.
2. **In chat, when you present the two cells**, phrased for what is about to happen: tell the user
   that once they click Launch the pipeline runs on Latch compute, and that they may then shut the
   notebook pod down to save cost. In this version, **name the tab** rather than saying "below" —
   the cells are in a tab the notebook did not switch to, so from chat the buttons are not below
   anything. The in-cell version at (1) may keep "below", since it sits next to the button.

The message text:

"The Trekker pipeline is now running on Latch compute and will take some time to finish. It runs independently of this notebook, so you may **shut down the notebook pod while the workflow runs, which stops the notebook compute charges and saves cost**. Shutting the pod down will not interrupt the workflow. You may monitor the progress of the workflow in the workflows executions tab. When the workflow has completed, restart the pod, reopen the notebook, and click **Show my QC report** below — that is all you need to do, and you do not have to message the agent for it."

Never tell the user that you will "resume from where you left off" or that you will pick the run up
automatically. Nothing in Plots can start an agent turn, so that is not true, and it is what leads
users to sit waiting and then interrupt you. Point them at the resume button instead.
</long_running_guidance>

<resuming>
The launch cell does not wait for the pipeline, and you will not be running when it finishes. **The
resume button in cell 3 is the intended path** — it does the whole report step in the kernel without
you. Make sure it is on screen before the user leaves, one per reaction.

If the user does message you after a launch — "continue", "is it done?", "the pipeline finished", or
anything else — treat that as a resume signal and check Latch Data *before* answering:

- **The notebook is not the source of truth for whether the pipeline finished.** The execution runs
  on Latch compute, entirely outside this pod. Never report "the pipeline is still running" because
  a cell looks busy, because `workflow_outputs` is undefined, or because you have no record of a
  completion — none of those are evidence about the execution.
- **Look under the run's `output_dir`.** Outputs there mean the pipeline finished; an empty or
  missing directory means it is still running or failed, and the user should check the workflows
  executions tab.
- **If kernel state was lost** (pod restarted), do not try to reconstruct `execution` or `res` — they
  are gone and are not needed. Re-run cells 1 and 3; the widget values persist with their `key`s, and
  everything downstream is derived from the Latch Data paths. Re-rendering cell 3 also puts the
  resume buttons back on screen.
- **With multiple reactions**, check each reaction's output directory independently and proceed with
  whichever have finished. One slow reaction must not hold up the others.
- If the report link has not been rendered yet, do that work yourself rather than telling the user to
  click the button they just bypassed — same steps as cell 3, then continue to
  `steps/view_report.md`'s follow-up question. Do not ask the user to re-confirm that the pipeline
  finished.
</resuming>

<takara_lib_import>
Paste this helper into the resume cell, above the button. It resolves the Takara helper library
robustly and **never raises** — a missing library must cost the user image optimization, not their
report link.

```python
import importlib
import sys
from pathlib import Path

# Checked first, in order. If the skill is deployed somewhere else, add that path here.
_TAKARA_HINTS = (
    "/opt/latch/plots-faas/.claude/skills/takara-devkit/lib",
    "/opt/latch/plots-faas/.claude/skills/latch-skills/takara-devkit/lib",
)
# Searched only if no hint matches. Most specific first — an rglob over a large tree is slow.
# `agent_config/context/technology_docs` is deliberately absent: it holds a frozen pre-monorepo
# snapshot of this devkit (see <legacy_technology_docs_path> in SKILL.md) that imports cleanly
# and runs months-old code. It has no optimize_html_images.py, so it would miss anyway — but do
# not add it back as a convenience for other imports.
_TAKARA_SEARCH_ROOTS = (
    "/opt/latch/plots-faas/.claude/skills",
    "/opt/latch/plots-faas",
    "/root",
)


def _find_takara_lib() -> str | None:
    """Directory to place on sys.path so `takara.optimize_html_images` resolves, or None."""
    for hint in _TAKARA_HINTS:
        if (Path(hint) / "takara" / "optimize_html_images.py").is_file():
            return hint
    for root in _TAKARA_SEARCH_ROOTS:
        try:
            hit = next(Path(root).rglob("takara/optimize_html_images.py"), None)
        except Exception:          # unreadable tree
            hit = None
        if hit is not None:
            return str(hit.parent.parent)
    return None


def _load_takara_optimize():
    """Returns (optimize, None) on success or (None, reason) on failure. Never raises."""
    lib = _find_takara_lib()
    if lib is None:
        return None, (
            "takara/optimize_html_images.py was not found under "
            + ", ".join(_TAKARA_SEARCH_ROOTS)
        )

    # Whichever `takara` is imported first pins its __path__ for the rest of the session, so a bare
    # sys.path.insert does nothing: the cached package wins and its submodules are the only ones
    # visible. That is what produces "No module named 'takara.optimize_html_images'" even though
    # `takara` itself imports fine. Drop the cached package AND refresh the path finders.
    for name in [m for m in sys.modules if m == "takara" or m.startswith("takara.")]:
        del sys.modules[name]
    while lib in sys.path:
        sys.path.remove(lib)
    sys.path.insert(0, lib)
    importlib.invalidate_caches()

    try:
        from takara.optimize_html_images import optimize
    except Exception as e:                     # deployed copy missing the module, PIL absent, ...
        return None, f"{e!r} (searched {lib})"

    return optimize, None
```

Two rules this encodes, which apply anywhere in this skill that imports `takara`:

- **Verify before trusting a path.** Check that `optimize_html_images.py` actually exists at a
  location before putting it on `sys.path`. A hard-coded path that is wrong in the deployed
  environment fails silently — `sys.path.insert` of a non-existent directory is a no-op — and the
  import then resolves against some other `takara`.
- **Purge `sys.modules` *and* call `importlib.invalidate_caches()`.** The purge handles a package
  already bound to a different path; `invalidate_caches()` handles the import system's cached
  directory listings, which otherwise keep a newly-added path's contents invisible.
</takara_lib_import>
