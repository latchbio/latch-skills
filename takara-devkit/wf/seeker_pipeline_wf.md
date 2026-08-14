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
  - **Always offer both** in the parameter entry widgets — never assume `"PREBUILT"`.
- **Custom genome base directory** → `igenomes_base` (`LatchDir`, optional)
  - Only required when `genome_choice="CUSTOM"`, and only then is it passed in `params`.
  - Collect it with a directory picker that appears when the user selects `"CUSTOM"`.
  - Must contain `Annotation/Genes/genes.gtf` and `Sequence/STARIndex/` subdirectories.
- **Execution name** → `execution_name` (`str`, **required**)
  - Names the run and the output subdirectory created under `outdir`.
  - Must be provided by the user — do not use a default or placeholder value.
- **Output directory** → `outdir` (`LatchDir`, **required**)
  - Top-level directory where results are saved.
  - Must be provided by the user — do not use a default or placeholder value.
</parameters>

<outputs>
Verified against the deployment source (`latch_platform/curioseeker`, `version` = 0.3.6), not
inferred. The entrypoint rewrites `outdir` to `f"{outdir.remote_path}/{execution_name}"` before
handing it to Nextflow (`wf/entrypoint_curio.py:226`), and every secondary module publishes to
`"${params.outdir}/OUTPUT/${meta.id}"` where `meta.id` is the samplesheet's `sample` column
(`subworkflows/local/input_check.nf:79`). So the results land at:

```
<outdir>/<execution_name>/
└── OUTPUT/
    └── <sample>/
        ├── <sample>_anndata.h5ad                        # ← secondary analysis input
        ├── <sample>_Report.html                         # ← the QC report
        ├── <sample>_seurat.rds
        ├── <sample>_Metrics.csv
        ├── <sample>_cluster_assignment.txt
        ├── <sample>_variable_features_clusters.txt
        └── <sample>_variable_features_spatial_moransi.txt
```

The two files this skill needs, and the modules that emit them:

- **`<sample>_anndata.h5ad`** — the AnnData the whole Secondary Analysis plan runs on, written by
  `sceasy::convertFormat` at the end of `bin/analysis.R:104` and published by
  `modules/local/secondary/analysis.nf:2,20`. **This is the file `steps/data_loading.md` loads.**
- **`<sample>_Report.html`** — the QC report (`modules/local/secondary/genreport.nf:2,23`,
  `bin/genreport.R:17`).

The generic nf-core `publishDir` in `conf/modules.config` — which would have placed outputs in
per-process directories — is **not** in effect: its `includeConfig` is commented out
(`nextflow.config:269`). The `OUTPUT/<sample>/` layout above is the one that runs.

Even so, **use the layout as a fast path and search by suffix as the fallback** (`_anndata.h5ad`,
`_Report.html`), anchored at the run directory. A constructed path that is wrong reports "the
pipeline hasn't finished" for a run that succeeded.
</outputs>

<instructions>
This pipeline uses **parameter entry widgets** — do not collect the parameters in chat and hard-code
them. Once the pre-pipeline question is resolved, **immediately generate and run both cells below**
— the parameter widget cell and the launch cell. Do **not** wait for the user to confirm in chat
before generating the launch cell, and do not ask them to tell you when to launch. The user launches
the pipeline by clicking the button that the launch cell renders.

Rules for the launch cell:

- Call `launch_workflow_once(...)` — never `w_workflow` directly — **unconditionally at the top
  level of the cell.** Never place it inside an `if` or a `try`, and never withhold it because the
  widget values still look empty. An unrendered launch call is a missing launch button — that is the
  failure mode this pattern exists to prevent. The helper guards against launching a run that is
  already in flight, and skips that check entirely while `readonly=True`, so it costs nothing on the
  reactive re-runs this cell does on every keystroke. See "Launching a workflow at most once" in
  `SKILL.md`.
- Pass `automatic=False` so the workflow launches on click instead of firing the moment the cell
  runs. **This deliberately overrides the `automatic=True` default in `latch-workflows/SKILL.md`**,
  which assumes params are hard-coded rather than entered through widgets. For the Seeker and
  Trekker pipelines, `automatic=False` is correct.
- Gate only the button's *enabled state* with `readonly=not params_ready`, never the call itself.
- Always offer **both genome sources**. Render a `PREBUILT` / `CUSTOM` choice, and swap the input
  below it reactively: the prebuilt genome list for `PREBUILT`, a directory picker for
  `igenomes_base` for `CUSTOM`. Never hard-code `genome_choice="PREBUILT"` — the user must be able
  to supply their own genome directory.
- Collect the file and directory parameters with `w_ldata_picker` (`file_type="file"` / `"dir"`).
  Its `.value` is an `LPath` or `None` — build `LatchFile` / `LatchDir` conditionally from
  `.value.path` (see the example). Calling `.path` on `None`, or `LatchFile("")`, raises and kills
  the cell before the launch call is reached, which removes the button.
- **The output directory is a picker like any other, and never a guess.** If the user named an output
  directory earlier in this session, pass it as `w_outdir`'s `default=` and say so in chat; if they
  did not, leave `default` unset rather than filling in a plausible path. See "Asking for an output
  directory" in `SKILL.md`.
- Include the `w_text_output(...)` long-running notice inside `if execution is not None:`. The click
  lands after your turn ends, so a chat message you would "display after launching" never happens —
  the cell has to render it. See `<long_running_guidance>`.
- **Never call `await execution.wait()` in the launch cell.** The Seeker pipeline runs for hours, and
  the notice explicitly invites the user to shut the notebook pod down while it runs. An `await`
  parks the cell in a permanently-running state, binds no result, and survives no pod restart — it is
  the reason the agent gets stuck reporting "still running" after the pipeline has finished.
- **Generate all three cells in the same turn**, including the resume cell (cell 3). Nothing in Plots
  can start an agent turn, so when the pipeline finishes hours later there is no way for you to be
  running. The resume button is what the user clicks instead; if it is not already on screen when
  they leave, their only recourse is to interrupt you and type "continue", which is exactly the
  confusing flow this pattern exists to remove. See `<resuming>`.

- **Name the tab when you hand off.** These cells render in a **new tab** that the notebook does not
  switch to, and every one of them needs a click. A launch button the user never finds is the same as
  no launch button, and the resume button is worse — they come back hours later, see nothing, and
  conclude the run was lost. See "Telling the user where results appeared" in `SKILL.md`.

After all three cells render, tell the user:
> "The parameter form and the **Launch Seeker workflow** button are in a **new tab** in this notebook
> — click that tab, fill in the fields, then click Launch. When the pipeline finishes — however long
> that takes, and even if you shut the pod down in between — come back to that same tab and click
> **Show my QC report**; the report link appears right there. You don't need to message me for that
> step."

The cell re-runs reactively as widget values change, so the button enables on its own once every
required field is set.
</instructions>

<example>
**Cell 1, parameter entry widgets:**
```python
from lplots.widgets.text import w_text_input
from lplots.widgets.select import w_select
from lplots.widgets.radio import w_radio_group
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
w_genome_choice = w_radio_group(
    label="Genome source",
    options=["PREBUILT", "CUSTOM"],
    default="PREBUILT",
    key="seeker_genome_choice",
)

# reading .value here makes the cell re-run when the user switches source,
# so the matching input below swaps in automatically
genome_choice_v = w_genome_choice.value or "PREBUILT"

w_genome = None
w_igenomes_base = None

if genome_choice_v == "PREBUILT":
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
else:
    w_igenomes_base = w_ldata_picker(
        label="Custom genome base directory (igenomes_base)",
        file_type="dir",
        key="seeker_igenomes_base",
        appearance={
            "help_text": "Must contain Annotation/Genes/genes.gtf and Sequence/STARIndex/"
        },
    )

w_execution_name = w_text_input(label="Execution name", key="seeker_execution_name")
# add default="latch://..." only when the user has already chosen an output directory this session
w_outdir = w_ldata_picker(label="Output directory", file_type="dir", key="seeker_outdir")
```

The user may select the FASTQs in the pickers or attach them with the attach button — if they
attach, set the picker's `default` to the attached `latch://` path so the cell stays in sync.

**Cell 2, launch:**
```python
from dataclasses import dataclass
# resolve takara/lib per SKILL.md "Helper library usage", then:
from takara.launch import LaunchStatus, launch_workflow_once
from lplots.widgets.text import w_text_output
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
execution_name_v = w_execution_name.value or ""

# picker values are LPath or None — never call .path on None
fastq_1_v = w_fastq_1.value
fastq_2_v = w_fastq_2.value
outdir_v = w_outdir.value

# only one of these two widgets exists, depending on the genome source
genome_choice_v = w_genome_choice.value or "PREBUILT"
genome_v = (w_genome.value or "") if w_genome is not None else ""
igenomes_base_v = w_igenomes_base.value if w_igenomes_base is not None else None

genome_ready = bool(genome_v) if genome_choice_v == "PREBUILT" else igenomes_base_v is not None

params_ready = (
    all([sample_v, experiment_date_v, tile_id_v, execution_name_v])
    and all(v is not None for v in (fastq_1_v, fastq_2_v, outdir_v))
    and genome_ready
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
    "genome_choice": genome_choice_v,
    "execution_name": execution_name_v,
    "outdir": LatchDir(outdir_v.path) if outdir_v is not None else None,
}

# pass only the key that belongs to the selected genome source
if genome_choice_v == "PREBUILT":
    params["genome"] = genome_v
else:
    params["igenomes_base"] = (
        LatchDir(igenomes_base_v.path) if igenomes_base_v is not None else None
    )

# ALWAYS called — never inside a conditional, or the launch button will not render
res = launch_workflow_once(
    wf_name="nf_nf_core_curioseeker",
    version="0.3.6-478939",
    params=params,
    label="Launch Seeker workflow",
    key_prefix="seeker_workflow",   # key is derived from params — do NOT pass a hand-written key
    run_name=execution_name_v,      # outputs land in <outdir>/<execution_name>/
    output_dir=outdir_v.path if outdir_v is not None else "",
    automatic=False,                # user clicks the button to launch
    readonly=not params_ready,      # button disabled until every field is set
)
execution = res.execution

if execution is not None:
    # The long-running notice MUST be rendered here, by the cell itself. The click happens
    # after the agent's turn has ended, so the agent is not running and cannot post it to chat.
    w_text_output(
        content=(
            "The Seeker pipeline is now running on Latch compute and will take some time to "
            "finish. It runs independently of this notebook, so you may **shut down the "
            "notebook pod while the workflow runs, which stops the notebook compute charges "
            "and saves cost**. Shutting the pod down will "
            "not interrupt the workflow. You may monitor the progress of the workflow in the "
            "workflows executions tab. When the workflow has completed, restart the pod, reopen "
            "the notebook, and click **Show my QC report** below — that is all you need to do, "
            "and you do not have to message the agent for it."
        ),
        appearance={"message_box": "info"},
        key="seeker_long_running_notice",
    )

# The cell ENDS here. Do not `await execution.wait()` — see <resuming>.
```

**Cell 3, resume** — generate and run this in the same turn as cells 1 and 2, so the button is on
screen before the user walks away. Clicking it re-runs *this cell in the kernel*; no agent turn is
involved, which is what makes the whole post-pipeline step work without the user having to message
the agent. It reads Latch Data rather than kernel state, so it also survives a pod restart:
```python
from pathlib import Path

from latch.ldata.path import LPath
from lplots.widgets.button import w_button
from lplots.widgets.text import w_text_output

resume = w_button(label="Show my QC report", key="seeker_resume")

# Re-derived from the widgets, not from the launch cell's variables. Picker values are LPath or
# None, and after a pod restart the parameter cell may not have been re-run at all — so never call
# .path unguarded (same rule as the launch cell).
# The task nests everything under <outdir>/<execution_name>/, and the secondary modules publish to
# OUTPUT/<sample>/ beneath that — see <outputs>.
try:
    run_dir = LPath(f"{w_outdir.value.path.rstrip('/')}/{w_execution_name.value or ''}")
    sample_v = w_sample.value or ""
except (AttributeError, NameError):
    run_dir, sample_v = None, ""

# reading .value makes this cell reactive — the click re-runs it
if resume.value and run_dir is None:
    w_text_output(
        content=(
            "I don't have the output directory for this run. Re-run the parameter cell above, set "
            "**Output directory** and **Execution name**, then click this button again."
        ),
        appearance={"message_box": "warning"},
        key="seeker_resume_no_params",
    )
elif resume.value:

    def _by_suffix(root: LPath, suffix: str, depth: int) -> list[LPath]:
        """Every file ending in `suffix` at or below root. Bounded; tolerates files and missing dirs."""
        found: list[LPath] = []
        try:
            entries = list(root.iterdir())
        except Exception:          # not a directory, or not created yet
            return found
        for p in entries:
            if p.path.rsplit("/", 1)[-1].endswith(suffix):
                found.append(p)
            elif depth > 1:
                found.extend(_by_suffix(p, suffix, depth - 1))
        return found

    # Fast path: the directory the deployed workflow actually publishes to (see <outputs>).
    # Falls back to a bounded search from the run directory, so a layout change costs speed,
    # not correctness. Both files land in the same directory, so one fast path serves both.
    known = LPath(f"{run_dir.path}/OUTPUT/{sample_v}") if sample_v else run_dir

    def _locate(suffix: str) -> LPath | None:
        hits = _by_suffix(known, suffix, 1) or _by_suffix(run_dir, suffix, 6)
        # Rank on the FILENAME, not the full path — the run directory itself often contains the
        # sample name, so matching on the path makes every candidate tie and another sample's
        # file can win.
        hits.sort(key=lambda p: not p.path.rsplit("/", 1)[-1].startswith(f"{sample_v}_"))
        return hits[0] if hits else None

    report = _locate("_Report.html")

    # Located here, next to the report, for one reason: this cell's output is the ONLY record of
    # the h5ad's location that survives a pod restart. The launch cell binds no execution result,
    # so if this path is not printed, the agent has nothing to derive it from when the user comes
    # back for secondary analysis — and steps/data_loading.md then has to ask for it. See
    # <resuming>.
    h5ad = _locate("_anndata.h5ad")

    if report is None:
        w_text_output(
            content=(
                f"No `*_Report.html` found under `{run_dir.path}`, so the pipeline has not finished "
                "writing its outputs. Check the execution's status in the workflows executions tab; "
                "if it is still running, click this button again once it reaches SUCCEEDED. If it "
                "shows FAILED, tell me and I'll look at the logs."
            ),
            appearance={"message_box": "warning"},
            key="seeker_resume_pending",
        )
    else:
        # Image optimization is a nice-to-have; the link is the deliverable. If the helper library
        # cannot be imported, link the original report rather than failing the whole cell.
        link, note = report, ""
        optimize, why = _load_takara_optimize()

        if optimize is None:
            note = f"\n\n_Images were not optimized ({why}), so the report may load slowly._"
        else:
            try:
                report_dir = report.path.rsplit("/", 1)[0]
                optimize(src=report, ldata_dst_dir=report_dir)
                link = LPath(report_dir) / (Path(report.path).stem + ".optimized.html")
            except Exception as e:
                note = f"\n\n_Images were not optimized ({e!r}), so the report may load slowly._"

        # Printing the h5ad path is not decoration — it is how the path reaches the next step.
        # Keep it in the same message as the report link so it is on screen whenever the user
        # asks to continue.
        if h5ad is not None:
            h5ad_line = f"Counts matrix for secondary analysis: `{h5ad.path}`\n\n"
        else:
            h5ad_line = (
                "_No `*_anndata.h5ad` found under the run directory — if you continue to "
                "secondary analysis I'll ask you where it is._\n\n"
            )

        w_text_output(
            content=(
                "**Seeker pipeline complete.** "
                f"[Open the QC report](https://console.latch.bio/data/{link.node_id()})\n\n"
                + h5ad_line
                + "Message me when you've looked it over and we'll continue with secondary analysis."
                + note
            ),
            appearance={"message_box": "success"},
            key="seeker_resume_report",
        )
```

`_load_takara_optimize()` is the shared helper defined in `<takara_lib_import>` at the end of this
doc — paste it into the cell above the button. Three notes:

- **A failed import must never cost the user their report link.** `optimize` only shrinks embedded
  images; if it is unavailable the original report still opens. That is why the import is resolved
  through a helper that returns `None` instead of raising.
- The helper locates the library by **verifying `optimize_html_images.py` exists** before putting a
  directory on `sys.path`, rather than trusting a hard-coded path. A `ModuleNotFoundError: No module
  named 'takara.optimize_html_images'` means a *different* `takara` package won the import — the
  helper's purge plus `importlib.invalidate_caches()` is what prevents that.
- **Never construct an output path from a guess.** `<outputs>` records the layout the deployed
  workflow actually writes; the fast path uses it and the suffix search is the safety net.
- **This cell must locate the h5ad, not just the report.** The launch cell no longer binds an
  execution result, so nothing else in the notebook knows where `<sample>_anndata.h5ad` is. Printing
  its path here is what lets `steps/data_loading.md` skip its "ask the user" branch after a pod
  restart. Do not drop it to keep the message short.
- If `iterdir()` is unavailable in the runtime, replace `_by_suffix` with
  `w_ldata_browser(dir=run_dir)` and have the user select the files; everything downstream is
  unchanged.

Both genome sources are always offered: the `w_radio_group` picks `PREBUILT` or `CUSTOM`, and the
matching input swaps in reactively — the prebuilt genome `w_select` for `PREBUILT`, the
`igenomes_base` directory picker for `CUSTOM`. Only the key belonging to the selected source is
passed in `params`.
</example>

<long_running_guidance>
Because `automatic=False`, the user clicks **Launch** after your turn has ended. You are not
running at that moment and cannot post anything to chat, so this message has to be delivered in
**two** places — do both, and never shorten it or drop the pod shutdown advice:

1. **In the launch cell**, as the `w_text_output(...)` inside `if execution is not None:` shown in
   the example above. This is what the user actually sees on click, and it is the only delivery
   that survives the agent's turn ending. Nothing may follow it in the cell that blocks — an
   `await execution.wait()` would withhold everything after it until the pipeline finishes.
2. **In chat, when you present the two cells**, phrased for what is about to happen: tell the user
   that once they click Launch the pipeline runs on Latch compute, and that they may then shut the
   notebook pod down to save cost. In this version, **name the tab** rather than saying "below" —
   the cells are in a tab the notebook did not switch to, so from chat the buttons are not below
   anything. The in-cell version at (1) may keep "below", since it sits next to the button.

The message text:

"The Seeker pipeline is now running on Latch compute and will take some time to finish. It runs independently of this notebook, so you may **shut down the notebook pod while the workflow runs, which stops the notebook compute charges and saves cost**. Shutting the pod down will not interrupt the workflow. You may monitor the progress of the workflow in the workflows executions tab. When the workflow has completed, restart the pod, reopen the notebook, and click **Show my QC report** below — that is all you need to do, and you do not have to message the agent for it."

Never tell the user that you will "resume from where you left off" or that you will pick the run up
automatically. Nothing in Plots can start an agent turn, so that is not true, and it is what leads
users to sit waiting and then interrupt you. Point them at the resume button instead.
</long_running_guidance>

<resuming>
The launch cell does not wait for the pipeline, and you will not be running when it finishes. **The
resume button in cell 3 is the intended path** — it does the whole report step in the kernel without
you. Make sure it is on screen before the user leaves.

If the user does message you after a launch — "continue", "is it done?", "the pipeline finished", or
anything else — treat that as a resume signal and check Latch Data *before* answering:

- **The notebook is not the source of truth for whether the pipeline finished.** The execution runs
  on Latch compute, entirely outside this pod. Never report "the pipeline is still running" because
  a cell looks busy, because `workflow_outputs` is undefined, or because you have no record of a
  completion — none of those are evidence about the execution.
- **Look under `outdir/<execution_name>/`.** Outputs there mean the pipeline finished; an empty or
  missing directory means it is still running or failed, and the user should check the workflows
  executions tab.
- **If kernel state was lost** (pod restarted), do not try to reconstruct `execution` or `res` — they
  are gone and are not needed. Re-run cells 1 and 3; the widget values persist with their `key`s, and
  everything downstream is derived from the Latch Data paths. Re-rendering cell 3 also puts the
  resume button back on screen.
- If the report link has not been rendered yet, do that work yourself rather than telling the user to
  click the button they just bypassed — same steps as cell 3, then continue to
  `steps/view_report.md`'s follow-up question. Do not ask the user to re-confirm that the pipeline
  finished.
- **Never ask the user where the h5ad is.** You launched this run, so its location is derivable:
  `<outdir>/<execution_name>/OUTPUT/<sample>/<sample>_anndata.h5ad`, with the parameters still in
  the widgets (`w_outdir`, `w_execution_name`, `w_sample` — they persist by `key` across a pod
  restart) and cell 3's rendered output as a second source. Find it the same way cell 3 does — fast
  path, then a bounded `_anndata.h5ad` suffix search from the run directory — and hand the resulting
  `LPath` straight to `steps/data_loading.md` step 1b. Fall back to the picker in step 1a **only**
  when that search genuinely comes up empty, and say so when you do, rather than asking as though
  you never had the information.
</resuming>

<takara_lib_import>
Paste this helper into the resume cell, above the button. It resolves the Takara helper library
robustly and **never raises** — a missing library must cost the user image optimization, not their
report link.

```python
import importlib
import sys
from pathlib import Path

# Checked first, in order. If the skill is deployed somewhere else, add that path here.
_TAKARA_HINTS = (
    "/opt/latch/plots-faas/.claude/skills/takara-devkit/lib",
    "/opt/latch/plots-faas/.claude/skills/latch-skills/takara-devkit/lib",
)
# Searched only if no hint matches. Most specific first — an rglob over a large tree is slow.
# `agent_config/context/technology_docs` is deliberately absent: it holds a frozen pre-monorepo
# snapshot of this devkit (see <legacy_technology_docs_path> in SKILL.md) that imports cleanly
# and runs months-old code. It has no optimize_html_images.py, so it would miss anyway — but do
# not add it back as a convenience for other imports.
_TAKARA_SEARCH_ROOTS = (
    "/opt/latch/plots-faas/.claude/skills",
    "/opt/latch/plots-faas",
    "/root",
)


def _find_takara_lib() -> str | None:
    """Directory to place on sys.path so `takara.optimize_html_images` resolves, or None."""
    for hint in _TAKARA_HINTS:
        if (Path(hint) / "takara" / "optimize_html_images.py").is_file():
            return hint
    for root in _TAKARA_SEARCH_ROOTS:
        try:
            hit = next(Path(root).rglob("takara/optimize_html_images.py"), None)
        except Exception:          # unreadable tree
            hit = None
        if hit is not None:
            return str(hit.parent.parent)
    return None


def _load_takara_optimize():
    """Returns (optimize, None) on success or (None, reason) on failure. Never raises."""
    lib = _find_takara_lib()
    if lib is None:
        return None, (
            "takara/optimize_html_images.py was not found under "
            + ", ".join(_TAKARA_SEARCH_ROOTS)
        )

    # Whichever `takara` is imported first pins its __path__ for the rest of the session, so a bare
    # sys.path.insert does nothing: the cached package wins and its submodules are the only ones
    # visible. That is what produces "No module named 'takara.optimize_html_images'" even though
    # `takara` itself imports fine. Drop the cached package AND refresh the path finders.
    for name in [m for m in sys.modules if m == "takara" or m.startswith("takara.")]:
        del sys.modules[name]
    while lib in sys.path:
        sys.path.remove(lib)
    sys.path.insert(0, lib)
    importlib.invalidate_caches()

    try:
        from takara.optimize_html_images import optimize
    except Exception as e:                     # deployed copy missing the module, PIL absent, ...
        return None, f"{e!r} (searched {lib})"

    return optimize, None
```

Two rules this encodes, which apply anywhere in this skill that imports `takara`:

- **Verify before trusting a path.** Check that `optimize_html_images.py` actually exists at a
  location before putting it on `sys.path`. A hard-coded path that is wrong in the deployed
  environment fails silently — `sys.path.insert` of a non-existent directory is a no-op — and the
  import then resolves against some other `takara`.
- **Purge `sys.modules` *and* call `importlib.invalidate_caches()`.** The purge handles a package
  already bound to a different path; `invalidate_caches()` handles the import system's cached
  directory listings, which otherwise keep a newly-added path's contents invisible.
</takara_lib_import>
