<goal>
Launch BANSkY spatial domain detection on MERFISH AnnData.
</goal>

<parameters>
- **input_file** → `LatchFile`  
  - H5AD file prepared for BANSkY (must contain `adata.obsm["X_spatial"]`).  
  - User selects a filename and LData location for saving before workflow launch.

- **run_name** → `str`  
  - Identifier for this BANSkY run (e.g., `"banksy_run_1"`).

- **output_dir** → `LatchDir`  
  - Directory on Latch Data where BANSkY results will be written.

- **lambda_list** → `str`  
  - A comma-separated list of lambda values (e.g., `"0.1,0.25,0.5"`).  
  - Exposed using lplots widgets.
</parameters>

<outputs>
- BANSkY domain detection results, including domain assignments and spatial embeddings written under:
  `{output_dir}/{run_name}/`
</outputs>

<example>
```python
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir

params = {
    "input_file": LatchFile("latch:///my_merfish/processed_for_banksy.h5ad"),
    "run_name": "banksy_demo",
    "output_dir": LatchDir("latch:///banksy_outputs"),
    "lambda_list": "0.5,1.0",
}

w = w_workflow(
    wf_name="wf.__init__.domain_detection_wf",
    key="banksy_workflow_run_1",
    version=None,
    automatic=True,
    label="Run BANSkY Domain Detection",
    params=params,
)

execution = w.value
if execution:
    res = await execution.wait()
```
</example>