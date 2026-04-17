<goal>
Concatenate multiple FASTQ.gz files (from the same read direction) into a single file, for use as input to the Trekker or Seeker pipeline
</goal>

<when_to_run>
When the user has multiple R1 **or** R2 FASTQ files for the same sample from a **single reaction sequenced across multiple lanes from a single tile**, run this workflow before Trekker or Seeker. Concatenate all R1 files together in one run, then concatenate all R2 files together in a separate run. Use the concatenated R1 and R2 as inputs to the pipeline.

This workflow supports both Trekker and Seeker inputs.

Note: If the FASTQ files come from **different reactions** (different sample indices) for a Trekker experiment, do not concatenate — run Trekker separately per reaction and use the Trekker Merger workflow afterwards.
</when_to_run>

<parameters>
The workflow accepts an unlimited number of FASTQ files per run. Run it twice — once for all R1 files, once for all R2 files.

- **fastq_files** (`List[LatchFile]`, **required, minimum 2**) — List of `.fastq.gz` or `.fq.gz` files to concatenate. Files are concatenated in the order provided. Use the "Bulk Add Files" feature in the Latch UI to add multiple files at once.
- **output_directory** (`LatchOutputDir`, **required**) — Directory on Latch where the concatenated file will be saved. Must be provided by the user.
- **output_filename** (`str`, **required**) — Name for the output file. Must end in `.fastq.gz` or `.fq.gz`. Use a descriptive name that makes clear whether this is R1 or R2 (e.g. `sampleA_merged_R1.fastq.gz`).
</parameters>

<outputs>
A single concatenated `.fastq.gz` file written to `output_directory/output_filename`.

After both runs complete, feed the merged R1 file as `fastq_cb` (Trekker) or `fastq_1` (Seeker), and the merged R2 file as `fastq_tags` (Trekker) or `fastq_2` (Seeker).
</outputs>

<instructions>
Run the workflow twice — first for R1 files, then for R2 files. Collect all parameters before executing either run. Confirm with the user before executing each run:
> "Ready to concatenate the R1 files. Let me know when you'd like to proceed."
> "Ready to concatenate the R2 files. Let me know when you'd like to proceed."
</instructions>

<example>
```python
# Run 1: concatenate all R1 files
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir

params_r1 = {
    "fastq_files": [
        LatchFile("latch://..."),   # first R1 file
        LatchFile("latch://..."),   # second R1 file
        LatchFile("latch://..."),   # third R1 file (add as many as needed)
    ],
    "output_directory": LatchDir("latch://..."),  # required — set by user
    "output_filename": "sample_merged_R1.fastq.gz",  # required — must end in .fastq.gz or .fq.gz
}

w_r1 = w_workflow(
    wf_name="wf.__init__.concatenate",
    key="fastq_concat_r1_run_1",
    version="1.1.9",
    params=params_r1,
    automatic=True,
    label="Concatenate R1 FASTQs",
)
execution_r1 = w_r1.value

if execution_r1 is not None:
    res_r1 = await execution_r1.wait()

# Run 2: concatenate all R2 files
params_r2 = {
    "fastq_files": [
        LatchFile("latch://..."),   # first R2 file
        LatchFile("latch://..."),   # second R2 file
        LatchFile("latch://..."),   # third R2 file (add as many as needed)
    ],
    "output_directory": LatchDir("latch://..."),  # required — set by user
    "output_filename": "sample_merged_R2.fastq.gz",  # required — must end in .fastq.gz or .fq.gz
}

w_r2 = w_workflow(
    wf_name="wf.__init__.concatenate",
    key="fastq_concat_r2_run_1",
    version="1.1.9",
    params=params_r2,
    automatic=True,
    label="Concatenate R2 FASTQs",
)
execution_r2 = w_r2.value

if execution_r2 is not None:
    res_r2 = await execution_r2.wait()

    if res_r2 is not None and res_r2.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        workflow_outputs = list(res_r2.output.values())
```
</example>
