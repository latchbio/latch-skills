<goal>
Identify and apply filtering thresholds to counts.
</goal>

<method>
### Which object this step operates on

Rebind `adata` before you start, so every reference below is unambiguous:

- **Seeker** — QC runs on the background-removed object, not the one loaded in step 1:
  `adata = result.adata_filtered` (from `steps/background_removal.md`).
- **Trekker** — background removal is skipped, so QC runs on the `adata` from
  `steps/data_loading.md` as-is. Nothing to rebind.

Getting this wrong on Seeker data is silent, not an error: thresholds get chosen from histograms
that still include the off-tissue background beads background removal just discarded, which drags
the low end of every distribution down and puts the valley in the wrong place.

For each of "genes per bead", "mitochondrial percentage" and "total UMIs" do the following:

1/ Make histograms of this metric. Set the x-axis range explicitly to the actual data range (min to max of the metric values computed from `adata.obs`) — do not rely on library defaults or hardcoded limits. For total UMIs use `xlim=(0, adata.obs['total_counts'].max())`.
2/ Plot spatial coordinates of *removed beads&* for a reasonable range of metrics so the user can identify effects on morphology 
3/ Expose a text input widget where the user can modify this value
4/ Render the bead-removal summary for that value **in the same cell**, from the same variable the plot uses — see "One cutoff variable per metric" below
5/ Inform the user that thresholds should be chosen that mess with the spatial morphology the least

For the "total UMIs" method specifically, also generate a knee plot:
- X-axis: bead rank (sorted by UMI count descending, so rank 1 = highest UMI count)
- Y-axis: total UMIs
- Both axes in log scale
- X-axis range: explicitly set to `(1, n_beads)` where `n_beads = len(adata)` — never use a hardcoded upper limit
- Y-axis range: explicitly set to `(adata.obs['total_counts'].min(), adata.obs['total_counts'].max())` — not a library default
- The knee/inflection point visually indicates a natural UMI threshold separating real beads from empty droplets/background

Start with "genes per bead" and go one at a time. Once all three cutoffs are set and the filter is
applied, close the step with the passed/failed spatial pair — see "The final plot" below.

Always use text input widgets for precise viewing and manipulation of threshold values (instead of eg. sliders)

### One cutoff variable per metric — the summary must move with the plot

The removed-beads plot updates when the user edits the cutoff box, but the **summary of the final
calculation goes stale**: it keeps reporting the default (100 genes per bead, and the bead count that
default removed) after the user has changed the box to something else. The user is then looking at a
plot for their cutoff and a bead count for a cutoff nobody chose. Every number the user reads must
come from the value currently in the box.

This happens when the summary is computed somewhere that does not re-run on a widget change:

- in a **separate cell** from the widget — the reactive kernel only re-runs cells that read
  `.value`, so a summary cell that closes over a `cutoff` variable bound by an earlier run keeps
  printing the old number, and nothing about it looks broken;
- from a **hardcoded literal** (`n_removed = (adata.obs["n_genes_by_counts"] < 100).sum()`) that was
  correct on the first pass and silently wrong after;
- in a **chat message only**. Chat text is frozen at the moment you wrote it. It cannot update when
  the user edits the box, so it must never be the only place a bead count appears.

So, for each metric:

**Read `.value` and derive everything below it in one cell.** The widget, the effective cutoff, the
histogram, the removed-beads spatial plot, and the summary all live in a single cell. One
`cutoff` variable feeds the plots and the summary, so they cannot disagree.

```python
from lplots.widgets.text import w_text_input, w_text_output

DEFAULT_MIN_GENES = 100

w_min_genes = w_text_input(
    label="Minimum genes per bead",
    key="qc_min_genes",
    default=str(DEFAULT_MIN_GENES),
)

# reading .value here is what makes the cell reactive — the plots AND the summary below
# re-run on every edit of the box
raw = (w_min_genes.value or "").strip()
try:
    min_genes = float(raw) if raw else DEFAULT_MIN_GENES
except ValueError:
    # keep the last good threshold rather than killing the cell mid-typing ("1", "1e", ...)
    min_genes = DEFAULT_MIN_GENES
    w_text_output(content=f"{raw!r} is not a number — showing {DEFAULT_MIN_GENES}.",
                  appearance={"message_box": "warning"})

removed = adata.obs["n_genes_by_counts"] < min_genes   # one mask, used by plot and summary
n_removed = int(removed.sum())

# ... histogram + spatial plot of adata[removed] , both using `min_genes` / `removed` ...

w_text_output(
    content=(
        f"Cutoff: {min_genes:g} genes per bead\n"
        f"Removed: {n_removed:,} of {len(adata):,} beads ({n_removed / len(adata):.1%})\n"
        f"Retained: {len(adata) - n_removed:,} beads"
    ),
    appearance={"message_box": "info"},
)
```

**Never write the cutoff twice.** No second literal in the summary string, no `cutoff = 100` re-bound
in a later cell, no separate mask for the plot and the summary. If a number appears in the summary it
is interpolated from `min_genes` / `n_removed`, never typed out.

**A cutoff given in chat goes into the widget, not around it.** When the user says "use 150" instead
of typing it, edit the widget cell so `default="150"` and re-run — do not add `min_genes = 150` below
the widget, which leaves the box showing one number and the summary another. Widget values persist by
`key`, so if the user had already typed something the persisted value wins over the new default: read
the rendered summary back, and if it did not take, tell them the number to type into the box.

**Quote the summary from the widget when you talk about it in chat.** State the cutoff alongside the
count ("at 150 genes per bead that removes 12,431 beads — the current numbers are always in the
**QC — genes per bead** tab"), so a bead count that has since been superseded is self-dating rather
than authoritative.

### Re-render each metric's plots with the value used in the final calculation

The summary rule above keeps the *text* honest. The **figures** need the same treatment, and they
fail the other way round: the final filter runs on the user's custom cutoff while the histogram,
the removed-beads spatial plot and the knee plot still show the default. Nothing errors — the tab
comes up with the right plots under the right labels, all describing a cutoff nobody chose.

Once the cutoffs are settled — and again whenever the user changes one — **re-run each metric's cell
so its figures are drawn from the current widget value**, then say in chat which tab now holds the
updated plots (see `<new_tab_notice>`).

Every cutoff that reaches a figure is interpolated from the same variable the final calculation
uses, never re-typed:

- histogram threshold line — `ax.axvline(min_genes, ...)`, not `axvline(100)` or
  `axvline(DEFAULT_MIN_GENES)`
- knee plot cutoff line — `ax.axhline(min_umis, ...)`
- the removed-beads spatial plot — the same `removed` mask the summary counts, not a second
  comparison written out again
- plot titles and annotations — f-strings off the cutoff variable
  (`ax.set_title(f"Genes per bead — cutoff {min_genes:g}")`)
- a sweep of candidate cutoffs (method step 2 above) is centered on the current value, not a fixed
  hardcoded set

The default constant appears in exactly two places: the widget's `default=` and the parse fallback
in the `try/except`. Anywhere else it is the bug.

The figure and its `w_plot(...)` call live in the **same cell that reads `.value`**, so the
re-render happens on its own — no figure built in an earlier setup cell, and no drawing onto an axes
left over from a previous run. Both would keep rendering the first pass forever, silently. Figure
naming follows "Rendering figures — one variable per plot" in `SKILL.md`.

### The final plot — QC-passed and QC-failed beads, side by side

When filtering is applied, the closing spatial plot must show **both** sides of the cut: the beads
that passed QC *and* the beads it removed, as two panels of one figure. A retained-beads plot on its
own cannot answer the question the user is actually asking — whether the thresholds ate real tissue.
Intact-looking morphology in the passed panel says nothing; the damage is only visible in what was
taken out.

One figure, two axes, one `w_plot`:

```python
import numpy as np

keep = (
    (adata.obs["n_genes_by_counts"] >= min_genes)
    & (adata.obs["pct_counts_mt"] <= max_mito)
    & (adata.obs["total_counts"] >= min_umis)
).to_numpy()          # the same mask the filter itself uses — never a second set of comparisons

xy = np.asarray(adata.obsm["spatial"])            # Takara spatial coords live in obsm, not obs

fig_qc_final_spatial, (ax_pass, ax_fail) = plt.subplots(
    1, 2, figsize=(14, 6), sharex=True, sharey=True,
)

ax_pass.scatter(xy[keep, 0], xy[keep, 1], s=1)
ax_pass.set_aspect("equal")
ax_pass.set_title(f"QC passed — {keep.sum():,} beads ({keep.mean():.1%})")

ax_fail.scatter(xy[~keep, 0], xy[~keep, 1], s=1)  # same marker size as the passed panel
ax_fail.set_aspect("equal")
ax_fail.set_title(f"QC failed — {(~keep).sum():,} beads ({(~keep).mean():.1%})")

w_plot(label="QC result — passed vs failed", source=fig_qc_final_spatial, key="qc_final_spatial")
```

Three things make the comparison readable, and all three are easy to lose:

- **Both panels on the same axes limits and the same aspect.** Left to itself matplotlib autoscales
  each panel to its own points, so the failed beads render in a different coordinate frame at a
  different zoom — the two pictures then cannot be laid over each other by eye, which is the entire
  point. `sharex=True, sharey=True` plus `set_aspect("equal")`, or set the limits explicitly from the
  full object.
- **Both panels from one mask.** `keep` and `~keep` — so the two panels always partition the same
  bead set and their counts add up to `len(adata)`.
- **Counts interpolated into the titles**, per the re-render rule above, so the panel labels move
  with the cutoffs.

Tell the user what to look for: the failed panel should read as background, edges and sparse
scatter. If it reproduces tissue structure — a recognizable region, a layer, a whole lobe — the
thresholds are removing real biology and should be relaxed, whatever the histograms suggested.

### Hand-off — Seeker: recommend RCTD before normalization

Once filtering is applied, **do not go straight to `steps/normalization.md` on Seeker data.** The
filtered object is now exactly what RCTD needs — raw counts in `.X` plus spatial coordinates — and
normalization overwrites `.X`, so this is the one point in the workflow where RCTD is free to run.

Recommend RCTD here, every time, and offer the skip in the same message; follow "When to recommend"
in `steps/rctd.md` for the wording. If the user declines, continue to normalization without
re-asking. For Trekker data there is no RCTD step — go directly to normalization.
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- For Seeker, the histograms were computed on the background-removed object (`result.adata_filtered`), not the H5AD loaded in step 1 — bead count should match the background-removal result, not the original
- Seek help from the user to identify a cutoff least disruptive to their morphology
- Prioritize spatial continuity and preservation of 'important morphology' over cutoffs selected from histogram data alone.

Permissive sanity checks (should hold true across tissue/disease):
- Never >20% mito per bead
- Never <25 genes per bead
- Never <30 UMI per bead
- The user was told, in chat, which tab holds the histograms and the threshold input widgets
- Editing the cutoff box updates the **summary of the final calculation** (cutoff value, beads removed, beads retained) as well as the removed-beads plot — check by changing the value and confirming the summary no longer reports the default of 100
- Each metric's cutoff exists as exactly one variable, derived from the widget's `.value` in the same cell as the plots and the summary — no hardcoded threshold literal outside the widget's `default`, and no summary cell separate from the widget cell
- Each metric's histogram threshold line, removed-beads spatial plot and knee-plot line show the cutoff that fed the final calculation — check by setting genes per bead well away from 100 and confirming no plot still draws the default
- No numeric cutoff literal or default constant appears in any plotting call; every cutoff drawn is interpolated from the widget-derived variable
- The final spatial plot shows QC-passed **and** QC-failed beads as two panels of one figure, on shared axis limits and equal aspect, with per-panel bead counts in the titles — a retained-beads-only plot does not satisfy this step
- The user was told what the failed panel means: background and edges is expected, recognizable tissue structure means the thresholds are too aggressive
- For Seeker data, RCTD was recommended (with an explicit skip option) after filtering and before normalization began — see `steps/rctd.md`
</self_eval_criteria>

<new_tab_notice>
This step is interactive — the histograms, the knee plot, and the threshold text inputs all live in a
**new tab** that the notebook does not switch to. A user who never finds that tab cannot set a
threshold, so name the tab in chat *before* you ask them for a value — see "Telling the user where
results appeared" in `SKILL.md`:

> The genes-per-bead histogram and the threshold input are in a **new tab** named **QC — genes per
> bead** — click it in the notebook and type a cutoff into the box. The plot and the summary
> underneath it both update as you type, so you can try a few values without messaging me.

Repeat this for each of the three metrics if each opens its own tab, and again for the final
passed/failed spatial pair once filtering is applied — name that tab too, and say the right-hand
panel is the one to check for lost morphology.
</new_tab_notice>
