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
  - Ask the user to provide it using the attach button in the Agent text interface, or supply its Latch Data path.
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

if execution is not None:
    res = await execution.wait()

    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        workflow_outputs = list(res.output.values())
```
</example>

<long_running_guidance>
After launching the workflow execution, display this message to the user:

"The TrekkerFX_FLEX FASTQ Partitioner is now running on Latch compute and will take some time to finish. It is safe to close this tab while the workflow runs. You may monitor the progress of the workflow in the workflows executions tab. When the workflow has completed, reopen the notebook and the agent will resume from where you left off."
</long_running_guidance>
</output>
