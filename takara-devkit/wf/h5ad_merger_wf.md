<goal>
Merge 2 or more h5ad files into a single spatially-unified h5ad file using the h5ad_merger workflow.
</goal>

<when_to_use>
Two scenarios require this workflow. Determine which applies **before** collecting parameters.

---

**Scenario A — Spatial tile stitching (same biological sample)**

Use when the h5ad files represent adjacent tissue regions captured across multiple tiles from the same biological sample (e.g., two Seeker slides placed side-by-side on the same tissue).

- Run `h5ad_merger_wf` **first**, then proceed to secondary analysis on the merged output.
- The merged h5ad is treated as a single dataset in secondary analysis: normalization, HVG selection, PCA, UMAP, and Leiden clustering are all computed jointly across all tiles.
- A `dataset` column is added to `.obs` recording each cell's tile of origin (the `tile_name` value you provide). This column can be used to color spatial and UMAP plots by tile.
- This is correct because all cells belong to the same biological sample — the tiles are just spatial subdivisions of it.

**Scenario B — Distinct biological samples (e.g., experimental vs control)**

Use when the h5ad files represent separate biological conditions or samples that must be compared.

- Run the full secondary analysis pipeline **independently on each h5ad first** (one complete run per sample).
- After all per-sample secondary analyses are complete, optionally run `h5ad_merger_wf` to stitch the analyzed h5ad files together for **unified spatial visualization**.
- Do **not** merge first — the secondary analysis pipeline does not perform batch correction, so merging distinct samples before analysis would conflate technical variation between samples with biological signal.
- The merged output will contain all per-sample `.obs` columns (clusters, cell types, UMAP embeddings) and a unified `X_offset` spatial coordinate array suitable for visualization.
</when_to_use>

<parameters>
- **h5ad files** → `h5ad_files` (`List[H5AD]`, **required**)
  - One entry per h5ad file to merge. Minimum 2 entries required.
  - Each entry has three fields:
    - `row` (int): grid row for this tile in the 2D spatial layout (rows are numbered from 1).
    - `tile_name` (str): label for this tile — becomes the value in the `dataset` column of the merged `.obs`.
    - `file` (LatchFile): path to the h5ad file on Latch.
  - Tiles in the same row get the same `row` value; the left-to-right order within a row is determined by their position in the list.
  - Examples:
    - Two tiles side-by-side: both get `row=1`
    - Two tiles stacked vertically: first gets `row=1`, second gets `row=2`
    - Four tiles in a 2×2 grid: top-left `row=1`, top-right `row=1`, bottom-left `row=2`, bottom-right `row=2`

- **Output directory** → `output_directory` (`LatchOutputDir`, **required**)
  - Directory on Latch where the merged h5ad will be saved.
  - Must be provided by the user — do not use a default or placeholder value.

- **Output filename** → `output_h5ad` (`str`, **required**)
  - Name for the merged output file. Must end in `.h5ad`.
</parameters>

<outputs>
A single merged h5ad file written to `output_directory/output_h5ad` containing:
- All cells from all input files, with barcodes made unique across tiles if necessary.
- A `dataset` column in `.obs` tracking each cell's tile of origin (value = `tile_name`).
- `X_offset` in `.obsm`: spatially recalculated coordinates positioning all tiles in a unified 2D layout (100-pixel spacing between adjacent tiles).
- All original `.obs` metadata, `.var` gene annotations, and `.obsm` arrays (including `X_spatial`) preserved from the input files.
</outputs>

<instructions>
Confirm which scenario applies (A or B) before collecting parameters.

For Scenario A (tile stitching), collect all parameters and confirm with the user before executing:
> "All parameters are set. Let me know when you're ready to run the H5AD Merger."
Only generate and execute the code cell below once the user confirms.

For Scenario B (distinct samples), run secondary analysis on each h5ad independently first. Return here after all per-sample analyses are complete if the user wants a merged spatial visualization.
</instructions>

<example>
```python
from dataclasses import dataclass
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir

@dataclass
class H5AD:
    row: int
    tile_name: str
    file: LatchFile

params = {
    "h5ad_files": [
        H5AD(
            row=1,
            tile_name="sample_A",           # required — label for this tile (becomes 'dataset' value in .obs)
            file=LatchFile("latch://..."),   # required — path to h5ad file on Latch
        ),
        H5AD(
            row=1,
            tile_name="sample_B",           # required — label for this tile
            file=LatchFile("latch://..."),   # required — path to h5ad file on Latch
        ),
        # add one H5AD entry per additional file to merge
    ],
    "output_directory": LatchDir("latch://..."),  # required — set by user
    "output_h5ad": "merged.h5ad",                 # required — must end in .h5ad
}

w = w_workflow(
    wf_name="wf.__init__.merge_h5ad_wf",
    key="h5ad_merger_run_1",
    version="0.0.7",
    params=params,
    automatic=True,
    label="H5AD Merger",
)
execution = w.value

if execution is not None:
    res = await execution.wait()

    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        # merged h5ad is available at output_directory/output_h5ad
        workflow_outputs = list(res.output.values())
```
</example>
