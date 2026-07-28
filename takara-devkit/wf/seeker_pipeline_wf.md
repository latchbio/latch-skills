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
This pipeline uses **parameter entry widgets** — do not collect the parameters in chat and hard-code
them. Once the pre-pipeline question is resolved, **immediately generate and run both cells below**
— the parameter widget cell and the launch cell. Do **not** wait for the user to confirm in chat
before generating the launch cell, and do not ask them to tell you when to launch. The user launches
the pipeline by clicking the button that the launch cell renders.

Rules for the launch cell:

- Call `w_workflow(...)` **unconditionally at the top level of the cell.** Never place it inside an
  `if` or a `try`, and never withhold it because the widget values still look empty. An unrendered
  `w_workflow` is a missing launch button — that is the failure mode this pattern exists to prevent.
- Pass `automatic=False` so the workflow launches on click instead of firing the moment the cell
  runs. **This deliberately overrides the `automatic=True` default in `latch-workflows/SKILL.md`**,
  which assumes params are hard-coded rather than entered through widgets. For the Seeker and
  Trekker pipelines, `automatic=False` is correct.
- Gate only the button's *enabled state* with `readonly=not params_ready`, never the call itself.
- Collect the file and directory parameters with `w_ldata_picker` (`file_type="file"` / `"dir"`).
  Its `.value` is an `LPath` or `None` — build `LatchFile` / `LatchDir` conditionally from
  `.value.path` (see the example). Calling `.path` on `None`, or `LatchFile("")`, raises and kills
  the cell before `w_workflow` is reached, which removes the button.

After both cells render, tell the user:
> "Fill in the parameters above, then click **Launch Seeker workflow** to start the pipeline."

The cell re-runs reactively as widget values change, so the button enables on its own once every
required field is set.
</instructions>

<example>
**Cell 1, parameter entry widgets:**
```python
from lplots.widgets.text import w_text_input
from lplots.widgets.select import w_select
from lplots.widgets.ldata import w_ldata_picker

w_sample = w_text_input(
    label="Sample name", key="seeker_sample",
    appearance={"help_text": "No spaces"},
)
w_experiment_date = w_text_input(
    label="Experiment date", key="seeker_experiment_date",
    appearance={"placeholder": "YYYY-MM-DD"},
)
w_tile_id = w_text_input(
    label="Tile ID", key="seeker_tile_id",
    appearance={"placeholder": "A0010_039"},
)
w_fastq_1 = w_ldata_picker(label="Read 1 FASTQ", file_type="file", key="seeker_fastq_1")
w_fastq_2 = w_ldata_picker(label="Read 2 FASTQ", file_type="file", key="seeker_fastq_2")
w_genome = w_select(
    label="Reference genome",
    options=[
        "GRCh38", "GRCm38", "GRCm39", "GRCh38_mm10", "mRatBN7.2", "GRCz11",
        "Mmul_10", "calJac4", "GRCg6a", "Guppy_female_1.0_MT", "BDGP6",
        "XENLA_10.1", "WBPSI7", "TAIR10", "Glycine_max_v2.1", "B73_RefGen_v4",
        "Sorghum",
    ],
    key="seeker_genome",
)
w_execution_name = w_text_input(label="Execution name", key="seeker_execution_name")
w_outdir = w_ldata_picker(label="Output directory", file_type="dir", key="seeker_outdir")
```

The user may select the FASTQs in the pickers or attach them with the attach button — if they
attach, set the picker's `default` to the attached `latch://` path so the cell stays in sync.

**Cell 2, launch:**
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

sample_v = w_sample.value or ""
experiment_date_v = w_experiment_date.value or ""     # "YYYY-MM-DD", e.g. "2023-07-19"
tile_id_v = w_tile_id.value or ""
genome_v = w_genome.value or ""
execution_name_v = w_execution_name.value or ""

# picker values are LPath or None — never call .path on None
fastq_1_v = w_fastq_1.value
fastq_2_v = w_fastq_2.value
outdir_v = w_outdir.value

params_ready = (
    all([sample_v, experiment_date_v, tile_id_v, genome_v, execution_name_v])
    and all(v is not None for v in (fastq_1_v, fastq_2_v, outdir_v))
)

params = {
    "input": [
        Sample(
            sample=sample_v,
            experiment_date=experiment_date_v,
            tile_id=tile_id_v,
            fastq_1=LatchFile(fastq_1_v.path) if fastq_1_v is not None else None,
            fastq_2=LatchFile(fastq_2_v.path) if fastq_2_v is not None else None,
        )
    ],
    "genome": genome_v,
    "genome_choice": "PREBUILT",
    "execution_name": execution_name_v,
    "outdir": LatchDir(outdir_v.path) if outdir_v is not None else None,
}

# ALWAYS called — never inside a conditional, or the launch button will not render
w = w_workflow(
    wf_name="nf_nf_core_curioseeker",
    key="seeker_workflow_run_1",
    version="0.3.6-478939",
    params=params,
    automatic=False,                # user clicks the button to launch
    readonly=not params_ready,      # button disabled until every field is set
    label="Launch Seeker workflow",
)
execution = w.value

if execution is not None:
    res = await execution.wait()

    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        # inspect workflow outputs for downstream analysis
        workflow_outputs = list(res.output.values())
```

For `genome_choice="CUSTOM"`, add a `w_ldata_picker(file_type="dir")` for `igenomes_base` and pass
`LatchDir(igenomes_base_v.path)` in `params` — surface it only if the user asks for a custom genome.
</example>

<long_running_guidance>
Once the user clicks the launch button and the execution starts, display this message to the user:

"The Seeker pipeline is now running on Latch compute and will take some time to finish. It is safe to close this tab while the workflow runs. You may monitor the progress of the workflow in the workflows executions tab. When the workflow has completed, reopen the notebook and the agent will resume from where you left off."
</long_running_guidance>
