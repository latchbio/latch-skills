<goal>
Apply all QC thresholds determined in previous steps to produce a filtered .h5mu object ready for biological analysis. This step consolidates cell calling, doublet removal, and QC annotations into a clean dataset.
</goal>

<method>
1. Apply hard UMI threshold filter:
   ```python
   # Keep only barcodes marked as cells
   mdata = mdata[mdata["gene_expression"].obs["is_cell"], :]
   ```

2. Remove predicted doublets:
   ```python
   mdata = mdata[~mdata["gene_expression"].obs["is_doublet"], :]
   ```

3. Update the `is_cell` annotation to reflect all filters applied.

4. Recalculate basic QC metrics on the filtered object:
   ```python
   import scanpy as sc
   sc.pp.calculate_qc_metrics(mdata["gene_expression"], inplace=True)
   ```

5. Update amplicon modality to match filtered cells:
   - Subset amplicon obs to cells present in filtered gene_expression
   - Recompute amplicon detection stats on filtered cells

6. Collect and append all metrics to `all_metrics.csv`:
   ```python
   from lib.metrics.metrics import MetricsCollector, MetricRecord
   
   record = MetricRecord(source_id=sample_name, library_type="RNA", modality="gene_expression")
   record.set("n_cells_after_filtering", n_filtered_cells)
   record.set("umi_threshold", UMI_THR)
   record.set("n_doublets_removed", n_doublets)
   ```

7. Save the filtered output:
   - Output: `samples_filtered.h5mu`
   - Also export: `all_metrics.csv` with per-sample QC summary

8. Display filtering summary:
   - Cells before vs after filtering (per sample)
   - Reasons for removal (below UMI threshold, doublets, ambient)
   - Final cell counts per sample

Parameters:
- All thresholds from previous steps are applied here
- No new parameters introduced
</method>

<workflows>
</workflows>

<library>
- `lib.metrics.metrics` — `MetricRecord`, `MetricsCollector`
</library>

<self_eval_criteria>
- Filtered .h5mu contains only cells passing all QC criteria
- Number of filtered cells is reasonable (not removing >80% of initial barcodes; if so, revisit thresholds)
- All present modalities are updated consistently (only subset those that exist in the .h5mu)
- Filtering summary is displayed with per-sample statistics
- Output file `samples_filtered.h5mu` is written successfully
- Metrics CSV is generated with QC summary per sample
</self_eval_criteria>
