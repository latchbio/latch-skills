<goal>
Remove off-tissue background beads from Seeker spatial transcriptomics data.

**Seeker only** — skip this step entirely if the data was generated with the Trekker kit.
If Trekker, proceed directly to the next step (Quality Control + Filtering).

To confirm kit type at this step if not already known: ask the user "Was this data generated with a Seeker or Trekker kit?"
</goal>

<method>
### Setup

```python
import importlib
import sys
from pathlib import Path

TAKARA_LIB = "/opt/latch/plots-faas/runtime/mount/agent_config/context/technology_docs/takara/lib"

# Verify the module is actually there before trusting the path — sys.path.insert of a directory
# that does not exist is a silent no-op, and the import then resolves against some other `takara`.
assert (Path(TAKARA_LIB) / "takara" / "background_removal.py").is_file(), TAKARA_LIB

# Whichever `takara` is imported first pins its __path__ for the rest of the session, so a bare
# sys.path.insert does nothing. Drop the cached package AND refresh the path finders.
for _name in [m for m in sys.modules if m == "takara" or m.startswith("takara.")]:
    del sys.modules[_name]
while TAKARA_LIB in sys.path:
    sys.path.remove(TAKARA_LIB)
sys.path.insert(0, TAKARA_LIB)
importlib.invalidate_caches()

from takara import remove_background, KitType
```

### Usage

```python
result = remove_background(
    adata,
    kit_type=KitType.TEN_BY_TEN,  # or KitType.THREE_BY_THREE
    min_log10_umi=1.4,  # adjust based on UMI histogram
    progress=print,  # timestamped line per step; drop it once the run is known-good
)

# Final filtered data
adata_filtered = result.adata_filtered
```

`progress` exists because the failure mode this step has actually hit in production is a
**silent** stall — no traceback, no output, just a cell that never returns. Always pass it
on a first run against a new dataset, so a stall shows you which step it stalled in.

`remove_background` does **not** modify the `adata` you pass it. This is deliberate: that
object is bound to the `w_h5` viewer with `sync_to`, and per Latch engineering `sync_to`
persists by serializing the Python AnnData and uploading it to the `LPath`. A stray `.obs`
write on it can therefore start a multi-GB upload from inside an unrelated cell. Earlier
versions wrote `obs['log10_nCount_RNA']` back to the source; that column is now on
`result.adata_filtered` only.

**The same rule applies to anything you write.** Before assigning to `adata.obs` or
`adata.obsm` on the viewer-bound object, consider whether it needs to persist. If it does,
do it deliberately and call `h5_refresh` — don't let it happen as a side effect.

### If this step runs long, capture the environment first

Before assuming the algorithm is at fault, run this — it distinguishes a compute problem
from a memory problem in seconds, and the answer determines the fix:

```python
import psutil, anndata, scipy.sparse as sp

vm = psutil.virtual_memory()
print(f"anndata={anndata.__version__} scipy={sp.__version__} backed={adata.isbacked}")
print(f"RAM total={vm.total/1e9:.1f}GB avail={vm.available/1e9:.1f}GB used={vm.percent}%")
X = adata.X
if sp.issparse(X):
    print(f"X fmt={X.format} nnz={X.nnz:,} dtype={X.dtype} "
          f"bytes={(X.data.nbytes + X.indices.nbytes)/1e9:.2f}GB")
else:
    print(f"X dense {X.shape} {X.dtype}")
```

If `avail` is not comfortably above ~3× the reported `X` bytes, the pod is memory-bound and
the fix is pod size / the load path (`steps/data_loading.md`), not this function.

If memory looks fine, the next suspect is **`sync_to` upload traffic** rather than compute:
a viewer-bound `adata` that something has written to may be serializing and uploading the
whole H5AD. Check the pod's network activity before assuming the filtering is at fault.

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `kit_type` | - | `KitType.TEN_BY_TEN` (10mm) or `KitType.THREE_BY_THREE` (3mm) |
| `min_log10_umi` | 1.4 | log10(UMI) threshold - set at histogram valley |
| `m` | 40 | Step 2 neighborhood size (µm) |
| `n` | 100 | Step 3 neighborhood size (µm) |
| `p` | 5 | Min beads per m×m region |
| `q` | 10 | Min beads per n×n region |
| `to_csr` | False | Convert `adata_filtered.X` (and any CSC layer) to CSR. Faster for downstream per-bead steps, but costs one extra copy of the matrix — leave it off and let normalization convert after the matrix has shrunk |
| `progress` | None | Callable taking a string, e.g. `print`. Emits a timestamped line per step |

### Inspecting Results

```python
# Bead counts at each step
print(f"Original: {adata.n_obs}")
print(f"After UMI filter: {result.step1_mask.sum()}")
print(f"After step 2: {result.step2_mask.sum()}")
print(f"After step 3: {result.step3_mask.sum()}")

# Plot density histogram to verify p/q thresholds
result.step2_density["count"].hist(bins=30, density=True)

# Spatial visualization
coords = adata.obsm["spatial"]
plt.scatter(coords[~result.step3_mask, 0], coords[~result.step3_mask, 1], s=1, c="gray", alpha=0.3)
plt.scatter(coords[result.step3_mask, 0], coords[result.step3_mask, 1], s=1, c="red")
```

`result.adata_step1` and `result.adata_step2` are zero-copy **views** onto `adata` — read and plot
them freely, but do not mutate them (writing to a view silently materializes a full copy). Only
`result.adata_filtered` is an independent object.

### Choosing min_log10_umi

Plot UMI distribution and pick threshold at valley between background and tissue peaks:

```python
import numpy as np
log10_umi = np.log10(adata.obs["total_counts"] + 1)
log10_umi.hist(bins=100)
```
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- Difficult to check without understanding what portion of slide covered with tissue
</self_eval_criteria>

<long_running_guidance>
Background removal should complete in **seconds**, not hours — all three masks come from bead
coordinates and UMI counts, and the counts matrix is subset exactly once. Measured at 150,000 beads
× 4,000 genes (57M non-zeros): 0.5 s and 338 MB of peak RSS above baseline. Do **not** show the
"leave this notebook open" message for this step; save it for feature selection, dimensionality
reduction, and clustering, which really are slow at this scale.

That timing holds **only while the matrix fits comfortably in RAM and nothing is uploading**. This
step has stalled for hours in production on a large dataset. The filtering itself was measured and
ruled out both times; the causes to check, in order, are outside it. If it runs longer than a minute:

1. Do not kill it immediately — the `progress` output tells you which step it is in. If the last line
   printed is a *step* line, the masks are done and it is stuck materializing or uploading, not
   filtering.
2. Run the environment capture block under `### If this step runs long` above.
3. If available RAM is tight → pod size / load path (`steps/data_loading.md`).
4. If RAM is fine → suspect `sync_to` upload traffic from a write to the viewer-bound `adata`.

Treat a long run here as a bug to investigate, not a wait. Only tell the user to leave the notebook
open once you have confirmed which of the two causes it is.
</long_running_guidance>

<new_tab_notice>
The bead counts, density histogram, and spatial before/after plots open in a **new tab** that the
notebook does not switch to. Name it in chat when you report the result — see "Telling the user where
results appeared" in `SKILL.md`:

> Background removal kept 71,402 of 84,213 beads. The plots opened in a **new tab** named
> **Background removal** — click it in the notebook to check that the retained beads still trace the
> tissue.
</new_tab_notice>
