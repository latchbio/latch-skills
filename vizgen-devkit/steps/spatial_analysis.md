<goal>
Run Squidpy-based spatial analyses on Vizgen MERFISH data.
</goal>

<method>
All spatial analyses must use **Squidpy** (`sq.gr`, `sq.pl`) and rely on spatial coordinates stored in the AnnData object (e.g., `adata.obsm["X_spatial"]`).

1/ **Centrality Analysis**  
   - Check whether spatial centrality scores already exist in `adata` (e.g., under `adata.obs` or `adata.uns` for the chosen `cluster_key`, typically `"leiden"`).  
   - If missing, compute centrality metrics with:
     - `sq.gr.centrality_scores(adata, cluster_key="leiden")`  
   - Use lplots widgets to let the user choose which centrality metric(s) (e.g., degree, betweenness, closeness) to visualize.  
   - Plot selected centrality scores overlaid on spatial coordinates using Squidpy plotting functions.

2/ **Co-occurrence Analysis**  
   - Compute pairwise cluster co-occurrence using:
     - `sq.gr.co_occurrence(adata, cluster_key="leiden", n_jobs=4)`  
   - Extract the 3D co-occurrence tensor from:
     - `adata.uns["leiden_co_occurrence"]["occ"]`  
     and average across spatial intervals to obtain a 2D co-occurrence matrix.  
   - Use lplots widgets to:
     - Let users select which clusters or cell types to focus on.  
   - Visualize co-occurrence patterns as heatmaps (and optionally bar plots) using Squidpy-compatible plotting functions and the averaged 2D matrix.

3/ **Neighborhood Enrichment**  
   - Compute neighborhood enrichment between clusters:
     - `sq.gr.nhood_enrichment(adata, cluster_key="leiden")`  
   - Visualize enrichment via:
     - Heatmaps and spatial overlays using `sq.pl.nhood_enrichment` and related plots.  
   - Optionally present **z-score–normalized** enrichment values to highlight over- and under-enriched cluster neighborhoods.

4/ **Ripley’s Statistics**  
   - Provide a lplots widget to let the user choose the Ripley mode:
     - Options: `"L"`, `"F"`, `"G"`; default: `"F"`.  
   - Run:
     - `sq.gr.ripley(adata, cluster_key="leiden", mode=mode)`  
   - Retrieve results from `adata.uns` using keys of the form:
     - `"{cluster_key}_ripley_{mode}"` or a fallback (e.g., `"leiden_ripley"`).  
   - Build a tidy dataframe of Ripley statistic values for all clusters and all distance bins.  
   - Use **Plotly** to create a multi-line curve plot:
     - One line per cluster, plotting statistic vs. spatial distance.  
     - Include a reference line representing a random (CSR) pattern.  
   - Ensure Ripley curves are plotted for **every cluster** and clearly labeled.

5/ **Spatial Autocorrelation (Moran’s I)**  
   - Compute Moran’s I scores for spatial gene expression using:
     - `sq.gr.spatial_autocorr(adata, mode="moran")` (or equivalent Squidpy API).  
   - Rank genes by Moran’s I to identify the most spatially autocorrelated genes.  
   - Display a table of the **top 10** genes ranked by Moran’s I.  
   - Optionally, for these genes, show spatial expression patterns using:
     - `sq.pl.spatial_scatter` (or similar Squidpy spatial plotting functions) so the user can visually inspect spatial structure.
</method>

<workflows>
</workflows>

<library>
squidpy, scanpy, plotly
</library>

<self_eval_criteria>
- Centrality scores show spatial organization (not uniform across tissue)
- Co-occurrence matrix reveals biologically plausible cell type associations
- Neighborhood enrichment shows clear over/under-enrichment patterns (not all neutral)
- Ripley's curves deviate from CSR reference line (indicating spatial clustering/dispersion)
- Top Moran's I genes show spatial expression patterns (not random noise)
</self_eval_criteria>
