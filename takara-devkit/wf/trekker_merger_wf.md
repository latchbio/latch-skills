<goal>
Merge Trekker pipeline outputs from multiple single-nuclei reactions into a single combined output
</goal>

<parameters>
- **Trekker output folders** → `trekker_output` (`List[TrekkerOutput]`, **required**)
  - One entry per Trekker pipeline run (reaction) to be merged.
  - Each entry has two fields:
    - `sample` (`str`): The `sample_ID` used when the Trekker pipeline was run for that reaction.
    - `outdir` (`LatchDir`): Path to the Trekker output directory for that reaction. Must contain:
      - `intermediates/{sample_ID}_seurat_spatial.rds`
      - `{sample_ID}_summary_metrics.csv`
  - Collect one entry for each reaction from the user before proceeding.

- **New merged sample ID** → `sample_ID` (`str`, **required**)
  - Prefix used to name the merged output files.
  - Must not contain `.` or spaces.

- **New merged output directory** → `output_directory` (`LatchOutputDir`, **required**)
  - Directory on Latch where the merged results will be saved.
  - Must be provided by the user — do not use a default or placeholder value.
</parameters>

<outputs>
The merged output is written to `output_directory/{sample_ID}/`.
</outputs>

<instructions>
**Tile ID grouping — check before collecting parameters:**
If the user is merging outputs from multiple Trekker pipeline executions that used different tile IDs, do NOT merge all outputs into one run. Instead:
- Group the outputs by `tile_id`.
- Run a separate Trekker Merger for each group, merging only the outputs that share the same tile ID.
- Each merger run requires its own `sample_ID` (the merged name for that tile) and its own `output_directory`.
- Inform the user of this grouping and collect parameters for each merger run before proceeding.

If all outputs share the same tile ID, a single merger run covering all outputs is likely correct.

After collecting all required parameters, confirm with the user before executing:
> "All parameters are set. Let me know when you're ready to run the Trekker Merger."
Only generate and execute the code cell below once the user confirms.
</instructions>

<example>
```python
from dataclasses import dataclass
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir

@dataclass
class TrekkerOutput:
    sample: str
    outdir: LatchDir

params = {
    "trekker_output": [
        TrekkerOutput(
            sample="reaction1_sample_id",              # required — sample_ID from Trekker run
            outdir=LatchDir("latch://..."),            # required — Trekker output dir for this reaction
        ),
        TrekkerOutput(
            sample="reaction2_sample_id",              # required — sample_ID from Trekker run
            outdir=LatchDir("latch://..."),            # required — Trekker output dir for this reaction
        ),
        # add one TrekkerOutput entry per reaction to merge
    ],
    "sample_ID": "",                                   # required — merged output prefix (no '.' or spaces)
    "output_directory": LatchDir("latch://..."),       # required — set by user
}

w = w_workflow(
    wf_name="trekker_merger",
    key="trekker_merger_run_1",
    version="1.4.6-0eab98",
    params=params,
    automatic=True,
    label="Trekker Merger",
)
execution = w.value

if execution is not None:
    res = await execution.wait()

    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        # inspect workflow outputs for downstream analysis
        workflow_outputs = list(res.output.values())
```
</example>
