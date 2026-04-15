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
  - Ask the user which single-cell platform was used and map their answer to the correct string below. Present all 11 options to the user:

    | String value | Platform |
    |---|---|
    | `"TrekkerU_C"` | 10x Chromium Next GEM 3'v3.1 |
    | `"TrekkerU_CX"` | 10x Chromium GEM-X 3'v4 |
    | `"Trekker5C_CX"` | 10x Chromium, 5' |
    | `"TrekkerFX_FLEX"` | 10x Chromium GEM-X Flex v1 ⚠️ *requires preprocessing — see below* |
    | `"TrekkerU_M"` | 10x Chromium Multiome ATAC + Gene Expression |
    | `"TrekkerU_R"` | BD Rhapsody WTA |
    | `"TrekkerU_RVDJ"` | BD Rhapsody TCR/BCR Next + mRNA WTA |
    | `"TrekkerU_RATAC"` | BD Rhapsody ATAC-Seq + mRNA WTA |
    | `"TrekkerU_IL"` | Illumina Single Cell 3' RNA Prep (DRAGEN) |
    | `"TrekkerU_PIP"` | Illumina Single Cell 3' RNA Prep (PIPSeeker) ⚠️ *requires preprocessing — see below* |
    | `"TrekkerQ_P"` | Parse Evercode WT v3 ⚠️ *requires preprocessing — see below* |

- **Input directory** (directory on Latch Data that stores the output of the single-cell platform used during the Trekker experiment) → `sc_outdir` (`LatchDir`)
- **Output directory** (where to save Trekker workflow results) → `output_dir` (`LatchDir`)

**Platforms requiring preprocessing — run the relevant workflow first, then use its outputs as Trekker inputs:**

- **`TrekkerFX_FLEX`** → follow `wf/trekker_fxflex_demux_wf.md` before running Trekker.
  - The preprocessing workflow demultiplexes the pooled FASTQs into per-sample pairs.
  - Use each output `_R1.fastq.gz` as `fastq_cb` and `_R2.fastq.gz` as `fastq_tags` for Trekker.
  - Run a separate Trekker execution for each demultiplexed sample.

- **`TrekkerU_PIP`** → follow `wf/trekker_upip_preprocess_wf.md` before running Trekker.
  - The preprocessing workflow converts the R1 FASTQ and scRNA-seq files into Trekker-compatible versions.
  - Use the output `<prefix>_converted_R1.fastq.gz` as `fastq_cb` for Trekker.
  - Use the **original** R2 `.fastq.gz` (unchanged) as `fastq_tags` for Trekker.
  - Use the output `converted_sc/` directory as `sc_outdir` for Trekker — **not** the original sc directory.

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
After collecting all required parameters from the user, confirm they are ready before executing the pipeline. Say:
> "All parameters are set. Let me know when you're ready to start the Trekker pipeline."
Only generate and execute the code cell below once the user confirms.
</instructions>

<example>
```python
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir

params = {
    "sample_id": "",                            # required — set by user
    "analysis_date": "YYYYMMDD",                # required — "YYYYMMDD"
    "tile_id": "",                              # required — set by user
    "fastq_cb": LatchFile("latch://..."),       # required — set by user
    "fastq_tags": LatchFile("latch://..."),     # required — set by user
    "sc_outdir": LatchDir("latch://..."),       # required — set by user
    "sc_platform": "",                          # required — set by user
    "output_dir": LatchDir("latch://..."),      # required — set by user
}

w = w_workflow(
    wf_name="wf.__init__.trekker_pipeline_wf",
    key="trekker_workflow_run_1",
    version="1.4.0-cd747c",
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
