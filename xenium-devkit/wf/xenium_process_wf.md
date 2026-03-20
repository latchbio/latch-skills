<goal>
Launch Xenium preprocessing workflow.
</goal>

<parameters>
- `input_file` (`LatchDir`): Path to the Xenium output directory (e.g. the `*_outs` folder) containing the raw Xenium data to be preprocessed.
- `run_name` (`str`): Name for this run; used to create a subdirectory under `output_directory` where outputs will be written.
- `output_directory` (`LatchDir`): Base directory where preprocessed results will be stored. Outputs are written to `{output_directory}/{run_name}/`.
</parameters>

<outputs>
- Preprocessed outputs written under:
  `{output_directory}/{run_name}/`
</outputs>

<example>
```python
from lplots.widgets.workflow import w_workflow
from latch.types import LatchDir

params = {
    "input_file": LatchDir("latch://38438.account/Scratch/xenium/Input/Xenium_V1_FFPE_TgCRND8_17_9_months_outs"),
    "run_name": "my_run",
    "output_directory": LatchDir("latch:///Xenium_Preprocessing"),
}

w = w_workflow(
    wf_name="wf.__init__.xenium_preprocess_workflow",
    version=None,
    label="Launch Data Preparation Workflow",
    params=params,
    automatic=True,
)
execution = w.value
if execution is not None:
    res = await execution.wait()

    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        workflow_outputs = list(res.output.values())
```
</example>
