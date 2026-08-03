<goal>
Load raw data into memory, display to user and check dimensions.
</goal>

<method>
### Step 1a — Get the H5AD file

If you do not already have the source H5AD's `LPath` (e.g. this is a fresh Secondary Analysis / Visualization entry rather than a direct continuation from a just-completed primary pipeline run), offer the user both input routes: render a `w_ldata_picker` for the file **and** tell them they can instead use the **attach button in the Agent text interface**. Use whichever they supply first.

```python
from lplots.widgets.ldata import w_ldata_picker

h5ad_picker = w_ldata_picker(label="H5AD file", file_type="file", key="h5ad_input")
```

The picker returns an `LPath` at `.value` (check for `None` before using it) — that is the same `LPath` used for `download(...)` and `sync_to` below. If neither route works, fall back to asking the user for its Latch Data path directly.

### Step 1b — Load and view

Use `w_h5` to show the user the spatial coordinates. Open it with `sync_to` pointed at the source H5AD's `LPath` so that any edits made in the viewer during this session (including a later image alignment, see `steps/image_overlay.md`) are persisted back to the file rather than lost when the session ends:

```python
from pathlib import Path
import anndata as ad
from latch.ldata.path import LPath
from lplots.widgets.h5 import w_h5

h5ad_path = LPath("latch://.../results/sample.h5ad")

local_h5ad = Path("/tmp") / h5ad_path.name()
h5ad_path.download(local_h5ad, cache=True)

# Load in memory — NOT backed='r'. Confirmed with Latch engineering: sync_to writes by
# serializing the Python AnnData object and uploading it to the LPath, and backed='r' is
# read-only so it cannot be the write channel. A backed handle here silently breaks the
# image-alignment persistence in steps/image_overlay.md. Hand the viewer the same object
# that analysis modifies.
#
# This does mean the counts matrix is resident for the whole session. On an 8–32 GB pod a
# 3–4B read Seeker dataset is a real fraction of that, so check before loading rather than
# discovering it as a stall (see <memory_check> below).
adata = ad.read_h5ad(local_h5ad)

viewer = w_h5(
    label="Review Takara H5AD",
    ann_data=adata,
    sync_to=h5ad_path,
)
```

Once the data is loaded and confirmed, **always ask the user whether they have an H&E or other pathology image of the tissue they'd like to overlay** — proceed to `steps/image_overlay.md` if yes.

### Step 1c — Point the user at the viewer's tab

Name the tab the viewer opened in, in the same chat message that reports the dimensions — see
`<new_tab_notice>` below for the wording.
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- Ensure ~70k–90k beads for Seeker 3x3 or ~0.8–1.1M beads for Seeker 10x10
- Ensure there are ~30K gene features
- The AnnData handed to downstream steps is in memory (`adata.isbacked is False`) — `sync_to` cannot write back from a backed handle, so a backed object breaks image-alignment persistence
- The available-RAM check ran and the H5AD comfortably fits (see `<memory_check>`)
- The viewer was opened with `sync_to` set to the source H5AD's `LPath`, not just a local path, so later edits (e.g. image alignment) can persist
- The user was told, in chat, which tab the viewer opened in
</self_eval_criteria>

<memory_check>
Run this **before** `read_h5ad`. The pod has 8–32 GB, and the in-memory object plus the copies
background removal and normalization make will need several times the file size. A pod that runs out
of memory does not crash — it pages, and the notebook simply stops making progress with no traceback.

```python
import psutil

size_gb = local_h5ad.stat().st_size / 1e9
avail_gb = psutil.virtual_memory().available / 1e9
print(f"H5AD {size_gb:.2f} GB | available RAM {avail_gb:.1f} GB")
if avail_gb < 4 * size_gb:
    print("WARNING: tight. Expect paging in background removal / normalization.")
```

If it warns, tell the user before loading and offer a larger pod rather than starting a run that will
stall hours later. Compressed H5ADs expand well beyond their on-disk size, so treat 4× as a floor.
</memory_check>

<new_tab_notice>
The viewer opens in its **own tab**, and the notebook does not switch to it. Say so in the same chat
message that reports the dimensions — see "Telling the user where results appeared" in `SKILL.md`:

> Your data is loaded: 84,213 beads × 31,053 genes. The viewer opened in a **new tab** — click it in
> the notebook to see the spatial coordinates. Do you have an H&E or other pathology image you'd like
> to overlay?

Everything after this step happens *in that tab*, so this is the one the user most needs to find.
Keep the H&E question in the same message — `main.md` requires that offer every time spatial data is
loaded.
</new_tab_notice>
