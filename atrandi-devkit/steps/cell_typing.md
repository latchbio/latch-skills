<goal>
Automatically annotate cells with the closest matching cell type labels from a broad human cell atlas reference using SCimilarity. This provides an unbiased biological annotation independent of clustering.
</goal>

<method>
1. Load the SCimilarity model from the configured path:
   ```python
   from scimilarity.utils import lognorm_counts
   from scimilarity import CellAnnotation
   
   # MODEL_PATH should point to the SCimilarity model directory on the pod
   # Common locations: /root/data/models/model_v1.1 or user-specified
   ca = CellAnnotation(model_path=MODEL_PATH)
   ```

2. Prepare the data for SCimilarity:
   - SCimilarity requires raw counts (not normalized) with gene symbols as var_names
   - Align genes to the model's expected gene set:
   ```python
   # Use raw counts layer
   adata_query = adata.copy()
   adata_query.X = adata_query.layers["raw_counts"]
   
   # Align to model genes
   ca.safelist_query(adata_query)
   ```

3. Run cell type prediction:
   ```python
   predictions = ca.annotate_dataset(adata_query)
   
   # Transfer labels back
   adata.obs["scimilarity_label"] = predictions["predicted_label"]
   adata.obs["scimilarity_score"] = predictions["prediction_score"]
   ```

4. Visualize cell type annotations:
   - UMAP colored by SCimilarity labels
   - UMAP colored by prediction confidence scores
   - Heatmap: SCimilarity labels vs Leiden clusters

5. Assess annotation quality:
   - Distribution of prediction confidence scores
   - Fraction of cells with low-confidence annotations (<0.5 score)
   - Concordance between SCimilarity labels and cluster structure

6. Generate cluster-vs-celltype contingency table:
   ```python
   import pandas as pd
   ct = pd.crosstab(adata.obs["leiden"], adata.obs["scimilarity_label"])
   ```

Parameters:
- `MODEL_PATH`: path to the SCimilarity model directory (user-configured; verify availability on pod before running)
- Confidence threshold for reliable annotations: 0.5 (scores below this are considered uncertain)

Note: SCimilarity assumes human data. For non-human organisms, an alternative annotation strategy should be used. If SCimilarity is unavailable, skip this step and rely on marker-gene-based annotation in the amplicon diagnostics step.
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- SCimilarity model loads successfully
- All cells receive a predicted label and confidence score
- Cell type annotations show expected diversity for the tissue type (ask user about expected cell types)
- Prediction confidence scores are mostly >0.5 (flag if >30% of cells have low confidence)
- Labels align with cluster structure (clusters should be enriched for specific cell types)
- UMAP visualization of cell types shows biologically coherent spatial organization
</self_eval_criteria>
