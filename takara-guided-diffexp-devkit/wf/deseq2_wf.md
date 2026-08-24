# Launching `takara_de_deseq2`

**Never block on `await execution.wait()`.** DESeq2 runs on Latch compute,
independently of the notebook pod. A cell that awaits it parks indefinitely and
does not survive a pod restart — and nothing in Plots can start an agent turn,
so completion is detected by reading Latch Data, not by polling status.

**Launch cell:**

```python
deseq2 = w_workflow(
    label="Run DESeq2",
    wf_name="takara_de_deseq2.workflow.deseq2",
    params={"counts_file": "{{RUN_DIR}}/confirmed/counts.csv",
            "coldata_file": "{{RUN_DIR}}/confirmed/coldata_confirmed.csv",
            "run_dir": "{{RUN_DIR}}"},
    automatic=True,
    key="deseq2_launch",
)
```

**Resume cell:**

```python
import json
from pathlib import Path

from latch.ldata.path import LPath
from lplots.widgets.button import w_button
from lplots.widgets.text import w_text_output


def lread(lp):
    """Download an LPath to a local temp file and return its text."""
    p = Path(f"/tmp/{lp.node_id()}{Path(lp.name() or '').suffix}")
    lp.download(p, cache=True)
    return p.read_text()


check = w_button(label="Show DESeq2 results")
out = LPath("{{RUN_DIR}}") / "deseq2"

if check.value:
    if (out / "results.csv").exists():
        summary = json.loads(lread(out / "de_metrics.json"))
    else:
        w_text_output(content="Still running — press again in a minute.")
```

Both cells go in the tab named **4. Differential Expression**. Tell the
user in chat, by that exact tab name, to press **Show DESeq2 results** when the
run finishes. The notebook will not have switched them to it, and a resume
button in an unopened tab is the same as no button at all.

Outputs under `{{RUN_DIR}}/deseq2/`: `results.csv`, `de_metrics.json`,
`volcano.png`, `ma_plot.png`, `heatmap.png`, `sessionInfo.txt`.
