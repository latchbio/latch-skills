# Step 5 — Neighbors Enrichment Analysis and Domain Detection

<goal>
Quantify spatial neighborhood structure (centrality, enrichment, spatially variable genes) from the processed Xenium dataset.
</goal>

<method>
1/ Build a spatial neighborhood graph using clustering results and compute centrality scores with Squidpy.
   - Use `w_text_output` to provide a one-sentence summary of what each centrality score represents and how to interpret it.
   - Visualize centrality scores on spatial embeddings.
   ```python
   sq.gr.spatial_neighbors(adata, coord_type="generic", delaunay=True, spatial_key="Spatial")
   sq.gr.centrality_scores(adata, cluster_key="leiden")
   sq.pl.centrality_scores(adata, cluster_key="leiden", figsize=(20, 5))

   fig_centrality = plt.gcf()
   w_plot(label="Centrality Scores by Cell Type", source=fig_centrality)
   plt.close()
   ```

2/ Compute neighborhood enrichment scores between cell types with:
   - `sq.gr.nhood_enrichment(adata, cluster_key="cell_type")`
   Visualize the resulting z-scores in a Plotly heatmap.

3/ Identify spatially variable genes using Moran’s I with:
   - `sq.gr.spatial_autocorr(adata, mode="moran", n_jobs=-1)`
   Highlight the top spatially autocorrelated genes on the spatial embedding.
</method>

<workflows>
</workflows>

<library>
- `squidpy`
- `plotly`
- `matplotlib`
- `scanpy`
- `latch.types`
- `latch.ldata.path`
- `lplots.widgets.workflow`
- `pathlib`
</library>

<self_eval_criteria>
- Spatial neighbor graph builds successfully with reasonable centrality patterns.
- Neighborhood enrichment heatmap shows interpretable positive and negative z-scores between cell-type pairs.
- Moran’s I identifies non-trivial sets of spatially variable genes.
- The processed `.h5ad` is successfully written, uploaded.
</self_eval_criteria>
