<goal>
Neighborhood and clustering (eg. Leiden).
</goal>

<method>

- PCA
Compute neighbors if it doesn't exist, apply **Leiden clustering** (start with
a reasonable range of resolutions like [0.2, 0.5, 0.7]) on the neighborhood
graph. **Always** display clusters on the UMAP and spatial embedding using
`w_h5`.
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- Ensure ~70k–90k beads for Seeker 3x3 or ~0.8–1.1M beads for Seeker 10x10
- Ensure there are ~30K gene features
</self_eval_criteria>

<long_running_guidance>
If adata.n_obs > 200000, display this message to the user after running the clustering cell:

"Your Clustering analysis is running on this pod notebook and may take some time to complete. Please leave this notebook open until the analysis is completed."
</long_running_guidance>
