<goal>
Detect and mark doublet barcodes (two cells captured in a single droplet) and estimate ambient RNA contamination. These steps ensure downstream analysis is not confounded by technical artifacts.
</goal>

<method>
1. Doublet detection using Scrublet (via scanpy):
   ```python
   import scanpy as sc
   
   sc.external.pp.scrublet(
       mdata["gene_expression"],
       expected_doublet_rate=EXP_DBL_RATE,
       random_state=RANDOM_SEED
   )
   ```
   - Default expected doublet rate: `EXP_DBL_RATE = 0.05` (~5%)
   - This adds `predicted_doublet` (bool) and `doublet_score` (float) to `.obs`

2. Visualize doublet scores:
   - Histogram of doublet scores with threshold line
   - UMAP colored by doublet score (if embedding exists)

3. Mark predicted doublets in `.obs["is_doublet"]` for downstream filtering.

4. Ambient RNA estimation using CellSweep:
   ```python
   import cellsweep
   
   # CellSweep estimates the fraction of counts attributable to ambient RNA
   # per cell based on the empty droplet profile
   ```
   - Identify the "ambient profile" from barcodes below the UMI threshold (empty droplets)
   - Estimate per-cell contamination fraction
   - Flag cells with excessive ambient contamination

5. Report summary statistics:
   - Number and percentage of predicted doublets per sample
   - Mean/median ambient RNA contamination fraction
   - Cells flagged for high contamination

Parameters:
- `EXP_DBL_RATE`: expected doublet rate (default: 0.05; scale with cell loading density — higher loading means more doublets)
- Ambient contamination threshold for flagging: implementation-dependent
- Note: if CellSweep is not available in the environment, skip ambient estimation and proceed with doublet filtering only
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- Doublet detection runs successfully on each sample
- Doublet rate is reasonable (typically 2-8% for standard single-cell protocols)
- Doublet scores show bimodal distribution (low-score singlets vs high-score doublets)
- Ambient RNA contamination estimates are generated
- Results are annotated in .obs for use in the filtering step
</self_eval_criteria>
