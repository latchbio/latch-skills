<goal>
Assess barcode incorporation bias across ligation steps and visualize in-cell read statistics for both RNA and DNA libraries. This QC step identifies systematic biases in the combinatorial barcoding that may affect data quality.
</goal>

<method>
1. Load barcode reference lists and corrected barcode data for each sample.

2. Visualize barcode occurrence across plate positions (A, B, C, D ligation steps) as heatmaps:
   ```python
   from lib.plotting.barcode import prepare_barcode_occurence_data, plot_barcode_occurence_heatmap
   
   summarized = prepare_barcode_occurence_data(df, reference_list)
   plot_barcode_occurence_heatmap(
       summarized, cumsum_fraction=0.95, sample_name=sample_name,
       library_type="RNA", barcode_pool_size=96, indices=indices
   )
   ```

3. Plot fraction-of-reads heatmaps per barcode position to detect over/under-represented barcodes:
   ```python
   from lib.plotting.barcode import plot_fraction_barcodes_heatmap
   
   plot_fraction_barcodes_heatmap(corrected, ref_df, sample_name, sample_out)
   ```
   - Expected: uniform ~1/96 fraction per barcode within each position
   - Flag barcodes that deviate more than 75% from the expected mean frequency

4. Generate barcode upset plots showing the fraction of reads with valid barcode combinations:
   ```python
   from lib.plotting.barcode import plot_barcode_upset_plot
   
   plot_barcode_upset_plot(raw_bc_corrected, ref_df, sample_name, library_type="RNA", indices=indices)
   ```
   - The "Correct" (green) category should represent the majority of reads
   - Reads with all 4 barcode positions detected indicate proper ligation

5. Compute and display in-cell read statistics per sample:
   - Total reads assigned to cells vs background
   - Fraction of reads with valid barcodes
   - Per-library (RNA/DNA) read assignment rates

6. Compare across samples to identify systematic library prep issues.

Parameters:
- Barcode pool size: varies by kit configuration (commonly 24 or 96 barcodes per ligation position). Ask the user if unknown.
- Cumulative fraction for heatmap display: top 95% of reads
- The 4-position combinatorial barcoding (D, C, B, A) is the standard Atrandi architecture; future kits may differ.
</method>

<workflows>
</workflows>

<library>
- `lib.plotting.barcode` — `prepare_barcode_occurence_data()`, `plot_barcode_occurence_heatmap()`, `plot_fraction_barcodes_heatmap()`, `plot_barcode_upset_plot()`
- `lib.plotting.common` — `plot_generic_upset_plot()`
- `lib.common_const` — `BARCODE_A`, `BARCODE_B`, `BARCODE_C`, `BARCODE_D`, `LibraryType`
</library>

<self_eval_criteria>
- Barcode occurrence heatmaps show no completely missing rows/columns (positions)
- Fraction heatmaps show relatively uniform distribution within each ligation step
- Upset plots show >80% of reads have all barcode positions correctly detected
- In-cell read fractions are documented per sample and library type
- Any systematic biases are flagged and reported to the user
</self_eval_criteria>
