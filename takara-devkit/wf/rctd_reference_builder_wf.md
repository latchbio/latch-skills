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
- **`reference_file`** (`LatchFile`, optional) — A reference from LData: an AnnData (`.h5ad`) or an R object (`.rds` — a spacexr `Reference` or a Seurat object). Use this for user-supplied references, whether they picked it with a `w_ldata_picker` (`file_type="file"`) or attached it with the attach button.
- **`reference_url`** (`str`, optional) — A direct download URL to a `.h5ad` or `.rds`. The workflow downloads it in compute (robust for large atlases). Use this for references you found on the web (CELLxGENE/TOME/MOCA/etc.) or a URL the user pasted. The URL **path** must end in `.h5ad`/`.h5`/`.rds` (a trailing `?signed-query-string` is fine); if a source only offers an extension-less link (e.g. some figshare `ndownloader` links), have the user download it to LData and supply it via `reference_file` instead — either by selecting it in a `w_ldata_picker` you render or with the attach button in the Agent interface (or by providing its Latch Data path).
- **`cell_type_column`** (`str`, default `"cell_type"`) — The cell-type column: an `.obs` column for `.h5ad`, or a `meta.data` column for a Seurat `.rds`. CELLxGENE uses `cell_type`. If it isn't found, the builder logs the available columns so you can correct it and relaunch.
- **`max_cells_per_type`** (`int`, default `1000`) — Per-cell-type downsample cap (controls RCTD memory). Each type is randomly downsampled to at most this many cells.
- **`min_cells_per_type`** (`int`, default `25`) — Cell types with fewer cells than this are dropped (RCTD needs a minimum per type).
- **`output_directory`** (`LatchOutputDir`, **required**) — Latch directory for outputs. The reference lands in `output_directory/<run_name>/`.

Notes:
- The file type is detected by extension: `.h5ad`/`.h5` → AnnData path (standardized in Python, then built in R); `.rds` → read directly in R (a spacexr `Reference` is re-validated; a Seurat object has its counts + `cell_type_column` extracted). A Seurat **v5** `.rds` cannot be read by SeuratObject 4.1.4 — if that fails, ask the user for a `.h5ad` instead — via a `w_ldata_picker`, the attach button in the Agent interface, or its Latch Data path.
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

After it completes, hand `<run_name>_reference.rds` to `wf/rctd_wf.md` as `reference_data` — derive
that path from the parameters you already have rather than asking the user for it again.

**Collect `output_directory` and `run_name` in chat, before you generate anything.** Do not render a
picker for them and then end your turn — nothing in Plots can start an agent turn, so the user fills
the picker in, nothing happens, and after a few minutes they conclude you are stuck and interrupt
you. That is a real failure this step has produced. If you do render a picker (because the user
prefers browsing to typing), put it in the **same cell** as the launch button so their selection arms
a click rather than waiting on a turn that will never come. See "Requesting files from the user" in
`SKILL.md`.

> ⚠️ Confirm the registered `wf_name`/`version` against the Latch workflows registry before launching (the reference-builder is a separate registration from RCTD). Do that lookup in cell 1, which cannot launch anything.

Generate **two cells** — resolve, then launch. The split exists because the launch cell fires an
execution every time it runs, and in Plots editing a cell runs it; keeping the `wf_name` lookup and
the parameter fixes in a cell with no `w_workflow` in it means a retry costs nothing. The full
reasoning is in the `<launch_discipline>` block of `wf/rctd_wf.md`, and it applies here too.
</instructions>

<example>
**Cell 1, resolve and validate — cannot launch anything.** Every retry lives here.
```python
from latch.types import LatchFile, LatchDir

WF_NAME = "wf.__init__.rctd_reference_builder_wf"  # confirm against the registered workflow
VERSION = "0.2.0-74dbff"                           # confirm against the registered version
RUN_NAME = ""                                      # required — no spaces
OUTPUT_DIR = "latch://..."                         # required — from the user, collected in chat

params = {
    "run_name": RUN_NAME,
    # Provide exactly ONE of the next two:
    "reference_url": "https://.../reference.h5ad",    # a .h5ad/.rds URL you found, or the user pasted
    # "reference_file": LatchFile("latch://..."),     # a user-attached .h5ad/.rds in LData
    "cell_type_column": "cell_type",                 # confirm for non-CELLxGENE sources / user files
    "max_cells_per_type": 1000,
    "min_cells_per_type": 25,
    "output_directory": LatchDir(OUTPUT_DIR),        # required
}

print("WORKFLOW PARAMETERS:")
for k, v in params.items():
    print(f"  {k}: {v}")

assert RUN_NAME and " " not in RUN_NAME, "run_name is required and must not contain spaces"
assert ("reference_url" in params) != ("reference_file" in params), "provide exactly one source"
```

**Cell 2, launch.** This workflow is short, so the in-turn `await` is fine — but only when the guard
actually launched something.
```python
# resolve takara/lib per SKILL.md "Helper library usage", then:
from takara.launch import LaunchStatus, launch_workflow_once

res = launch_workflow_once(
    wf_name=WF_NAME,
    version=VERSION,
    params=params,
    label="RCTD Reference Builder",
    key_prefix="rctd_ref_builder",   # key is derived — do NOT pass a hand-written key
    run_name=RUN_NAME,
    output_dir=OUTPUT_DIR,
    automatic=True,
)
print(res.status.value, res.message)

reference_rds = None
if res.status is LaunchStatus.LAUNCHED:
    done = await res.execution.wait()

    if done is not None and done.status == "SUCCEEDED":
        # <run_name>_reference.rds is under output_directory/<run_name>/. This path is exactly what
        # wf/rctd_wf.md takes as `reference_data` — hand it over, do not re-ask the user for it.
        reference_rds = f"{OUTPUT_DIR.rstrip('/')}/{RUN_NAME}/{RUN_NAME}_reference.rds"
        workflow_outputs = list(done.output.values())
    elif done is not None:
        print(f"Reference build {done.status} — read the execution logs before relaunching.")
elif res.status is LaunchStatus.BLOCKED_RUNNING:
    # Already building. Do not relaunch, and do not re-run this cell to check on it.
    print(res.existing.describe())
```

If the build fails on a wrong `cell_type_column`, the workflow logs the available columns. Correct it
in **cell 1**, then re-run cell 2 — the changed parameter gives the launch a new fingerprint, so the
guard treats it as the genuinely new run that it is.
</example>

