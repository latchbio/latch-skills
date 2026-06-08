<goal>
Assess amplicon read distributions relative to RNA-called cells, generate OncoPrint-style heatmaps for amplicon detection QC, and compute cross-modality completeness metrics. This is a key internal QC step for the RNA:DNA co-seq assay.
</goal>

<method>
1. Align amplicon modality barcodes with RNA-called cells:
   - Since modalities have partially overlapping `obs_names`, explicitly handle missing barcodes:
   ```python
   # Get union of barcodes across modalities
   rna_cells = set(mdata["gene_expression"].obs_names)
   amp_cells = set(mdata["amplicon"].obs_names)
   
   # For cross-modality comparisons, fill missing with 0
   overlap = rna_cells & amp_cells
   ```

2. Compute per-cell amplicon read counts and compare to RNA UMI counts:
   - Scatter plot: total amplicon reads vs total RNA UMIs per cell
   - Correlation between amplicon and RNA detection rates

3. Down-sample amplicon reads for fair cross-sample comparison:
   - Target: `AMP_READS_PER_CELL = 1000` average reads per cell per amplicon
   - This ensures comparable amplicon detection sensitivity across samples with different sequencing depths

4. Generate OncoPrint-style heatmaps (key internal QC diagnostic):
   ```python
   # Using pyoncoprint for binary detection heatmaps
   # Rows: cells (or cell clusters), Columns: amplicon targets
   # Color: detected (sufficient reads) vs not detected
   ```
   - Show per-cell amplicon detection pattern
   - Identify amplicons with systematically low detection
   - Identify cells with poor amplicon capture

5. Compute completeness metrics:
   - **Data completeness**: fraction of (cell x amplicon) matrix entries with >0 reads
   - **Cell completeness**: fraction of cells with all amplicons detected
   - **Amplicon completeness**: fraction of amplicons detected in all cells
   - Per-amplicon detection rate across cells

6. Amplicon vs RNA overlap statistics:
   - How many RNA-called cells also have amplicon data
   - How many amplicon barcodes are NOT in the RNA cell set (background amplicon reads)

Parameters:
- `AMP_READS_PER_CELL`: target reads per cell per amplicon for downsampling (default: 1000; adjust based on panel size and sequencing depth)
- Detection threshold: minimum reads to call an amplicon "detected" in a cell (depends on panel and expected coverage)
- Panel size: the number of amplicon targets varies by experiment; completeness expectations scale with panel size
</method>

<workflows>
</workflows>

<library>
- `lib.plotting.amplicon` — `plot_amplicon_anchors()`
- `lib.common_const` — `Modality.AMPLICON`, `Modality.GENE_EXPRESSION`
</library>

<self_eval_criteria>
- OncoPrint heatmaps are generated showing amplicon detection patterns
- Completeness metrics are computed and reported (data, cell, amplicon completeness)
- Cross-modality overlap is documented (RNA cells with amplicon data)
- Amplicons with <50% detection rate are flagged
- Down-sampling is applied before cross-sample comparisons
- Amplicon read correlation with RNA UMIs is visualized
</self_eval_criteria>
