# Step 3 — Differential Gene Expression (DGE)

<goal>
Identify cluster-specific marker genes suitable for annotation and visualization.
</goal>

<method>
1/ Select the DGE method:
   - **Default (fastest):** `t-test_overestim_var` with Benjamini–Hochberg FDR control.
   - **Alternative (more robust to outliers/zero inflation):** `wilcoxon`.
   Keep `t-test_overestim_var` as the default (“Quick mode”) and offer a toggle to “Robust mode” → `wilcoxon` when users prioritize robustness over speed.

2/ Use `"K=5"` as the default clustering column and offer a dropdown widget to let the user select other cluster columns.

3/ Render parameters as widgets with defaults:
   - **Method:** `t-test_overestim_var` (default) | `wilcoxon`
   - **Top genes per cluster:** `top_n` (default: 5)

4/ Filter out cells with missing cluster labels and coerce cluster labels to strings.

```python
valid_cells = ~adata.obs[cluster_col].isna()
n_removed = (~valid_cells).sum()

adata_filtered = adata[valid_cells].copy()
adata_filtered.obs[cluster_col] = adata_filtered.obs[cluster_col].apply(
    lambda x: str(x) if not isinstance(x, str) else x
)
```

5/ Run differential gene expression using Scanpy with Benjamini–Hochberg correction.
```python
sc.tl.rank_genes_groups(
    adata_filtered,
    groupby=cluster_col,
    method=dge_method,
    use_raw=False,
    corr_method="benjamini-hochberg",
)
```

6/ Store results under adata.uns["dge"] and, per cluster, report:
    - gene
    - log fold change
    - p-value
    - **FDR** (adjusted p-value).

7/ Report top marker genes for each cluster and make dot plots with Scanpy.

8/ Select the **top four** biologically meaningful marker genes and color the spatial embedding by their log1p expression in four subplots, explaining briefly why they are biologically meaningful.
    - Use `w_text_output` to summarize the biological function of each top gene.
</method>

<workflows>
</workflows>

<library>
- `scanpy`
- `matplotlib`
- `plotly`
</library>

<self_eval_criteria>
- DGE runs without errors on the selected cluster column.
- Most clusters have non-empty marker sets with reasonable log fold changes and FDR.
- `adata.uns["dge"]` is populated and can be reused for cell-type annotation.
- Spatial and UMAP plots of top markers look biologically plausible.
</self_eval_criteria>

