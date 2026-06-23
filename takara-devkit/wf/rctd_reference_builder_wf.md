<goal>
Convert one chosen single-cell reference into an RCTD-compatible spacexr `Reference` `.rds`. The input is a single reference — a `.h5ad` or `.rds` file (attached from LData) **or** a download URL to one. The output is a spacexr `Reference` `.rds` ready to pass to `wf/rctd_wf.md`.
</goal>

<scope>
This workflow is a **pure converter** (resolve → standardize → build → validate → save). It does **not** search any atlas. Deciding *which* reference to use — interpreting the user's tissue, searching CELLxGENE / Tabula Sapiens / Allen / GEO / TOME / others, presenting candidates, and disambiguating — happens conversationally in `steps/rctd.md` **before** this workflow is launched. Arrive here only once a single reference (file or URL) is chosen.

Why a dedicated workflow rather than converting inline: the RCTD reference must be an R-serialized spacexr `Reference` object built under the **same pinned Seurat 4.4.0 / SeuratObject 4.1.4** stack the RCTD image uses. The Plots notebook is a Python kernel with no R/spacexr, and web references ship as AnnData or Seurat v5 (which 4.4.0 cannot deserialize). This workflow rebuilds the object under the RCTD image's R stack to emit a version-compatible object regardless of the original format.
</scope>

<parameters>
Provide **exactly one** reference source (`reference_file` or `reference_url`):
- **`run_name`** (`str`, **required**) — Names the run and output subdirectory. No spaces.
- **`reference_file`** (`LatchFile`, optional) — A reference attached from LData: an AnnData (`.h5ad`) or an R object (`.rds` — a spacexr `Reference` or a Seurat object). Use this for user-attached references.
- **`reference_url`** (`str`, optional) — A direct download URL to a `.h5ad` or `.rds`. The workflow downloads it in compute (robust for large atlases). Use this for references you found on the web (CELLxGENE/TOME/MOCA/etc.) or a URL the user pasted. The URL **path** must end in `.h5ad`/`.h5`/`.rds` (a trailing `?signed-query-string` is fine); if a source only offers an extension-less link (e.g. some figshare `ndownloader` links), have the user download and attach it via `reference_file` instead.
- **`cell_type_column`** (`str`, default `"cell_type"`) — The cell-type column: an `.obs` column for `.h5ad`, or a `meta.data` column for a Seurat `.rds`. CELLxGENE uses `cell_type`. If it isn't found, the builder logs the available columns so you can correct it and relaunch.
- **`max_cells_per_type`** (`int`, default `1000`) — Per-cell-type downsample cap (controls RCTD memory). Each type is randomly downsampled to at most this many cells.
- **`min_cells_per_type`** (`int`, default `25`) — Cell types with fewer cells than this are dropped (RCTD needs a minimum per type).
- **`output_directory`** (`LatchOutputDir`, **required**) — Latch directory for outputs. The reference lands in `output_directory/<run_name>/`.

Notes:
- The file type is detected by extension: `.h5ad`/`.h5` → AnnData path (standardized in Python, then built in R); `.rds` → read directly in R (a spacexr `Reference` is re-validated; a Seurat object has its counts + `cell_type_column` extracted). A Seurat **v5** `.rds` cannot be read by SeuratObject 4.1.4 — if that fails, ask the user for a `.h5ad` instead.
- For `.h5ad`, the builder auto-picks the rawest counts (`.layers['counts']` → `.raw.X` → `.X`) and a gene-symbol var column when present.
</parameters>

<outputs>
Written to `output_directory/<run_name>/`:
- `<run_name>_reference.rds` — the spacexr `Reference` object. **This is the file to pass as `reference_data` to `wf/rctd_wf.md`.**
- `<run_name>_reference_summary.txt` — per-cell-type counts, gene count, and the source (filename or URL).
- `<run_name>_reference_celltypes.png` — bar plot of cells per cell type after curation.
</outputs>

<instructions>
Confirm the resolved source and cell-type column with the user before launching, echoing them back:
> "I'll convert this reference into an RCTD-compatible object: source=<file or URL>, cell-type column=<cell_type_column>, capped at <max_cells_per_type> cells/type. Ready?"

Only generate and execute the code cell once the user confirms. After it completes, hand `<run_name>_reference.rds` to `wf/rctd_wf.md` as `reference_data`.

> ⚠️ Confirm the registered `wf_name`/`version` against the Latch workflows registry before launching (the reference-builder is a separate registration from RCTD).
</instructions>

<example>
```python
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir

params = {
    "run_name": "",                                  # required — no spaces
    # Provide exactly ONE of the next two:
    "reference_url": "https://.../reference.h5ad",    # a .h5ad/.rds URL you found, or the user pasted
    # "reference_file": LatchFile("latch://..."),     # a user-attached .h5ad/.rds in LData
    "cell_type_column": "cell_type",                 # confirm for non-CELLxGENE sources / user files
    "max_cells_per_type": 1000,
    "min_cells_per_type": 25,
    "output_directory": LatchDir("latch://..."),     # required — set by user
}

w = w_workflow(
    wf_name="wf.__init__.rctd_reference_builder_wf",  # confirm against the registered workflow
    key="rctd_ref_builder_run_1",
    version="0.2.0",                                  # confirm against the registered version
    params=params,
    automatic=True,
    label="RCTD Reference Builder",
)
execution = w.value

if execution is not None:
    res = await execution.wait()

    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        # <run_name>_reference.rds is under output_directory/<run_name>/
        workflow_outputs = list(res.output.values())
```
</example>

