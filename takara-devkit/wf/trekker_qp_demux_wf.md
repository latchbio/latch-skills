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
    "fastq_r1": LatchFile("latch://..."),             # required — set by user
    "fastq_r2": LatchFile("latch://..."),             # required — set by user
    "output_directory": LatchDir("latch://..."),      # required — set by user
    "chemistry": "v3",                                # "v1", "v2", or "v3"
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

# Do NOT `await execution.wait()` here — the partitioner runs for a long time and the user is told
# they may shut the notebook pod down. Check for outputs with the results cell below. See <resuming>.
```

**Resume cell** — generate and run it in the same turn as the launch cell, so the button is on screen
before the user walks away. Clicking it re-runs *this cell in the kernel*; no agent turn is involved,
which matters because nothing in Plots can start one. It reads Latch Data rather than kernel state, so
it also survives a pod restart:
```python
from latch.ldata.path import LPath
from lplots.widgets.button import w_button
from lplots.widgets.text import w_text_output

out_dir = LPath("latch://...")          # the same output_directory passed in params

resume = w_button(label="Check my demultiplexed FASTQs", key="qp_demux_resume")

# reading .value makes this cell reactive — the click re-runs it
if resume.value:
    try:
        fastqs = sorted(p.path for p in out_dir.iterdir() if p.path.endswith(".fastq.gz"))
    except Exception:
        fastqs = []

    if fastqs:
        w_text_output(
            content=(
                f"**Partitioning is complete.** Demultiplexed FASTQs in `{out_dir.path}`:\n\n"
                + "\n".join(f"- `{p}`" for p in fastqs)
                + "\n\nMessage me and I'll set up one Trekker pipeline run per group."
            ),
            appearance={"message_box": "success"},
            key="qp_demux_resume_ready",
        )
    else:
        w_text_output(
            content=(
                f"No demultiplexed FASTQs under `{out_dir.path}` yet, so the run has not finished "
                "writing its outputs. Check the execution's status in the workflows executions tab; "
                "if it is still running, click this button again once it reaches SUCCEEDED. If it "
                "shows FAILED, tell me and I'll look at the logs."
            ),
            appearance={"message_box": "warning"},
            key="qp_demux_resume_pending",
        )
```

Unlike the Seeker and Trekker pipelines, the step *after* partitioning is not self-contained — it
means building a fresh set of Trekker parameter widgets per demultiplexed group. So this button
confirms the FASTQs are ready and tells the user to message the agent; it cannot finish the step on its
own. If `iterdir()` is unavailable in the runtime, browse the directory with
`w_ldata_browser(dir=out_dir)` instead.
</example>

<long_running_guidance>
After launching the workflow execution, display this message to the user **in full** — do not
shorten it or drop the pod shutdown advice:

"The TrekkerQ_P Partitioner is now running on Latch compute and will take some time to finish. It runs independently of this notebook, so you may **shut down the notebook pod while the workflow runs, which stops the notebook compute charges and saves cost**. Shutting the pod down will not interrupt the workflow. You may monitor the progress of the workflow in the workflows executions tab. When the workflow has completed, restart the pod, reopen the notebook, and go to the **TrekkerQ_P Partitioner** tab — the **Check my demultiplexed FASTQs** button is in that tab, and clicking it will confirm the outputs are ready and tell you what happens next."

Because that advice invites the user to shut the pod down, the launch cell must **not** block on
`await execution.wait()` — an await parks the cell in a permanently-running state, binds no result,
and does not survive a pod restart.

Never tell the user that you will "resume from where you left off" automatically. Nothing in Plots can
start an agent turn, so that is not true, and it is what leads users to sit waiting and then interrupt
you. Point them at the resume button instead — and **name the tab it is in**, since this message goes
to chat while the button renders in the workflow's own tab, which the notebook does not switch to. A
resume button the user cannot find is the same as no resume button. See "Telling the user where
results appeared" in `SKILL.md`.
</long_running_guidance>

<resuming>
The launch cell does not wait for the execution, and you will not be running when it finishes. The
resume button is what tells the user their FASTQs are ready; make sure it is on screen before they
leave. When they then message you — "continue", "is it done?", or anything else — treat that as a
resume signal and check Latch Data *before* answering:

- **The notebook is not the source of truth.** The execution runs on Latch compute, outside this pod.
  Never report "the partitioner is still running" because a cell looks busy, because
  `workflow_outputs` is undefined, or because you have no record of it completing — none of those are
  evidence.
- **Check Latch Data.** Per-group `_R1.fastq.gz` / `_R2.fastq.gz` pairs under `output_directory` mean
  the run finished; nothing there means it is still running or failed, and the user should check the
  workflows executions tab.
- **If kernel state was lost** (pod restarted), do not try to reconstruct `execution` or `res` — they
  are gone and are not needed. The demultiplexed FASTQ paths are all that the Trekker pipeline needs.
- Once the FASTQs are present, go straight on to `wf/trekker_pipeline_wf.md`, one execution per
  demultiplexed group. Do not ask the user to re-confirm that the run finished.
</resuming>
