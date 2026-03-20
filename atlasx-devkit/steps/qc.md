<goal>
Identify and apply filtering thresholds to counts for quality control metrics.
</goal>

<method>
**IMPORTANT**: Skip if clustering requested (workflow includes QC internally).

### Pre-check
Always verify if AnnData is pre-processed: check `adata.obs` for existing QC metrics.

### Key Metrics & Thresholds
Use `snapatac2` library. Apply adaptive filtering (per-sample quantiles):
- `n_fragments`: [max(q5, 1k), min(q99.5, 50k)]
- `tsse`: ≥ min(q10, 2)
- `frip`: ≥ min(q10, 0.2)
- `nucleosome_signal`: ≤ max(q90, 4)
- `mitochondrial_fraction`: ≤ max(q90, 0.10)

### Metrics to evaluate

1. **Fragment Size Distribution** - Assess nucleosome periodicity and library quality. Pattern: 80-300bp (open chromatin), ~150-200bp (mono), ~300-400bp (di), >500bp (multi/artifacts)

2. **TSS Enrichment (TSSE)** - Quantify enrichment near transcription start sites. Thresholds: ≥5-10 good, <4 poor

3. **FRiP - Fraction of Reads in Peaks** - Quantify fragments in called peaks (~0.2 good, <0.1 noisy)

4. **Nucleosome Signal** - Thresholds: <2 good, >4 over-digested

5. **Number of Fragments per Cell** - Field: `adata.obs["n_fragment"]`. Thresholds: <1k dropouts, very high = doublets

6. **Mitochondrial Read Fraction** - Field: `adata.obs["frac_dup"]`. Thresholds: >10% = stressed cells, can be relaxed based on adaptive filters for ATAC-seq data.
</method>

<workflows>
</workflows>

<library>
snapatac2
</library>

<self_eval_criteria>
</self_eval_criteria>
