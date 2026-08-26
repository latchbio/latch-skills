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
- **output_directory** (`LatchOutputDir`, **required**) — Directory on Latch where the concatenated file will be saved. Must be provided by the user. Ask for it with a `w_ldata_picker` (`file_type="dir"`), not as free text, rendered in the same message as the other parameters you are collecting in chat; prefill `default=` with a directory the user chose earlier in this session and name it in chat, and offer no default if there is none. Both runs (R1 and R2) go to the same directory — ask once. See "Asking for an output directory" in `SKILL.md`.
- **output_filename** (`str`, **required**) — Name for the output file. Must end in `.fastq.gz` or `.fq.gz`. Use a descriptive name that makes clear whether this is R1 or R2 (e.g. `sampleA_merged_R1.fastq.gz`).
</parameters>

<outputs>
A single concatenated `.fastq.gz` file written to `output_directory/output_filename`.

After both runs complete, feed the merged R1 file as `fastq_cb` (Trekker) or `fastq_1` (Seeker), and the merged R2 file as `fastq_tags` (Trekker) or `fastq_2` (Seeker).
</outputs>

<instructions>
**Step 1 — Collect all files**

Ask the user to provide all R1 files and all R2 files before doing anything else. Do not proceed until both lists are in hand.

**Step 2 — Pair and sort**

Match each R1 file to its corresponding R2 file. Use the lane identifier embedded in the filename (e.g. `_L001_`, `_L002_`) as the sort key. Sort all pairs together by that key in ascending order. If no lane identifier is present, sort lexicographically by filename and note the assumption.

**Step 3 — Show confirmation table**

Display the proposed pairing to the user as a table before submitting any job:

```
Order | R1 file                         | R2 file
------|---------------------------------|---------------------------------
1     | sample_L001_R1_001.fastq.gz     | sample_L001_R2_001.fastq.gz
2     | sample_L002_R1_001.fastq.gz     | sample_L002_R2_001.fastq.gz
...
```

Then ask:
> "Does this pairing and order look correct? If not, describe any corrections (e.g. 'swap rows 2 and 3' or 'row 1 R2 should be `sample_L001_R2_002.fastq.gz`') and I'll update before proceeding."

Repeat — update the table and ask again — until the user confirms the order is correct. Do not submit either run until confirmation is given.

**Step 4 — Execute both runs in parallel**

Submit the R1 and R2 runs simultaneously. Use the same row order from the confirmed table for both `fastq_files` lists. Await both executions together before reporting results.
</instructions>

<example>
```python
import asyncio
from latch.types import LatchFile, LatchDir

# resolve takara/lib per SKILL.md "Helper library usage", then:
from takara.launch import LaunchStatus, launch_workflow_once

WF_NAME, VERSION = "wf.__init__.concatenate", "1.1.9-e2ce84"
OUTPUT_DIR = "latch://..."   # required — set by user

# Run 1: concatenate all R1 files
params_r1 = {
    "fastq_files": [
        LatchFile("latch://..."),   # first R1 file
        LatchFile("latch://..."),   # second R1 file
        LatchFile("latch://..."),   # third R1 file (add as many as needed)
    ],
    "output_directory": LatchDir(OUTPUT_DIR),        # required
    "output_filename": "sample_merged_R1.fastq.gz",  # required — must end in .fastq.gz or .fq.gz
}

# Run 2: concatenate all R2 files (submitted in parallel with Run 1)
params_r2 = {
    "fastq_files": [
        LatchFile("latch://..."),   # first R2 file
        LatchFile("latch://..."),   # second R2 file
        LatchFile("latch://..."),   # third R2 file (add as many as needed)
    ],
    "output_directory": LatchDir(OUTPUT_DIR),        # required
    "output_filename": "sample_merged_R2.fastq.gz",  # required — must end in .fastq.gz or .fq.gz
}

# Distinct key_prefixes: these are two runs of the SAME workflow, so they need separate launch
# records. Their params differ (different files, different output_filename), so the guard sees them
# as two genuine runs and does not treat the second as a duplicate of the first.
res_r1 = launch_workflow_once(
    wf_name=WF_NAME, version=VERSION, params=params_r1,
    label="Concatenate R1 FASTQs", key_prefix="fastq_concat_r1",
    output_dir=OUTPUT_DIR, automatic=True,
)
res_r2 = launch_workflow_once(
    wf_name=WF_NAME, version=VERSION, params=params_r2,
    label="Concatenate R2 FASTQs", key_prefix="fastq_concat_r2",
    output_dir=OUTPUT_DIR, automatic=True,
)

# Await whichever actually launched. A BLOCKED_RUNNING result means that half is already going —
# report it, do not relaunch, and do not re-run this cell to check on it.
pending = [r.execution for r in (res_r1, res_r2) if r.status is LaunchStatus.LAUNCHED]
if pending:
    results = await asyncio.gather(*(e.wait() for e in pending))
for r in (res_r1, res_r2):
    if r.status is LaunchStatus.BLOCKED_RUNNING:
        print(r.existing.describe())
```
</example>
