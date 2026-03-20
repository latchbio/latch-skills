<goal>
Perform normalization, dimensionality reduction, clustering, and differential expression on AnnData.
</goal>

<method>
1/ **Normalization**  
   - Provide a choice between **log1p** and **total count scaling** via lplots widgets.  
   - Default behavior: apply **log1p** to the QC-filtered dataset.

2/ **Dimensionality Reduction**  
   - Check whether PCA and UMAP already exist in the AnnData object.  
     - If present, do **not** recompute unless the user explicitly chooses to.  
   - If recomputation is required:  
     - Compute **PCA**, then **UMAP**.  
     - Expose widget controls for:  
       - Number of PCs (default **10**)  
       - Number of neighbors (default **40**)  
   - Always visualize PCA and UMAP embeddings.

3/ **Clustering**  
   - Compute neighbors if missing.  
   - Apply **Leiden clustering** with default resolution **0.3**.  
   - Display clusters on **UMAP** and **spatial embeddings**.

4/ **Differential Gene Expression (DGE)**  
   - Identify cluster marker genes via rank-based tests.  
   - Default test: **t-test**, with alternative methods selectable via lplots widgets.  
   - Report **top marker genes per cluster**.  
   - Visualize results using Scanpy dot plots.
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
</self_eval_criteria>
