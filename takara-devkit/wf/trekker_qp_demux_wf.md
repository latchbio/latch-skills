<goal>
Demultiplex a pooled pair of TrekkerQ_P (Parse Evercode) FASTQ files into per-group paired FASTQ files ready for the Trekker pipeline
</goal>

<parameters>
- **Read 1 FASTQ** → `fastq_r1` (`LatchFile`, **required**)
  - The multiplexed R1 `.fastq.gz` file. Filename must end with `R1.fastq.gz` or `r1.fastq.gz`.
- **Read 2 FASTQ** → `fastq_r2` (`LatchFile`, **required**)
  - The multiplexed R2 `.fastq.gz` file. Filename must end with `R2.fastq.gz` or `r2.fastq.gz`.
- **Output directory** → `output_directory` (`LatchOutputDir`, **required**)
  - Destination directory on Latch where demultiplexed files will be written.
  - Must be provided by the user — do not use a default or placeholder value.
- **Chemistry** → `chemistry` (`str`, **required**)
  - The Parse Evercode chemistry version used. Ask the user and map to the correct string:

    | String value | Chemistry |
    |---|---|
    | `"v1"` | Parse Evercode v1 |
    | `"v2"` | Parse Evercode v2 |
    | `"v3"` | Parse Evercode v3 |

- **Well labels** → `well_labels` (dataclass, **required**)
  - Defines how well positions on the Parse plate are grouped into samples.
  - Ask the user for each group: a group name and the well positions assigned to it.
  - Group names must contain no spaces.
  - Well position syntax:
    - Single well: `"A1"`
    - Row range: `"A1-A12"` (sweeps from start to end position)
    - Rectangular block: `"A1:C6"` (top-left to bottom-right)
    - Multiple selections: comma-joined, e.g. `"A1-A6,B1:D3,C4"`

  ```python
  @dataclass
  class LabelInfo:
      group: str = ""   # sample group name, no spaces
      wells: str = ""   # well positions (see syntax above)

  @dataclass
  class WellLabels:
      labels: List[LabelInfo] = field(default_factory=list)
  ```
</parameters>

<outputs>
For each group defined in `well_labels`, the workflow writes to `output_directory`:
- `{group_name}_R1.fastq.gz` — demultiplexed Read 1
- `{group_name}_R2.fastq.gz` — demultiplexed Read 2

**Feeding outputs into the Trekker pipeline:**
- Use each per-group `_R1.fastq.gz` as `fastq_cb` for Trekker.
- Use each per-group `_R2.fastq.gz` as `fastq_tags` for Trekker.
- Run a separate Trekker workflow execution for each demultiplexed group.
</outputs>

<example>
```python
from dataclasses import dataclass, field
from typing import List
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir

@dataclass
class LabelInfo:
    group: str = ""
    wells: str = ""

@dataclass
class WellLabels:
    labels: List[LabelInfo] = field(default_factory=list)

params = {
    "fastq_r1": LatchFile("latch://38771.account/.../sample_R1.fastq.gz"),
    "fastq_r2": LatchFile("latch://38771.account/.../sample_R2.fastq.gz"),
    "output_directory": LatchDir("<latch://...>"),   # required — set by user
    "chemistry": "v3",                               # "v1", "v2", or "v3"
    "well_labels": WellLabels(labels=[
        LabelInfo(group="group_1", wells="A1-A6"),
        LabelInfo(group="group_2", wells="B1-B6"),
        LabelInfo(group="group_3", wells="A7:C12"),
        # add one LabelInfo per sample group
    ]),
}

w = w_workflow(
    wf_name="wf.__init__.trekker_qp_demux",
    key="trekker_qp_demux_run_1",
    version="1.0.0-4cb1c3",
    params=params,
    automatic=True,
    label="TrekkerQ_P demux",
)
execution = w.value

if execution is not None:
    res = await execution.wait()

    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        workflow_outputs = list(res.output.values())
```
</example>
