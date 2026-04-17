<goal>
Turn reads (FastQs) into counts
</goal>

<pre_pipeline_questions>
Before collecting any pipeline parameters, ask the user the following questions **in order**:

1. **Which single-cell platform was used?**
   Present the full `sc_platform` table from the parameters section below and ask the user to identify their platform.
   - If the selected platform is **TrekkerFX_FLEX**, **TrekkerU_PIP**, or **TrekkerQ_P**: run the corresponding preprocessing workflow first (see the platform-specific notes in the parameters section), then return here to continue with questions 2 and 3.
   - All other platforms: proceed directly to question 2.

2. **Multiple reactions?**
   > "Was the experiment for this Trekker tile split into multiple single-nuclei reactions (i.e. processed with different sample indices during sequencing)?"
   - If **yes**: plan to run the Trekker pipeline once per reaction and merge the outputs afterward using `wf/trekker_merger_wf.md`. Inform the user now so they can plan sample IDs and output directories for each reaction.

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
  - Three platforms require a preprocessing workflow before Trekker can run — these are called out first:

    **Platforms requiring preprocessing (must be run before Trekker):**

    | String value | Platform | Preprocessing workflow |
    |---|---|---|
    | `"TrekkerFX_FLEX"` | 10x Chromium GEM-X Flex v1 | `wf/trekker_fxflex_demux_wf.md` |
    | `"TrekkerU_PIP"` | Illumina Single Cell 3' RNA Prep (PIPSeeker) | `wf/trekker_upip_preprocess_wf.md` |
    | `"TrekkerQ_P"` | Parse Evercode WT v3 | `wf/trekker_qp_demux_wf.md` |

    **All platforms:**

    *10x Chromium*

    | String value | Platform |
    |---|---|
    | `"TrekkerU_C"` | 10x Chromium Next GEM 3'v3.1 |
    | `"TrekkerU_CX"` | 10x Chromium GEM-X 3'v4 |
    | `"Trekker5C_CX"` | 10x Chromium, 5' |
    | `"TrekkerFX_FLEX"` | 10x Chromium GEM-X Flex v1 ⚠️ |
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
    | `"TrekkerU_PIP"` | Illumina Single Cell 3' RNA Prep (PIPSeeker) ⚠️ |

    *Parse*

    | String value | Platform |
    |---|---|
    | `"TrekkerQ_P"` | Parse Evercode WT v3 ⚠️ |

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
