<goal>
Determine per-sample UMI thresholds for calling barcodes as "real cells" using knee-curve analysis on ranked UMI counts. This step establishes which barcodes represent true cells versus empty droplets or debris.
</goal>

<method>
1. Load the aggregated `.h5mu` from the previous step.

2. For each sample, compute total RNA UMI counts per barcode from the `gene_expression` modality:
   ```python
   import scanpy as sc
   sc.pp.calculate_qc_metrics(mdata["gene_expression"], inplace=True)
   ```

3. Rank barcodes by descending total UMI count and apply knee-point detection:
   ```python
   from lib.barcode.filtering import knee_point, knee_cells_from_umis
   
   # Get per-barcode counts sorted descending
   counts_sorted = adata.obs["total_counts"].sort_values(ascending=False).values
   
   # Detect knee
   knee_idx = knee_point(counts_sorted)
   ```

4. Plot ranked UMI curves (barcode rank vs total UMI, log-log scale) with the detected knee position highlighted:
   ```python
   from lib.plotting.barcode import plot_rank_knee
   umi_at_knee = plot_rank_knee(df_summary, knee_ncells, sample_name, value_type="total_counts")
   ```

5. Display UMI histograms showing the distribution of counts with the threshold marked:
   ```python
   from lib.plotting.barcode import plot_histograms
   plot_histograms(df, sample_name, umi_threshold=UMI_THR, data_type="total_counts")
   ```

6. Allow the user to adjust the UMI threshold if the automatic knee is not suitable. Default: `UMI_THR = 1000`.

7. Mark barcodes as `is_cell = True/False` based on the selected threshold in `.obs`.

Parameters:
- `UMI_THR`: UMI count threshold for calling real cells (default: 1000)
- The knee-point algorithm uses a smoothing window of 101 and searches between the 1st and 90th percentile of the curve
</method>

<workflows>
</workflows>

<library>
- `lib.barcode.filtering` — `knee_point()`, `knee_cells_from_umis()`
- `lib.plotting.barcode` — `plot_rank_knee()`, `plot_histograms()`
</library>

<self_eval_criteria>
- Knee plots are generated for each sample showing ranked UMI curves with threshold
- The selected UMI threshold produces a reasonable number of cells given the experimental design (ask the user about expected cell recovery if unsure)
- Barcodes are annotated with `is_cell` boolean in .obs
- The threshold is documented and justified (either automatic knee or user-adjusted)
- If the knee detection fails or looks unreasonable, fall back to the user-specified UMI_THR
</self_eval_criteria>
