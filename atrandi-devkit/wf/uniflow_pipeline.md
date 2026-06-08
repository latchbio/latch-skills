<goal>
The uniflow RNA:DNA co-seq pipeline processes raw FASTQ files into per-sample .h5mu files containing gene expression, amplicon, and SNP modalities. This pipeline runs externally (upstream) and its outputs are the starting point for this devkit's analysis.
</goal>

<parameters>
The uniflow pipeline is not invoked by this devkit. It runs as an independent Nextflow pipeline prior to secondary analysis. Its outputs are fetched via S3 in the sample aggregation step.

Expected pipeline outputs per sample:
- `counts/counts.h5mu` — multi-modal count matrix
- `dev/full_read_RNA.parquet` — per-read RNA data with STAR tags (GN, UR, UB, CB)
- `dev/full_read_DNA.parquet` — per-read DNA data (optional)
- `metrics/*.yaml` — per-process metrics files
</parameters>

<outputs>
- Per-sample `.h5mu` files with three modalities (gene_expression, amplicon, snp)
- Per-read parquet files for saturation curve recalculation
- YAML metrics files for QC aggregation
</outputs>

<example>
This workflow is not invoked by the agent. It runs upstream. To access its outputs:

```python
# The sample sheet points to S3 locations of pipeline output
# Example sample sheet format:
# sample_name,experiment_id,s3_path
# sampleA,EXP001,s3://bucket/path/to/pipeline/output

# The agent fetches these via the sample_aggregation step
```
</example>
