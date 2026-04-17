<goal>
Demultiplex a pooled pair of TrekkerFX_FLEX FASTQ files into per-sample paired FASTQ files ready for the Trekker pipeline
</goal>

<parameters>
- **Read 1 FASTQ** → `fastq_r1` (`LatchFile`, **required**)
  - The multiplexed R1 `.fastq.gz` file. Filename must end with `R1.fastq.gz` or `r1.fastq.gz`.
- **Read 2 FASTQ** → `fastq_r2` (`LatchFile`, **required**)
  - The multiplexed R2 `.fastq.gz` file. Filename must end with `R2.fastq.gz` or `r2.fastq.gz`.
- **Output directory** → `output_directory` (`LatchOutputDir`, **required**)
  - Destination directory on Latch where demultiplexed files will be written.
  - Must be provided by the user — do not use a default or placeholder value.
- **Sample labels** → `sample_labels` (dataclass, optional)
  - Maps each of the 16 multiplex barcode slots (AB001–AB016) to an optional custom sample name.
  - Ask the user which barcode slots they used (e.g. AB001, AB003) and what sample name to assign to each.
  - Any slot left blank (`""`) will use the barcode ID itself (e.g. `AB001`) as the output filename prefix.
  - Sample names must contain no spaces.
  - Slots with fewer than 1% of total reads and no assigned name are automatically dropped from the output.

  ```python
  @dataclass
  class SampleLabels:
      AB001: str = ""
      AB002: str = ""
      AB003: str = ""
      AB004: str = ""
      AB005: str = ""
      AB006: str = ""
      AB007: str = ""
      AB008: str = ""
      AB009: str = ""
      AB010: str = ""
      AB011: str = ""
      AB012: str = ""
      AB013: str = ""
      AB014: str = ""
      AB015: str = ""
      AB016: str = ""
  ```
</parameters>

<outputs>
For each detected barcode slot, the workflow writes to `output_directory`:
- `{sample_name_or_barcodeID}_R1.fastq.gz` — demultiplexed Read 1
- `{sample_name_or_barcodeID}_R2.fastq.gz` — demultiplexed Read 2
- `metrics.csv` — per-sample read counts and percentages

**Feeding outputs into the Trekker pipeline:**
- Use each per-sample `_R1.fastq.gz` as `fastq_cb` for Trekker.
- Use each per-sample `_R2.fastq.gz` as `fastq_tags` for Trekker.
- Run a separate Trekker workflow execution for each demultiplexed sample.
</outputs>

<example>
```python
from dataclasses import dataclass
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir

@dataclass
class SampleLabels:
    AB001: str = ""
    AB002: str = ""
    AB003: str = ""
    AB004: str = ""
    AB005: str = ""
    AB006: str = ""
    AB007: str = ""
    AB008: str = ""
    AB009: str = ""
    AB010: str = ""
    AB011: str = ""
    AB012: str = ""
    AB013: str = ""
    AB014: str = ""
    AB015: str = ""
    AB016: str = ""

params = {
    "fastq_r1": LatchFile("latch://38771.account/.../sample_R1.fastq.gz"),
    "fastq_r2": LatchFile("latch://38771.account/.../sample_R2.fastq.gz"),
    "output_directory": LatchDir("<latch://...>"),   # required — set by user
    "sample_labels": SampleLabels(
        AB001="TumorSample",
        AB002="NormalSample",
        # leave unused slots as "" to use barcode ID as filename prefix
    ),
}

w = w_workflow(
    wf_name="wf.__init__.trekker_fxflex_demux",
    key="trekker_fxflex_demux_run_1",
    version="1.0.0-69f00b",
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
