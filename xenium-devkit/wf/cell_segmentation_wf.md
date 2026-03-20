<goal>
Launch Xenium cell segmentation workflow.
</goal>

<parameters>
- `transcript` (`LatchFile`): Path to the transcript-level input file (e.g. `transcripts.parquet`).
- `tiff` (`LatchFile`): Path to the full-resolution morphology image (`morphology.ome.tif`). Must be the full-resolution image; do not use any file containing `"mip"`.
- `run_name` (`str`): Name for this run; used to create a subdirectory under `output_dir` where outputs will be written.
- `output_dir` (`LatchDir`): Base directory where cell segmentation outputs will be stored.
- `level` (`str` or `int`): Segmentation resolution level (higher values produce finer segmentation).
</parameters>

<outputs>
- Cell segmentation outputs written under:
  `{output_dir}/{run_name}/`
- Updated cell boundary and segmentation artifacts produced by the workflow.
</outputs>

<example>
```python
from latch.types import LatchDir, LatchFile
from lplots.widgets.workflow import w_workflow

params = {
    "transcript": LatchFile("latch:///transcripts.parquet"),
    "tiff": LatchFile("latch:///morphology.ome.tif"),
    "run_name": "my_run",
    "output_dir": LatchDir("latch:///cell_resegmentation_output"),
    "level": "5",
}

w = w_workflow(
    wf_name="wf.__init__.xenium_cell_segmentation_workflow",
    version=None,
    label="Launch Cell Segmentation Workflow",
    params=params,
    automatic=True,
)

execution = w.value
</example>
