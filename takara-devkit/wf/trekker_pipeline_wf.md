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
     - **Same tile ID**: recommend to launch all Trekker pipeline executions in parallel (one per reaction) and await them all together, then run a **single** `wf/trekker_merger_wf.md` to merge all outputs.
     - **Multiple tile IDs**: recommend to launch all Trekker pipeline executions in parallel and await them together, then run a **separate** `wf/trekker_merger_wf.md` for **each tile ID group** — only merge outputs that share the same tile ID. Inform the user that they will need one merged sample ID and output directory per tile group.
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
</outputs>

<instructions>
Once the pre-pipeline questions are resolved, **immediately generate and run both cells below** — the
parameter widget cell and the launch cell. Do **not** wait for the user to confirm in chat before
generating the launch cell, and do not ask them to tell you when to launch. The user launches the
pipeline by clicking the button that the launch cell renders.

Rules for the launch cell:

- Call `w_workflow(...)` **unconditionally at the top level of the cell.** Never place it inside an
  `if`, a `try`, or a loop body that can be skipped, and never withhold it because the widget values
  still look empty. An unrendered `w_workflow` is a missing launch button — that is the failure mode
  this pattern exists to prevent.
- Pass `automatic=False` so the workflow launches on click instead of firing the moment the cell
  runs. **This deliberately overrides the `automatic=True` default in `latch-workflows/SKILL.md`**,
  which assumes params are hard-coded rather than entered through widgets. For the Trekker and
  Seeker pipelines, `automatic=False` is correct.
- Gate only the button's *enabled state* with `readonly=not params_ready`, never the call itself.
- Collect the file and directory parameters with `w_ldata_picker` (`file_type="file"` / `"dir"`).
  Its `.value` is an `LPath` or `None` — build `LatchFile` / `LatchDir` conditionally from
  `.value.path` (see the example). Calling `.path` on `None`, or `LatchFile("")`, raises and kills
  the cell before `w_workflow` is reached, which removes the button.

After both cells render, tell the user:
> "Fill in the parameters above, then click **Launch Trekker workflow** to start the pipeline."

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
w_output_dir = w_ldata_picker(
    label="Output directory", file_type="dir", key="trekker_output_dir",
)
```

The user may select the FASTQs in the pickers or attach them with the attach button — if they
attach, set the picker's `default` to the attached `latch://` path so the cell stays in sync.

**Cell 2, launch:**
```python
from lplots.widgets.workflow import w_workflow
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
w = w_workflow(
    wf_name="wf.__init__.trekker_pipeline_wf",
    key="trekker_workflow_run_1",
    version="1.4.11-909971",
    params=params,
    automatic=False,                # user clicks the button to launch
    readonly=not params_ready,      # button disabled until every field is set
    label="Launch Trekker workflow",
)
execution = w.value

if execution is not None:
    res = await execution.wait()

    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        workflow_outputs = list(res.output.values())
```

Multiple reactions (one button per reaction, await all together). Build one set of parameter
entry widgets per reaction in cell 1 — same widgets as above, with `key` suffixed by the
reaction number — then in cell 2:
```python
import asyncio
from lplots.widgets.workflow import w_workflow
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

    # ALWAYS called for every reaction — one button each
    w = w_workflow(
        wf_name="wf.__init__.trekker_pipeline_wf",
        key=f"trekker_workflow_run_{i}",
        version="1.4.11-909971",
        params=params,
        automatic=False,
        readonly=not ready_i,
        label=f"Launch Trekker workflow — reaction {i}",
    )
    if w.value is not None:
        executions.append(w.value)

results = await asyncio.gather(*[e.wait() for e in executions])
workflow_outputs = [
    list(res.output.values())
    for res in results
    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}
]
```
</example>

<long_running_guidance>
Once the user clicks the launch button and the execution starts, display this message to the user:

"The Trekker pipeline is now running on Latch compute and will take some time to finish. It is safe to close this tab while the workflow runs. You may monitor the progress of the workflow in the workflows executions tab. When the workflow has completed, reopen the notebook and the agent will resume from where you left off."
</long_running_guidance>
