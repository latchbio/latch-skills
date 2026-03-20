<goal>
Launch domain detection workflow on preprocessed Xenium data and visualize detected domains.
</goal>

<parameters>
- `input_file` (`LatchFile`): Path to the preprocessed `.h5ad` file to be used as input for domain detection.
- `run_name` (`str`): Name for this run; used to create a subdirectory under `output_dir` where outputs will be written.
- `output_dir` (`LatchDir`): Base directory where domain detection outputs will be stored.
- `lambda_list` (`str`): Comma-separated list of lambda values to use for domain detection (e.g. `"0.5"`).
</parameters>

<outputs>
- Domain detection outputs written under:
  `{output_dir}/{run_name}/`
- One or more `.h5ad` files containing domain labels in `obs` (e.g. `labels_scaled_gaussian_*`).
</outputs>

<example>
```python
from pathlib import Path
from latch.ldata.path import LPath

if "Spatial" in adata.obsm:
    adata.obsm["X_spatial"] = adata.obsm["Spatial"]

output_h5ad_path = "/tmp/xenium_processed_for_domain_detection.h5ad"
adata.write_h5ad(output_h5ad_path)

output_lpath = LPath("latch:///xenium/analysis_output/xenium_processed_for_domain_detection.h5ad")
local_path = Path(output_h5ad_path)
output_lpath.upload_from(local_path)

from latch.types import LatchDir, LatchFile
from lplots.widgets.workflow import w_workflow

params = {
    "input_file": LatchFile("latch:///xenium/analysis_output/xenium_processed_for_domain_detection.h5ad"),
    "run_name": "my_run",
    "output_dir": LatchDir("latch:///Domain_detection_output"),
    "lambda_list": "0.5",
}

w = w_workflow(
    wf_name="wf.__init__.domain_detection_wf",
    version=None,
    label="Launch Domain Detection Workflow",
    params=params,
    automatic=True,
)

execution = w.value

if execution is not None:
    res = await execution.wait()
    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        workflow_outputs = list(res.output.values())
</example>
