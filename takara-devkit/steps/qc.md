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
4/ Tell the user how many beads will be removed after applying this value
5/ Inform the user that thresholds should be chosen that mess with the spatial morphology the least

For the "total UMIs" method specifically, also generate a knee plot:
- X-axis: bead rank (sorted by UMI count descending, so rank 1 = highest UMI count)
- Y-axis: total UMIs
- Both axes in log scale
- X-axis range: explicitly set to `(1, n_beads)` where `n_beads = len(adata)` — never use a hardcoded upper limit
- Y-axis range: explicitly set to `(adata.obs['total_counts'].min(), adata.obs['total_counts'].max())` — not a library default
- The knee/inflection point visually indicates a natural UMI threshold separating real beads from empty droplets/background

Start with "genes per bead" and go one at a time.

Always use text input widgets for precise viewing and manipulation of threshold values (instead of eg. sliders)
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
</self_eval_criteria>

<new_tab_notice>
This step is interactive — the histograms, the knee plot, and the threshold text inputs all live in a
**new tab** that the notebook does not switch to. A user who never finds that tab cannot set a
threshold, so name the tab in chat *before* you ask them for a value — see "Telling the user where
results appeared" in `SKILL.md`:

> The genes-per-bead histogram and the threshold input are in a **new tab** named **QC — genes per
> bead** — click it in the notebook, then type a cutoff into the box and I'll tell you how many beads
> it removes.

Repeat this for each of the three metrics if each opens its own tab.
</new_tab_notice>
