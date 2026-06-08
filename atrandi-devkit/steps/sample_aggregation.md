<goal>
Collect uniflow RNA:DNA co-seq pipeline outputs from S3 for all samples of interest and aggregate individual sample-level .h5mu files into a single joint unfiltered .h5mu annotated with sample name, experiment ID, and basic RNA-based count metrics.
</goal>

<method>
1. Load the sample sheet CSV in format `<sample_name>,<s3_preprocessed_path>` (with columns: `sample_name`, `experiment_id`, `s3_path`).

2. Validate that all required S3 files exist for each sample:
   - Required files: `counts/counts.h5mu`, `dev/full_read_RNA.parquet`
   - Optional files: `dev/full_read_DNA.parquet`
   - Required directories: `metrics/`
   - Note: the exact pipeline output structure may evolve between versions. Adapt file paths if the pipeline layout has changed.

3. Sync all sample files from S3 to a local working directory using `aws s3 cp` / `aws s3 sync`.

4. For each sample, load the `.h5mu` file using `muon.read()` or `mudata.read()`.

5. Annotate each sample's MuData object with metadata in `.obs`:
   - `sample_name`
   - `experiment_id`
   - Basic RNA metrics: total UMI counts, number of genes detected

6. Concatenate all sample-level MuData objects into a single joint `.h5mu`:
   ```python
   import mudata as md
   combined = md.concat(mudata_list, label="sample_name")
   ```

7. Parse STAR alignment logs (if available in `metrics/`) to collect mapping statistics per sample.

8. Collect pipeline metrics from YAML files using `MetricsCollector`:
   ```python
   from lib.metrics.metrics import MetricsCollector
   collector = MetricsCollector()
   collector.scan_dir(metrics_path)
   collector.aggregate()
   ```

9. Save the aggregated object:
   - Output: `samples_aggregated-raw.h5mu`
   - Save the sample sheet used: `aggregator_sample_sheet.csv`

Parameters:
- `SAMPLE_SHEET`: path to the aggregation sample sheet
- `OUTPUT_DIR`: output directory (default: `outputs/aggregator`)
- `CPU`: number of CPUs for parallel .h5mu loading (default: 4)
</method>

<workflows>
</workflows>

<library>
- `lib.metrics.metrics` — MetricsCollector for YAML metrics aggregation
</library>

<self_eval_criteria>
- All samples in the sample sheet are present in the aggregated .h5mu
- Expected modalities are present in the combined object (gene_expression is required; amplicon and snp depend on pipeline version and panel)
- Sample-level obs annotations (sample_name, experiment_id) are correctly assigned
- The output file `samples_aggregated-raw.h5mu` is written successfully
- Total number of barcodes across samples is reasonable (not truncated or duplicated)
- If any expected files are missing from S3, report clearly which samples/files failed
</self_eval_criteria>
