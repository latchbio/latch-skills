<goal>
Perform Leiden clustering at multiple resolutions and select a biologically meaningful resolution using diagnostic plots comparing cluster assignments to automatic cell type labels, silhouette scores, and cluster stability metrics.
</goal>

<method>
1. Run Leiden clustering at multiple resolutions:
   ```python
   import scanpy as sc
   
   RESOLUTIONS = [0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
   
   for res in RESOLUTIONS:
       key = f"leiden_{res}"
       sc.tl.leiden(adata, resolution=res, key_added=key, random_state=RANDOM_SEED)
   ```

2. Visualize clusters on UMAP for each resolution:
   ```python
   sc.pl.umap(adata, color=[f"leiden_{r}" for r in RESOLUTIONS], ncols=3)
   ```

3. Compute cluster diagnostics for resolution selection:
   - **Adjusted Rand Index (ARI)** between Leiden clusters and SCimilarity cell type labels (from next step, or pre-computed if available)
   - **Silhouette score** per resolution:
   ```python
   from sklearn.metrics import silhouette_score
   
   for res in RESOLUTIONS:
       score = silhouette_score(adata.obsm["X_pca"][:, :n_pcs], adata.obs[f"leiden_{res}"])
   ```
   - **Number of clusters** vs resolution plot

4. Generate cluster-vs-celltype heatmaps:
   - Contingency table: rows = clusters, columns = cell type labels
   - Helps identify if clusters correspond to known biology

5. Assess embedding quality per sample:
   - Local Inverse Simpson's Index (LISI) or similar metric
   - Helps decide if batch integration is needed

6. Select final resolution:
   ```python
   FINAL_RES = 0.6  # user-adjustable based on diagnostics
   adata.obs["leiden"] = adata.obs[f"leiden_{FINAL_RES}"]
   ```

7. Display cluster sizes and sample composition per cluster.

Parameters:
- `RESOLUTIONS`: list of clustering resolutions to explore (default: [0.2, 0.4, 0.5, 0.6, 0.8, 1.0])
- `FINAL_RES`: selected final resolution (default: 0.6)
- `RANDOM_SEED`: seed for reproducibility (default: 42)
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- Clustering is performed at multiple resolutions (at least 4 values)
- UMAP plots show clusters for each resolution
- Diagnostic metrics (silhouette, ARI) are computed to justify resolution choice
- Final resolution produces clusters that align with known cell type biology
- No cluster is dominated entirely by a single sample (potential batch artifact) unless biologically expected
- Cluster sizes are balanced (no extremely small clusters with <5 cells unless rare populations)
</self_eval_criteria>
