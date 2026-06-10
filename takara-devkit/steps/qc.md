<goal>
Identify and apply filtering thresholds to counts.
</goal>

<method>
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
- Seek help from the user to identify a cutoff least disruptive to their morphology
- Prioritize spatial continuity and preservation of 'important morphology' over cutoffs selected from histogram data alone.

Permissive sanity checks (should hold true across tissue/disease):
- Never >20% mito per bead
- Never <25 genes per bead
- Never <30 UMI per bead
</self_eval_criteria>
