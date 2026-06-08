<goal>
Compute PCA on highly variable genes, build a k-nearest neighbor graph, and generate UMAP embeddings for visualization. Optionally determine the optimal number of principal components automatically.
</goal>

<method>
1. Scale the data (zero mean, unit variance) on HVGs:
   ```python
   import scanpy as sc
   
   sc.pp.scale(adata, max_value=10)
   ```

2. Run PCA on highly variable genes:
   ```python
   sc.tl.pca(adata, n_comps=50, use_highly_variable=True)
   ```

3. Determine the number of PCs to use:
   - If `NUM_PCS` is specified, use that value directly
   - If `NUM_PCS = None`, automatically select based on the elbow/variance explained:
   ```python
   # Plot variance ratio to help select
   sc.pl.pca_variance_ratio(adata, n_pcs=50)
   
   # Auto-pick: find elbow where cumulative variance explained > 80-90%
   cumvar = adata.uns["pca"]["variance_ratio"].cumsum()
   n_pcs = (cumvar < 0.90).sum() + 1
   n_pcs = max(n_pcs, 15)  # minimum 15 PCs
   ```

4. Compute the neighborhood graph:
   ```python
   sc.pp.neighbors(adata, n_pcs=n_pcs, n_neighbors=15)
   ```

5. Generate UMAP embedding:
   ```python
   sc.tl.umap(adata, random_state=RANDOM_SEED)
   ```

6. Visualize embeddings colored by:
   - Sample identity
   - Total counts
   - Number of genes
   - Mitochondrial fraction
   ```python
   sc.pl.umap(adata, color=["sample_name", "total_counts", "n_genes_by_counts", "pct_counts_mt"])
   ```

Parameters:
- `NUM_PCS`: number of principal components (default: None for auto-selection)
- `RANDOM_SEED`: seed for reproducibility (default: 42)
- n_neighbors for the kNN graph: 15 (standard default)
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- PCA variance ratio plot is generated
- Selected number of PCs captures >80% of variance in HVGs
- UMAP embedding shows structure (not a uniform blob)
- Embeddings are colored by sample to assess potential batch effects
- If samples separate strongly on the UMAP by batch rather than biology, flag that batch-aware integration (e.g., Harmony, scVI) may be needed as a subsequent step
- For single-sample experiments, batch assessment is not applicable
</self_eval_criteria>
