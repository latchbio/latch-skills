<pre_analysis_questions>
- What tissue type and disease condition describe your samples?
- How many samples are being analyzed, and are they from the same experiment?
- Has the uniflow RNA:DNA co-seq pipeline already been run (i.e., do you have .h5mu files)? If so, which pipeline version?
- What amplicon panel is being used and how many targets does it contain?
- What organism is the data from (human, mouse, other)? This affects gene annotation patterns.
- Is batch integration expected to be needed (multiple sequencing runs or library preps)?
- What is the expected number of cells per sample (guides cell-calling thresholds)?
</pre_analysis_questions>

<pre_analysis_step>
MANDATORY: Set up the lib path for Atrandi helper functions.

```python
import sys
sys.path.insert(0, "/opt/latch/plots-faas/runtime/mount/agent_config/context/technology_docs/atrandi")
```

Verify the library is importable:
```python
from lib.common_const import Modality, LibraryType
from lib.barcode.filtering import knee_point, knee_cells_from_umis
print("Atrandi lib loaded successfully")
```
</pre_analysis_step>

<plan>
1. Sample Aggregation -> `steps/sample_aggregation.md`
2. Cell Calling -> `steps/cell_calling.md`
3. Saturation Analysis -> `steps/saturation_analysis.md`
4. Barcode QC -> `steps/barcode_qc.md`
5. Doublets and Ambient RNA -> `steps/doublets_and_ambient.md`
6. Amplicon QC -> `steps/amplicon_qc.md`
7. Filtering -> `steps/filtering.md`
8. Normalization -> `steps/normalization.md`
9. Dimensionality Reduction -> `steps/dimensionality_reduction.md`
10. Clustering -> `steps/clustering.md`
11. Cell Type Annotation -> `steps/cell_typing.md`
12. Amplicon Diagnostics -> `steps/amplicon_diagnostics.md`
</plan>

<data_structure>
The central data object is a `.h5mu` (MuData) file with up to three modalities sharing partially overlapping barcodes (`obs_names`):

- `gene_expression`: per-barcode UMI counts (any gene with > 0 counts in at least one barcode)
- `amplicon`: per-barcode amplicon read counts (variable number of amplicon features depending on the panel used)
- `snp`: single-nucleotide variant calls at amplicon target positions (format may evolve as variant-calling module matures; future versions may include indels)

Important: Modalities may have different numbers of barcodes with only partial overlap. Cross-modality operations (e.g., plotting amplicon reads vs RNA UMIs) require explicitly filling missing `obs_names` with 0. Not all modalities are guaranteed to be present — the `snp` modality may be absent in early pipeline versions.

Supporting files from the uniflow pipeline (structure may evolve between pipeline versions):
- `counts/counts.h5mu` — multi-modal count matrix per sample
- `dev/full_read_RNA.parquet` — per-read RNA data (STAR tags: GN, UR, UB, CB) for saturation recalculation
- `dev/full_read_DNA.parquet` — per-read DNA data (optional, may not be present)
- `metrics/` — YAML metrics files per sample/library/process
</data_structure>

<self_eval_criteria>
- The final .h5mu output should contain filtered cells with QC annotations in obs
- Saturation curves should be generated and compared against 10x references (when per-read parquet data is available)
- Cell calling should be justified by knee-curve analysis with documented UMI thresholds
- Clustering resolution should be selected with supporting diagnostics (ARI vs cell type labels, silhouette)
- Cell type annotations should be present in the final object (via SCimilarity if available, otherwise via marker genes)
- Amplicon diagnostic plots (OncoPrint-style heatmaps) should be generated when amplicon modality is present
- Steps that depend on optional modalities or tools should degrade gracefully (skip with a note, not fail)
</self_eval_criteria>
