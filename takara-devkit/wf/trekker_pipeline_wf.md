<goal>
Turn reads (FastQs) into counts
</goal>

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
  - User may one of the three options "10x Chromium Next GEM 3’v3.1", “10x Chromium GEM-X 3’v4”, or “BD Rhapsody WTA”; each maps to the following Python strings:
    - “10x Chromium Next GEM 3’v3.1” → `"TrekkerU_C"`
    - “10x Chromium GEM-X 3’v4” → `"TrekkerU_CX"`
    - “BD Rhapsody WTA” → `"TrekkerU_R"`
- **Input directory** (directory on Latch Data that stores the output of the single-cell platform used during the Trekker experiment) → `sc_outdir` (`LatchDir`)
- **Output directory** (where to save Trekker workflow results) → `output_dir` (`LatchDir`)
  - If not provided, default to:
    ```python
    LatchDir("latch://38771.account/Trekker_Outputs/Test_Data")
    ```
</parameters>

<outputs>
</outputs>

<example>
```python
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir

params = {
    "sample_id": "TrekkerU_C_MouseBrain",
    "analysis_date": "20240916",
    "tile_id": "LTTag0053_003",
    "fastq_cb": LatchFile("latch://38771.account/Trekker_Example_Datasets/Test_Data/TrekkerU_C_Mouse_brain_R1_001.fastq.gz"),
    "fastq_tags": LatchFile("latch://38771.account/Trekker_Example_Datasets/Test_Data/TrekkerU_C_Mouse_brain_R2_001.fastq.gz"),
    "sc_outdir": LatchDir("latch://38771.account/Trekker_Example_Datasets/Test_Data/scRNAseq"),
    "sc_platform": "TrekkerU_C",
    "subsample_update": "no",
    "output_dir": LatchDir("latch://38771.account/Trekker_Example_Datasets/Test_Data/")
}

w = w_workflow(
    wf_name="wf.__init__.trekker_pipeline_wf",
    key="trekker_workflow_run_1",
    version="0.2.3-4fdda8",
    params=params,
    automatic=True,
    label="Trekker workflow",
)
execution = w.value

if execution is not None:
  res = await execution.wait()

  if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
      # inspect workflow outputs for downstream analysis
      workflow_outputs = list(res.output.values())
```
</example>
