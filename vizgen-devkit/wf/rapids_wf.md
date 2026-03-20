<goal>
Run GPU-accelerated single-cell preprocessing with scRAPIDS.
</goal>

<parameters>
- **Workflow name**
  - `wf.__init__.rapids_single-cell_preprocessing`
  - Always prefer this workflow over hand-written GPU preprocessing code.

---

### Required Inputs

- **`input_file`** → `LatchFile`
  - H5AD file containing the input AnnData.
  - Typically created by first saving the current `adata` from the notebook to Latch Data.
  - Must be a valid AnnData/H5AD object.

- **`output_directory`** → `LatchOutputDir`
  - Latch Data directory where workflow outputs will be written.
  - The main output will be:
    - `{output_directory}/{run_name}/preprocessed.h5ad`

- **`run_name`** → `str`
  - Short identifier for this run (e.g., `"rapids_1"`).
  - Used to namespace outputs within `output_directory`.

---

### Optional Inputs — QC & Core Processing

- **`min_genes`** → `int` (default: `3`)
  - Minimum genes per cell to retain during QC (if QC is not skipped).

- **`min_counts`** → `int` (default: `10`)
  - Minimum total counts per cell to retain during QC (if QC is not skipped).

- **`skip_qc`** → `bool`
  - `True`  → assume dataset has already been QC-filtered; no additional filtering.
  - `False` → run QC + filtering and store raw counts in `adata.layers["counts"]`.
  - Before setting this flag, inspect the input `adata`:
    - look for QC fields, evidence of prior filtering, and/or user indication that QC is done.

- **`skip_normalization`** → `bool`
  - `True`  → assume input is already normalized; skip normalization + log transform.
  - `False` → perform `normalize_total` + `log1p`.
  - Decide this by examining the matrix (log-like values, existing normalization metadata) and user context.

- **`skip_pca`** → `bool`
  - `True`  → keep existing PCA in `adata.obsm["X_pca"]` (if valid).
  - `False` → recompute PCA.
  - Check for an existing, valid `X_pca` and associated PCA metadata before setting.

- **`skip_umap`** → `bool`
  - `True`  → reuse existing neighbors + UMAP (if present).
  - `False` → recompute neighbors and UMAP.
  - Inspect `adata.obsm["X_umap"]` and neighbor graphs in `adata.obsp` when deciding.

- **`n_comps`** → `int` (default: `50`)
  - Number of principal components to compute/use.

- **`n_neighbors`** → `int` (default: `15`)
  - Number of neighbors (`k`) used to build the kNN graph.

---

### Batch Correction

- **`batch_key`** → `str` or `None`
  - Name of a **categorical** column in `adata.obs` to use for batch correction.
  - If set, Harmony-based correction is applied in the workflow.
  - Typically chosen from existing `adata.obs` columns after inspection.

---

### Clustering

- **`clustering_resolution`** → `List[float]` (e.g., `[0.3, 0.5, 0.7, 1.0]`)
  - Multiple resolutions will produce multiple cluster label columns:
    - `clustering_{method}_{resolution}` in `adata.obs`.

- **`clustering_method`** → `str` (default: `"leiden"`)
  - Either `"leiden"` or `"louvain"`.

- **`skip_clustering`** → `bool`
  - `True`  → skip clustering (use existing labels).
  - `False` → run clustering at all specified resolutions.
  - Before setting:
    - inspect `adata.obs` for existing cluster labels (e.g., leiden/louvain or project-specific labels)
    - and consider user-provided intent (e.g., “clusters already computed”).

---

### Differential Expression

- **`skip_differential_expression`** → `bool`
  - `True`  → no new DE is computed.
  - `False` → run DE per cluster.

- **`clustering_column`** → `str` or `None`
  - Name of the `adata.obs` column to use as the cluster key for DE.
  - Required when:
    - `skip_clustering = True` and
    - DE is enabled.
  - DE results are written to:
    - `adata.uns["rank_genes_groups_{cluster_key}"]`.

---

### Internal Decision Logic (for `skip_*` flags)

Before constructing `params`:
- Inspect the input `adata` plus notebook context and user instructions.
- For each processing stage (QC, normalization, PCA, UMAP, clustering, DE):
  - Check for the **existence and structure** of the corresponding fields:
    - QC indicators, layers, or absence of low-quality cells.
    - Normalization metadata or log-transformed matrices.
    - `adata.obsm["X_pca"]`, `adata.obsm["X_umap"]`, graphs in `adata.obsp`.
    - Existing clustering columns in `adata.obs`.
    - Existing DE results in `adata.uns`.
- Set `skip_*` flags accordingly; **do not rely on hard coded numeric thresholds**.
</parameters>

<outputs>
- **Primary output:** `preprocessed.h5ad`  
  - Location:
    - `{output_directory}/{run_name}/preprocessed.h5ad`
  - Contains:
    - QC metrics  
    - Normalized/log-transformed counts  
    - PCA (and Harmony embeddings if `batch_key` provided)  
    - Neighbors graph  
    - UMAP embedding  
    - Cluster labels for all resolutions  
    - Differential expression results under:
      - `adata.uns["rank_genes_groups_{cluster_key}"]`
</outputs>

<example>
```python
from lplots.widgets.workflow import w_workflow
from lplots.widgets.text import w_text_output
from latch.types import LatchFile, LatchOutputDir

# Example: previously saved AnnData to Latch as an H5AD
input_file = LatchFile("latch://12345.account/my_project/input_adata.h5ad")

params = {
    "input_file": input_file,
    "output_directory": LatchOutputDir("latch:///Rapids_Output"),
    "run_name": "rapids_1",

    # QC and core processing
    "min_genes": 3,
    "min_counts": 10,
    "skip_qc": False,
    "skip_normalization": False,
    "skip_pca": False,
    "skip_umap": False,
    "n_comps": 50,
    "n_neighbors": 15,

    # Batch correction
    "batch_key": None,  # or e.g. "batch" if present in adata.obs

    # Clustering
    "clustering_resolution": [0.3, 0.5, 0.7, 1.0],
    "clustering_method": "leiden",
    "skip_clustering": False,

    # Differential expression
    "skip_differential_expression": False,
    "clustering_column": None,  # set if skip_clustering=True and DE is enabled
}

w = w_workflow(
    wf_name="wf.__init__.rapids_single-cell_preprocessing",
    key="rapids_singlecell_preprocessing_run_1",
    version=None,
    params=params,
    automatic=True,
    label="RAPIDS Single-Cell Preprocessing",
)

execution = w.value

if execution is not None:
    res = await execution.wait()

    if res is not None and res.status == "SUCCEEDED":
        w_text_output(
            content="✓ RAPIDS single-cell preprocessing workflow completed!",
            appearance={"message_box": "success"},
        )
