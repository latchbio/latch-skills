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

# Load in memory, not backed='r'. AnnData.copy() raises ValueError on a backed object
# ("To copy an AnnData object in backed mode, pass a filename"), and a view of a backed
# object is itself backed — so every downstream step that subsets beads needs the
# in-memory handle. The pod has far more RAM than the file needs.
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
- The AnnData handed to downstream steps is in memory (`adata.isbacked is False`) — a backed object cannot be `.copy()`'d and will break bead filtering
- The viewer was opened with `sync_to` set to the source H5AD's `LPath`, not just a local path, so later edits (e.g. image alignment) can persist
- The user was told, in chat, which tab the viewer opened in
</self_eval_criteria>

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
