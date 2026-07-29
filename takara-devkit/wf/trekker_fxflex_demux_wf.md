<goal>
Demultiplex a pooled pair of TrekkerFX_FLEX FASTQ files into per-sample paired FASTQ files ready for the Trekker pipeline. Supports both 10x Genomics FLEX chemistries: FLEX v2 (APEX) and FLEX v1.
</goal>

<pre_demux_questions>
Before collecting parameters, ask the user the following **in order**:

1. **Which FLEX chemistry version was used?**
   The demultiplexer must know which barcode set to partition against. Ask the user to choose:

   | Chemistry | `chemistry` value | Barcode IDs | Barcode count |
   |---|---|---|---|
   | 10x Genomics FLEX v2 (APEX) *(default)* | `Chemistry.FLEX_v2_APEX` | `A-A01` through `D-H12` (plate A–D, row A–H, column 01–12) | 384 |
   | 10x Genomics FLEX v1 | `Chemistry.FLEX_v1` | `AB001` through `AB016` | 16 |

   - If the user is unsure, FLEX v2 (APEX) is the current default chemistry.
   - The chosen chemistry determines the valid barcode IDs used when labeling samples in question 2 — a v1 barcode (e.g. `AB003`) is invalid under v2, and vice versa.

2. **How would you like to label the demultiplexed samples? (optional)**
   Assigning a sample name to each barcode is **optional**. Let the user know they have two ways to supply the mapping, or may skip it entirely:
   - **Enter names and barcodes manually** (`sample_labels`): for every sample in the pool, give a **sample name** and the **barcode ID** it was assigned (matching the chemistry from question 1), one row per sample.
   - **Use a manifest file** (`sample_manifest`): upload a headerless two-column file mapping sample name → barcode ID.
   - **Skip it:** if no labels are provided, outputs are named by their barcode ID.
   - Sample names must contain **no spaces**. If both a samplesheet and a manifest file are supplied, the uploaded manifest file takes precedence.

Once chemistry (and the optional labeling approach) are resolved, proceed to collect the remaining parameters.
</pre_demux_questions>

<parameters>
- **Read 1 FASTQ** → `fastq_r1` (`LatchFile`, **required**)
  - The multiplexed R1 `.fastq.gz` file. Filename must contain `R1` (or `r1`) and end with `fastq.gz`.
- **Read 2 FASTQ** → `fastq_r2` (`LatchFile`, **required**)
  - The multiplexed R2 `.fastq.gz` file. Filename must contain `R2` (or `r2`) and end with `fastq.gz`.
- **FLEX chemistry version** → `chemistry` (`Chemistry` enum, **required**)
  - Determined in the pre-demux questions. Maps to:

    ```python
    class Chemistry(Enum):
        FLEX_v2_APEX = "v2"   # default — 384 barcodes, A-A01 through D-H12
        FLEX_v1      = "v1"   # 16 barcodes, AB001 through AB016
    ```

  - Defaults to `Chemistry.FLEX_v2_APEX` if not set.
- **Output directory** → `output_directory` (`LatchOutputDir`, **required**)
  - Destination directory on Latch where demultiplexed files will be written.
  - Must be provided by the user — do not use a default or placeholder value.
- **Sample labels** → `sample_labels` (`List[LabelInfo]`, optional)
  - A samplesheet with one row per sample, entered manually. Each row (`LabelInfo`) maps a **sample name** to the **barcode ID** that sample was multiplexed under.
  - Optional: leave empty to name outputs by their barcode ID, or supply a `sample_manifest` file instead.
  - Barcode IDs must match the selected chemistry (v1: `AB001`–`AB016`, v2: `A-A01` through `D-H12`).
  - Sample names must contain no spaces.

    ```python
    @dataclass
    class LabelInfo:
        sample_name: str
        barcode_id: str
    ```

- **Sample manifest file** → `sample_manifest` (`LatchFile`, optional — alternative to `sample_labels`)
  - A headerless, two-column file mapping sample name → barcode ID, one row per sample. Columns may be comma-, tab-, or semicolon-delimited.
  - Column 1 = sample name, column 2 = barcode ID (matching the chosen chemistry).
  - Example rows:
    ```
    Sample1,A-A01
    Sample2,A-A02
    ```
  - **If provided, this file takes precedence over `sample_labels`.**
  - Offer both input routes: render a `w_ldata_picker` (`file_type="file"`) for it and tell the user they may instead use the attach button in the Agent text interface. If neither works, ask for its Latch Data path.
</parameters>

<outputs>
For each detected sample (barcode), the workflow writes to `output_directory`:
- `{sample_name_or_barcode_id}_R1.fastq.gz` — demultiplexed Read 1
- `{sample_name_or_barcode_id}_R2.fastq.gz` — demultiplexed Read 2
- `metrics.csv` — per-sample read counts and percentages
- a run log

**Feeding outputs into the Trekker pipeline:**
- Use each per-sample `_R1.fastq.gz` as `fastq_cb` for Trekker.
- Use each per-sample `_R2.fastq.gz` as `fastq_tags` for Trekker.
- Select `TrekkerFX_FLEX` as the Trekker `sc_platform` — the Trekker pipeline auto-detects the FLEX barcode version, so v1 and v2 (APEX) demultiplexed outputs are both fed in the same way.
- Run a separate Trekker workflow execution for each demultiplexed sample.
</outputs>

<example>
```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir


@dataclass
class LabelInfo:
    sample_name: str
    barcode_id: str


class Chemistry(Enum):
    FLEX_v2_APEX = "v2"
    FLEX_v1 = "v1"


params = {
    "fastq_r1": LatchFile("latch://..."),             # required — set by user
    "fastq_r2": LatchFile("latch://..."),             # required — set by user
    "output_directory": LatchDir("latch://..."),      # required — set by user
    "chemistry": Chemistry.FLEX_v2_APEX,              # FLEX_v2_APEX (default) or FLEX_v1
    "sample_labels": [                                 # barcode -> sample name mapping
        LabelInfo(sample_name="TumorSample", barcode_id="A-A01"),
        LabelInfo(sample_name="NormalSample", barcode_id="A-A02"),
        # add one entry per sample; barcode IDs must match the chosen chemistry
    ],
    # Alternatively, upload a manifest file instead of sample_labels (takes precedence):
    # "sample_manifest": LatchFile("latch://..."),
}

w = w_workflow(
    wf_name="wf.__init__.trekker_fxflex_demux",
    key="trekker_fxflex_demux_run_1",
    version="1.1.1-c72111",
    params=params,
    automatic=True,
    label="TrekkerFX_FLEX demux",
)
execution = w.value

# Do NOT `await execution.wait()` here — the partitioner runs for a long time and the user is told
# they may shut the notebook pod down. Check for outputs with the results cell below. See <resuming>.
```

**Results cell** — generate it now, run it when the user says the execution has finished. It reads
Latch Data rather than kernel state, so it works even after a pod restart:
```python
from latch.ldata.path import LPath
from lplots.widgets.text import w_text_output

out_dir = LPath("latch://...")          # the same output_directory passed in params

try:
    fastqs = sorted(p.path for p in out_dir.iterdir() if p.path.endswith(".fastq.gz"))
except Exception:
    fastqs = []

if fastqs:
    w_text_output(
        content="Demultiplexed FASTQs in `{}`:\n\n".format(out_dir.path)
        + "\n".join(f"- `{p}`" for p in fastqs),
        appearance={"message_box": "success"},
        key="fxflex_demux_outputs_found",
    )
else:
    w_text_output(
        content=(
            f"No demultiplexed FASTQs under `{out_dir.path}` yet — the execution is most likely "
            "still running. Check its status in the workflows executions tab, then re-run this cell "
            "once it reaches SUCCEEDED."
        ),
        appearance={"message_box": "warning"},
        key="fxflex_demux_outputs_pending",
    )
```

If `iterdir()` is unavailable in the runtime, browse the directory with
`w_ldata_browser(dir=out_dir)` instead — the point is only to confirm the per-sample
`_R1.fastq.gz` / `_R2.fastq.gz` pairs exist in Latch Data before feeding them into Trekker.
</example>

<long_running_guidance>
After launching the workflow execution, display this message to the user **in full** — do not
shorten it or drop the pod shutdown advice:

"The TrekkerFX_FLEX FASTQ Partitioner is now running on Latch compute and will take some time to finish. It runs independently of this notebook, so it is safe to close this tab — and you may also **shut down the notebook pod while the workflow runs, which stops the notebook compute charges and saves cost**. Shutting the pod down will not interrupt the workflow. You may monitor the progress of the workflow in the workflows executions tab. When the workflow has completed, restart the pod, reopen the notebook, and the agent will resume from where you left off."

Because that advice invites the user to shut the pod down, the launch cell must **not** block on
`await execution.wait()` — an await parks the cell in a permanently-running state, binds no result,
and does not survive a pod restart.
</long_running_guidance>

<resuming>
The launch cell does not wait for the execution. When the user comes back and says it has finished,
or types "continue":

- **The notebook is not the source of truth.** The execution runs on Latch compute, outside this pod.
  Never report "the partitioner is still running" because a cell looks busy, because
  `workflow_outputs` is undefined, or because you have no record of it completing — none of those are
  evidence.
- **Check Latch Data.** Run the results cell. Per-sample `_R1.fastq.gz` / `_R2.fastq.gz` pairs under
  `output_directory` mean the run finished; nothing there means it is still running or failed, and
  the user should check the workflows executions tab.
- **If kernel state was lost** (pod restarted), do not try to reconstruct `execution` or `res` — they
  are gone and are not needed. The demultiplexed FASTQ paths are all that the Trekker pipeline needs.
- Once the FASTQs are present, go straight on to `wf/trekker_pipeline_wf.md`, one execution per
  demultiplexed sample. Do not ask the user to re-confirm that the run finished.
</resuming>
</output>
