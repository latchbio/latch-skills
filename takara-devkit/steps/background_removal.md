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

from takara import remove_background, KitType, monitor, tail
import takara

# Which code is actually running. The deployed copy under technology_docs/takara/lib is an
# artifact *copied* from the repo, not a checkout of it, so the branch you launched from
# does not tell you what is on the pod — this does. A stale copy has already cost one full
# investigation: two runs were compared as "old vs new" while both were the old code.
print(takara.describe())
```

Report that line to the user before any timing run. To check it against your working copy,
this reproduces the same id from the repo without importing anything:

```bash
python3 -c "import hashlib,pathlib; h=hashlib.sha256()
[ (h.update(p.name.encode()), h.update(p.read_bytes())) for p in sorted(pathlib.Path('takara-devkit/lib/takara').glob('*.py')) ]
print(h.hexdigest()[:12])"
```

If the two ids differ, the pod is running different code from the one you edited — stop and
re-register the skill. Any measurement taken before they match is about the wrong program.

### Usage

Always run this inside `monitor`. The portal shows no progress for a running cell, so an
eight-second step and a hung one look identical; `monitor` is what tells them apart.

Open a logs widget **in the same cell, before** the monitored block — per
`latch-plots-ui/SKILL.md` this is the supported way to show progress in the portal, and bare
`print()` is explicitly not:

```python
from lplots.widgets.logs import w_logs_display
from lplots import submit_widget_state

w_logs_display(label="Background removal progress")
submit_widget_state()

with monitor("background removal") as mon:
    result = remove_background(
        adata,
        kit_type=KitType.TEN_BY_TEN,  # or KitType.THREE_BY_THREE
        min_log10_umi=1.4,  # adjust based on UMI histogram
        progress=mon.phase,
    )

adata_filtered = result.adata_filtered
```

`monitor` emits a line per step plus a heartbeat every 15 s carrying resident memory,
available RAM, CPU, swap rate and network rate, and closes with a per-phase table and a
verdict. It writes to the widget stream *and* to `/tmp/takara_progress.log`.

**Rely on the log file.** It is fsynced per line and outlives the kernel, so a run aborted
after five hours still says exactly where it was and what the pod was doing. Read it from a
fresh cell — including after an abort:

```python
from takara import tail
w_text_output(content=tail(120))
```

`/tmp` is pod-local and is lost when the pod recycles. To keep a run's log, pass a path on a
mounted volume: `monitor("background removal", path="/root/bg_removal.log")`.

`remove_background` does **not** modify the `adata` you pass it. This is deliberate: that
object is bound to the `w_h5` viewer with `sync_to`, and per Latch engineering `sync_to`
persists by serializing the Python AnnData and uploading it to the `LPath`. A stray `.obs`
write on it can therefore start a multi-GB upload from inside an unrelated cell. Earlier
versions wrote `obs['log10_nCount_RNA']` back to the source; that column is now on
`result.adata_filtered` only.

**The same rule applies to anything you write.** Before assigning to `adata.obs` or
`adata.obsm` on the viewer-bound object, consider whether it needs to persist. If it does,
do it deliberately and call `h5_refresh` — don't let it happen as a side effect.

### If this step runs long, read the monitor log

Measured at the production shape — 741,256 beads × 38,086 genes, CSC — the whole function
takes **under one second**, and it scales linearly in non-zeros. If this step is taking
minutes, the time is not in the filtering, and guessing at the algorithm will waste it.

`monitor` writes a verdict when the run ends, and the heartbeat lines tell you the same
thing while it is still going. Read the slowest phase:

| heartbeat shows | what is actually happening |
|---|---|
| `cpu` high, `rss` steady | genuinely computing |
| `cpu` low, `swap` non-zero | the pod is out of RAM and thrashing — fix pod size or the load path |
| `cpu` low, `net_tx` high | a `sync_to` H5AD serialize-and-upload, not computation |
| `cpu` low, everything flat | blocked on I/O or a remote call |

Only the first of those is a reason to look at this function.

To capture the environment as well — this distinguishes a compute problem from a memory
problem in seconds, and the answer determines the fix:

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
| `to_csr` | True | Convert `adata_filtered.X` (and any CSC layer) to CSR. This is the only place in the pipeline that converts — leave it on. Measured at 741,256 × 38,086 / 100M nnz: +1.1 s, and no increase in peak memory |
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

# Spatial visualization — downsample first. At 741K beads an alpha-blended scatter of every
# point takes minutes in matplotlib and can be hundreds of MB if rendered to an interactive
# plot, which reads in the portal as a cell that never finishes. 100K points is plenty to
# judge morphology.
coords = adata.obsm["spatial"]
keep, drop = result.step3_mask, ~result.step3_mask
if adata.n_obs > 100_000:
    sel = np.zeros(adata.n_obs, dtype=bool)
    sel[np.random.default_rng(0).choice(adata.n_obs, 100_000, replace=False)] = True
    keep, drop = keep & sel, drop & sel

plt.scatter(coords[drop, 0], coords[drop, 1], s=1, c="gray", alpha=0.3)
plt.scatter(coords[keep, 0], coords[keep, 1], s=1, c="red")
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
Background removal completes in **seconds**, not hours — all three masks come from bead coordinates
and UMI counts, and the counts matrix is subset exactly once. Measured at the largest production
shape seen so far, 741,256 beads × 38,086 genes stored CSC: **0.83 s**, linear in non-zeros. Do
**not** show the "leave this notebook open" message for this step; save it for feature selection,
dimensionality reduction, and clustering, which really are slow at this scale.

That timing holds **only while the matrix fits in RAM and nothing is uploading**. This step has
stalled for hours in production three times. Each time the filtering itself was measured and ruled
out — including once *after* it had already been made 300× faster, which changed the wall clock not
at all. Do not optimize this function again without a measurement showing it is the cost.

If it runs longer than a minute:

1. Do not kill it — `monitor` is already recording. The heartbeat names the phase it is in and
   whether the pod is computing, swapping, or uploading.
2. Read the table under `### If this step runs long` above and act on the *verdict*, not on a guess.
3. If you did kill it, the log outlived the kernel: `from takara import tail; print(tail(120))`.

Treat a long run here as a bug to investigate, not a wait. Only tell the user to leave the notebook
open once the heartbeat shows the pod is genuinely CPU-bound.
</long_running_guidance>

<new_tab_notice>
The bead counts, density histogram, and spatial before/after plots open in a **new tab** that the
notebook does not switch to. Name it in chat when you report the result — see "Telling the user where
results appeared" in `SKILL.md`:

> Background removal kept 71,402 of 84,213 beads. The plots opened in a **new tab** named
> **Background removal** — click it in the notebook to check that the retained beads still trace the
> tissue.
</new_tab_notice>
