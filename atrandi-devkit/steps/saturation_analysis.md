<goal>
Generate sequencing saturation curves by subsampling reads to increasing depths, and compare Atrandi RNA:DNA co-seq performance against 10x Chromium v3.1 and v4 reference datasets. These curves inform whether additional sequencing would meaningfully increase gene/UMI detection.
</goal>

<method>
1. Load per-read RNA parquet data (from uniflow pipeline output `full_read_RNA.parquet`) for each sample:
   ```python
   import polars as pl
   full_read = pl.read_parquet(parquet_path)
   ```

2. Filter to reads belonging to called cells (from the cell calling step).

3. Generate saturation curves by subsampling reads at decreasing depths using `get_saturation_curve_cells_reverse`:
   ```python
   from lib.library_qc import get_saturation_curve_cells_reverse, REFERENCE_DATASETS
   
   sat_df = get_saturation_curve_cells_reverse(
       full_read=full_read,
       data_input="filtered",
       barcode_col="CB",
       top_cells=top_cells_df,
       step=5000
   )
   ```

4. At each subsampled depth, compute:
   - Median UMI counts per cell
   - Median genes per cell
   - Sequencing saturation rate: `1 - (unique_molecules / total_reads)`

5. Plot comparative saturation curves overlaying sample data with 10x reference datasets:
   ```python
   from lib.library_qc import REFERENCE_DATASETS, plot_comparative_saturation_curves
   
   # Reference datasets available:
   # - "10x_v4_filtered" (max ~22k reads/cell, saturation ~47%)
   # - "10x_v3.1_filtered" (max ~48k reads/cell, saturation ~74%)
   
   combined = pl.concat([sat_df, REFERENCE_DATASETS["10x_v4_filtered"]])
   plot_comparative_saturation_curves(combined, sample_name, "filtered")
   ```

6. Generate three faceted plots per sample:
   - Mean reads per cell vs median UMI counts per cell
   - Mean reads per cell vs median genes per cell
   - Mean reads per cell vs saturation rate

Parameters:
- `PLOT_10X`: whether to include 10x reference curves (default: True)
- Step sizes for subsampling are generated via `generate_round_descending_range()` with additional fine points at 2500, 1000, 500 reads/cell
</method>

<workflows>
</workflows>

<library>
- `lib.library_qc` — `get_saturation_curve_cells_reverse()`, `get_saturation_metrics_df()`, `plot_saturation_curves()`, `plot_comparative_saturation_curves()`, `REFERENCE_DATASETS`
</library>

<self_eval_criteria>
- Saturation curves are generated for each sample with at least 5 subsampled points
- Curves show expected monotonically increasing UMIs/genes with diminishing returns at higher depths
- Saturation rate is between 0 and 1 and increases with sequencing depth
- 10x reference data is overlaid for comparison when PLOT_10X is True
- If saturation is below 30% at maximum depth, flag that additional sequencing may be beneficial
</self_eval_criteria>
