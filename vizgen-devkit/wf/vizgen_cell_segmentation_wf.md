<goal>
Run Vizgen MERFISH cell segmentation from raw images.
</goal>

<parameters>
- **Image Directory** → `image_directory` (`LatchDir`)
  - Directory containing mosaic TIF files (`mosaic_*_z*.tif`). Typically `{dataset_dir}/region_*/images/`

- **Micron to Mosaic Transform** → `micron_to_mosaic_transform` (`LatchFile`)
  - CSV transformation file. Typically `{dataset_dir}/region_*/images/micron_to_mosaic_pixel_transform.csv`

- **Detected Transcripts** → `detected_transcripts` (`LatchFile`)
  - CSV with transcript coordinates. Typically `{dataset_dir}/region_*/detected_transcripts.csv`

- **Algorithm JSON** → `cell_segmentation_algorithm` (`LatchFile`)
  - Create new `algorithm.json` from user input. Ignore existing files.
  - **Use lplots widgets for all user interactions.**

  **Steps:**
  1. Parse `manifest.json` from `image_directory`. Extract z-indexes, stains, mosaic properties. Display summary.
  
  2. **MANDATORY: ALWAYS ask user for number of segmentation tasks FIRST**
     - Prompt: "How many segmentation tasks do you want to configure?"
     - Store as `N` (integer)
     - Do NOT proceed to task configuration until `N` is obtained
  
  3. **For each task (1..N), configure based on its selected algorithm:**
     - Show current task number (e.g., "Configuring task 1 of N")
     - Select `z_layers` (default: all)
     - **FIRST for this task**: Select algorithm for THIS task: `"Cellpose"`, `"Cellpose2"` (default), or `"Watershed"`
       - Each task can have a DIFFERENT algorithm
       - Algorithm selection for THIS task determines which parameter widgets appear for THIS task
     - Select channels for `task_input_data` (e.g., DAPI, PolyT)
     - Configure preprocessing for each channel (CLAHE normalization)
     
     **Then configure THIS task based on its selected algorithm:**
     
     **If THIS task uses Cellpose:**
     - Model: `"cyto2"` or `"nuclei"` (default: cyto2)
     - `version`: "latest" (default)
     - **Do NOT show channel_map widgets** (Cellpose doesn't use it)
     - `segmentation_properties`: `{model, model_dimensions: "2D", custom_weights: null, version: "latest"}`
     - Collect: `nuclear_channel`, `entity_fill_channel`, `diameter`, `flow_threshold`, `mask_threshold`, `minimum_mask_size`
     
     **If THIS task uses Cellpose2:**
     - Model: `"cyto2"` or `"nuclei"` (default: cyto2)
     - **Show channel_map widgets**: Map channels to RGB
       - For cyto2: `{red: "PolyT", green: "", blue: "DAPI"}` (example)
       - For nuclei: `{red: "", green: "", blue: "DAPI"}`
     - **Do NOT show version widget** (Cellpose2 doesn't use it)
     - `segmentation_properties`: `{model, model_dimensions: "2D", custom_weights: null, channel_map: {red, green, blue}}`
     - Collect: `nuclear_channel`, `entity_fill_channel`, `diameter`, `flow_threshold`, `cellprob_threshold`, `minimum_mask_size`
     
     **If THIS task uses Watershed:**
     - Collect Watershed-specific parameters
     - Use Watershed-specific `segmentation_properties` structure
     
     - For all algorithms, collect `polygon_parameters` for THIS task:
       - `simplification_tol` (default: 2), `smoothing_radius` (default: 10), `minimum_final_area` (default: 500)
  
  4. Use lplots signals for dynamic updates:
     - When `N` changes: Regenerate task configuration list (all tasks must be reconfigured)
     - When algorithm family changes for a specific task: Dynamically show/hide widgets for THAT task only
       - Cellpose: Show `mask_threshold`, `version`; Hide `cellprob_threshold`, `channel_map`
       - Cellpose2: Show `cellprob_threshold`, `channel_map`; Hide `mask_threshold`, `version`
     - Each task's configuration is independent and based on its own algorithm selection
  
  5. Save to LData:
     - Get filename via widget
     - Use `w_ldata_picker` → **always retrieve**: `picker.value.path` (not widget object)
     - Write JSON to `f"{picker.value.path}/{filename}"`
     - Wrap as `LatchFile(algorithm_path)`

  **Templates:** `wf/templates/algorithm_cellpose.json`, `wf/templates/algorithm_cellpose2.json`

- **Output directory** → `output_directory` (`LatchOutputDir`)
  - Default: `LatchOutputDir("latch://38438.account/vizgen_cellsegmentation_outputs")`
  - Use `w_ldata_picker` → `LatchOutputDir(picker.value.path)`

- **Run name** → `run_name` (`str`)

- **Optional** (defaults if not provided):
  - `tile_size` (int, default: 2400)
  - `tile_overlap` (int, default: 200)
  - `num_process` (int, default: 8)
  - `update_vzg` (bool, default: False)
  - `vzg_file` (`LatchFile`, required if `update_vzg=True`)

- **Workflow launch:**
  - `wf_name="wf.__init__.vizgen_cell_segmentation_wf"`
  - `automatic=True`
  - Unique `key` per run
  - `await execution.wait()` before proceeding
</parameters>

<outputs>
</outputs>

<example>
```python
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir, LatchOutputDir

params = {
    "image_directory": LatchDir("latch://.../region_0/images"),
    "micron_to_mosaic_transform": LatchFile("latch://.../micron_to_mosaic_pixel_transform.csv"),
    "detected_transcripts": LatchFile("latch://.../detected_transcripts.csv"),
    "cell_segmentation_algorithm": LatchFile("latch://.../algorithm.json"),
    "output_directory": LatchOutputDir("latch://.../outputs"),
    "run_name": "run_1",
    "tile_size": 2400,
    "tile_overlap": 200,
    "num_process": 8,
    "update_vzg": False,
}

w = w_workflow(
    wf_name="wf.__init__.vizgen_cell_segmentation_wf",
    key="vizgen_cellsegmentation_run_1",
    version=None,
    params=params,
    automatic=True,
    label="Run Cell Segmentation Workflow",
)
execution = w.value
if execution is not None:
    res = await execution.wait()
    if res and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        workflow_outputs = list(res.output.values())
```
</example>
