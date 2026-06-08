<goal>
Perform differential gene expression to identify cluster marker genes, and assess amplicon read distributions across clusters to explore DNA-level variation in the context of RNA-defined cell populations.
</goal>

<method>
1. Compute cluster marker genes using Wilcoxon rank-sum test:
   ```python
   import scanpy as sc
   
   sc.tl.rank_genes_groups(adata, groupby="leiden", method="wilcoxon")
   sc.pl.rank_genes_groups(adata, n_genes=10, sharey=False)
   ```

2. Display top marker genes per cluster:
   - Dotplot showing expression of top N markers across clusters
   - Heatmap of marker gene expression
   ```python
   sc.pl.rank_genes_groups_dotplot(adata, n_genes=5)
   sc.pl.rank_genes_groups_matrixplot(adata, n_genes=5)
   ```

3. Validate markers against cell type annotations (SCimilarity or user-provided):
   - Do cluster markers match known markers for the predicted cell types?
   - Flag clusters where markers are inconsistent with automatic labels
   - If cell type annotations are unavailable, use marker genes for manual annotation

4. Amplicon read distributions per cluster:
   - For each Leiden cluster, compute per-cell amplicon read distributions
   - Compare amplicon detection rates across cell types
   ```python
   # Cross-modality: map amplicon data to RNA-defined clusters
   amp_data = mdata["amplicon"]
   # Subset to cells in RNA analysis
   shared_cells = list(set(amp_data.obs_names) & set(adata.obs_names))
   ```

5. Amplicon-to-target correlations:
   - Correlate amplicon read counts with RNA expression of targeted genes
   - Identify amplicons where DNA-level signal correlates with RNA expression
   - Flag discordant amplicons (DNA detected but no RNA, or vice versa)

6. Cluster-level amplicon summary:
   - Mean amplicon reads per cluster
   - Detection rate per amplicon per cluster
   - Heatmap: clusters x amplicons (mean reads or detection fraction)

7. General diagnostics:
   - Per-cluster detection rates for amplicon panel
   - Identify cell populations with unusually high/low amplicon capture

Parameters:
- Marker gene detection: Wilcoxon rank-sum, top N genes per cluster
- Amplicon correlation: Pearson/Spearman between amplicon reads and gene expression
</method>

<workflows>
</workflows>

<library>
- `lib.plotting.amplicon` — `plot_amplicon_anchors()`
- `lib.common_const` — `Modality.AMPLICON`, `Modality.GENE_EXPRESSION`
</library>

<self_eval_criteria>
- Marker genes are identified for each cluster (at minimum top 5 per cluster)
- Marker genes are biologically plausible for the predicted cell types
- If amplicon modality is present: amplicon data is successfully mapped to RNA-defined clusters
- If amplicon modality is present: amplicon detection rates are computed per cluster
- Amplicon-RNA correlations are assessed for targeted genes (when amplicon target-to-gene mappings are available)
- Summary visualizations (dotplots, heatmaps) are generated
- Clusters with anomalous amplicon patterns are flagged
- If no amplicon data exists, this step focuses solely on marker gene identification
</self_eval_criteria>
