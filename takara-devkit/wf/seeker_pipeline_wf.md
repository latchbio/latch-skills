<goal>
Turn reads (FastQs) into counts
</goal>

<pre_pipeline_questions>
Before collecting any pipeline parameters, ask the user:

> "Do you have multiple R1 (or R2) FASTQ files for this sample — for example, from sequencing the same reaction across multiple lanes for a single tile?"
- If **yes**: concatenate the R1 files into one file and the R2 files into one file using `wf/fastq_concatenator_wf.md` **before** proceeding. Use the concatenated FASTQs as input to the Seeker pipeline.

Only proceed to collect Seeker pipeline parameters after this is resolved and any required concatenation is complete.
</pre_pipeline_questions>

<parameters>
- Every Seeker sample has **two FASTQ files** (paired-end sequencing).
  - **Read 1** → `fastq_1` field of `Sample`
  - **Read 2** → `fastq_2` field of `Sample`
  These must be provided by the user and wrapped as `LatchFile(latch://...)`.
- The `input` parameter is a **list of `Sample` dataclass instances** (one per sample). Each `Sample` has the following fields:
  - **`sample`** (`str`) — Sample name. No spaces.
  - **`experiment_date`** (`str`) — Date in `"YYYY-MM-DD"` format (e.g. `"2023-07-19"`).
  - **`tile_id`** (`str`) — Tile ID (e.g. `"A0010_039"`).
  - **`fastq_1`** (`LatchFile`) — Read 1 FASTQ (`.fastq.gz`).
  - **`fastq_2`** (`LatchFile`) — Read 2 FASTQ (`.fastq.gz`).
- **Reference genome** → `genome`
  - Only used when `genome_choice="PREBUILT"` (the default).
  - Ask the user which organism their sample is from and map their answer to the correct string below. Present all options to the user:

    | String value | Organism |
    |---|---|
    | `"GRCh38"` | Human (*Homo sapiens*) |
    | `"GRCm38"` | Mouse (*Mus musculus*, GRCm38/mm10) |
    | `"GRCm39"` | Mouse (*Mus musculus*, GRCm39/mm39) |
    | `"GRCh38_mm10"` | Human + Mouse (*Homo sapiens* + *Mus musculus*) |
    | `"mRatBN7.2"` | Rat (*Rattus norvegicus*) |
    | `"GRCz11"` | Zebrafish (*Danio rerio*) |
    | `"Mmul_10"` | Rhesus macaque (*Macaca mulatta*) |
    | `"calJac4"` | Common marmoset (*Callithrix jacchus*) |
    | `"GRCg6a"` | Chicken (*Gallus gallus*) |
    | `"Guppy_female_1.0_MT"` | Guppy fish (*Poecilia reticulata*) |
    | `"BDGP6"` | Fruit fly (*Drosophila melanogaster*) |
    | `"XENLA_10.1"` | African clawed frog (*Xenopus laevis*) |
    | `"WBPSI7"` | *C. elegans* |
    | `"TAIR10"` | Thale cress (*Arabidopsis thaliana*) |
    | `"Glycine_max_v2.1"` | Soybean (*Glycine max*) |
    | `"B73_RefGen_v4"` | Maize (*Zea mays*) |
    | `"Sorghum"` | Sorghum (*Sorghum bicolor*) |

- **Genome choice** → `genome_choice`
  - `"PREBUILT"` (default) — uses the selected `genome` reference.
  - `"CUSTOM"` — uses a user-supplied genome directory via `igenomes_base`.
- **Custom genome base directory** → `igenomes_base` (`LatchDir`, optional)
  - Only required when `genome_choice="CUSTOM"`.
  - Must contain `Annotation/Genes/genes.gtf` and `Sequence/STARIndex/` subdirectories.
- **Execution name** → `execution_name` (`str`, **required**)
  - Names the run and the output subdirectory created under `outdir`.
  - Must be provided by the user — do not use a default or placeholder value.
- **Output directory** → `outdir` (`LatchDir`, **required**)
  - Top-level directory where results are saved.
  - Must be provided by the user — do not use a default or placeholder value.
</parameters>

<outputs>
</outputs>

<instructions>
After collecting all required parameters from the user, confirm they are ready before executing the pipeline. Say:
> "All parameters are set. Let me know when you're ready to start the Seeker pipeline."
Only generate and execute the code cell below once the user confirms.
</instructions>

<example>
```python
from dataclasses import dataclass
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir

@dataclass
class Sample:
    sample: str
    experiment_date: str
    tile_id: str
    fastq_1: LatchFile
    fastq_2: LatchFile

params = {
    "input": [
        Sample(
            sample="",                              # required — sample name, no spaces
            experiment_date="YYYYMMDD",             # required — "YYYYMMDD"
            tile_id="",                             # required — e.g. "A0010_039"
            fastq_1=LatchFile("latch://..."),       # required — set by user
            fastq_2=LatchFile("latch://..."),       # required — set by user
        )
    ],
    "genome": "",                                   # required — set by user
    "genome_choice": "PREBUILT",
    "execution_name": "",                           # required — set by user
    "outdir": LatchDir("latch://..."),              # required — set by user
}

w = w_workflow(
    wf_name="nf_nf_core_curioseeker",
    key="seeker_workflow_run_1",
    version="0.3.6-478939",
    params=params,
    automatic=True,
    label="Seeker workflow",
)
execution = w.value

if execution is not None:
    res = await execution.wait()

    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        # inspect workflow outputs for downstream analysis
        workflow_outputs = list(res.output.values())
```
</example>

<long_running_guidance>
After launching the workflow execution, display this message to the user:

"The Seeker pipeline is now running on Latch compute and will take some time to finish. It is safe to close this tab while the workflow runs. You may monitor the progress of the workflow in the workflows executions tab. When the workflow has completed, reopen the notebook and the agent will resume from where you left off."
</long_running_guidance>
