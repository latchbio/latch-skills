# Launching `takara_de_qc`

Short stage, but still use a resume cell rather than blocking.

**Launch cell:**

```python
qc = w_workflow(
    label="Run sample quality check",
    wf_name="takara_de_qc.workflow.qc",
    params={"counts_file": "{{RUN_DIR}}/confirmed/counts.csv",
            "coldata_file": "{{RUN_DIR}}/confirmed/coldata_confirmed.csv",
            "run_dir": "{{RUN_DIR}}"},
    automatic=True,
    key="qc_launch",
)
```

**Resume cell** (separate cell — this is what survives a pod restart):

```python
import json
from pathlib import Path

from latch.ldata.path import LPath
from lplots.widgets.button import w_button
from lplots.widgets.plot import w_plot


def lread(lp):
    """Download an LPath to a local temp file and return its text."""
    p = Path(f"/tmp/{lp.node_id()}{Path(lp.name() or '').suffix}")
    lp.download(p, cache=True)
    return p.read_text()


check = w_button(label="Show QC results")
out = LPath("{{RUN_DIR}}") / "qc"

if check.value and (out / "qc_metrics.json").exists():
    metrics = json.loads(lread(out / "qc_metrics.json"))
```

Both cells go in the tab named **3. Quality Check**. Tell the user in
chat, by that exact tab name, to press **Show QC results** when the run
finishes — the notebook does not switch them to it.

Outputs under `{{RUN_DIR}}/qc/`: `pca.png`, `sample_correlation.png`,
`qc_metrics.json`.
