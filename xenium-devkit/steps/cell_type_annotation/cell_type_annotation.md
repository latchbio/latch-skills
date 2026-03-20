# Step 3 — Cell Type Annotation (CellGuide-Based)

<goal>
Assign biologically meaningful cell-type labels to clusters using DGE markers and CellGuide, then (optionally) map them into a controlled vocabulary.
</goal>

<method>
This step assigns cell types to clusters by:
1. Using precomputed **cluster-level marker genes** (from DGE).
2. Matching markers to **CellGuide**.
3. Aggregating evidence per cluster with helper functions from a shared library.
4. Writing the final labels (or raw summaries) back into `adata.obs` / `adata.uns`.

---

## 0. Setup (import shared helpers)

```python
sys.path.insert(0, "/opt/latch/plots-faas/runtime/mount/agent_config/context/technology_docs/xenium/lib")

from xenium_cell_type import (
    load_json_lpath,
    load_vocab_index,
    load_cell_type_vocab_config,
    lookup_cellguide_celltypes,
    summarize_clusters,
)
````

---

## 1. High-Level Flow

1. Pick the **cluster column** in `adata.obs` and the matching **DGE key** in `adata.uns`.
2. Use `scanpy.get.rank_genes_groups_df` to obtain a tidy marker table.
3. Use `summarize_clusters(...)` to aggregate CellGuide evidence per cluster.
4. Optionally load a vocab config via `load_vocab_index` / `load_cell_type_vocab_config`.
5. Write final labels to `adata.obs["cell_type"]` and a structured summary to `adata.uns["cell_type_annotation"]`.

---

## 2. CellGuide Databases

CellGuide provides curated mappings between genes, cell types, tissues, and organisms. The library helpers expect / use:

- A **per-gene** database to ask “which cell types does this gene mark?”
- A **per-cell-type** database to ask “which genes mark this cell type?”
- A **tissue metadata** file to constrain queries to the correct organism/tissue.
- A **central vocab index** + per-tissue vocab configs for controlled labels.

Typical layout on disk:

```text
/opt/latch/plots-faas/runtime/mount/agent_config/context/technology_docs/
  xenium/
    cell_type_annotation.md
    cell_type_vocab_index.json
    cell_type_vocab_mus_musculus_brain.json
    cell_type_vocab_mus_musculus_kidney.json
```

Helper functions:

-`load_json_lpath(uri: str)`
  Download + parse JSON from an `latch:///...` URI.
- `load_vocab_index()`
  Load `cell_type_vocab_index.json` from the docs directory.
- `load_cell_type_vocab_config(organism, tissue, panel_name=None)`
  Use the central index to find and load the correct vocab config.
- `lookup_cellguide_celltypes(genes, organism, tissue, db_path)`
  Map a list of genes → CellGuide cell types for the given organism+tissue.
- `summarize_clusters(ranked_df, db_path, organism, tissue, ...)`
  Use top markers per cluster + CellGuide to produce per-cluster summaries.

---

## 3. Prerequisites

Your `AnnData` must include:

- **Cluster assignments (required)**
  A column in `adata.obs` whose name follows
  `clustering_{clustering_algorithm}_{clustering_resolution}`
  Examples:

  - `clustering_leiden_0.4`
  - `clustering_louvain_1.0`

- **Expression matrix**
  Expression values in `adata.X` or an appropriate `adata.layers[...]`
  (already used for DGE upstream).

- **DGE results**
  A `rank_genes_groups` entry in `adata.uns`, e.g.
  `rank_genes_groups_clustering_leiden_0.4`.

Additional inputs:

- Organism + tissue strings, e.g.:

  - `organism = "Mus musculus"`
  - `tissue   = "brain"`

> Tip: Inspect `adata.obs.columns` and `adata.uns.keys()` before assuming names.

---

## 4. Select Clustering and Retrieve Marker Genes

```python
import scanpy as sc

print("obs columns:", adata.obs.columns.tolist())
print("uns keys:", list(adata.uns.keys()))

cluster_col = "clustering_leiden_0.4"                  # example
dge_key = "rank_genes_groups_clustering_leiden_0.4"    # example

ranked_df = sc.get.rank_genes_groups_df(
    adata,
    group=None,   # all clusters
    key=dge_key,
)
```

`ranked_df` is a long-form DataFrame with columns like:

- `group` (cluster ID)
- `names` (gene)
- `scores`, `pvals_adj`, etc.

---

## 5. Lookup Cell Types & Summarize Clusters (via library)

### 5.1 Load CellGuide marker database

```python
db_path = "latch:///cellguide_marker_gene_database_per_gene.json"
marker_db = load_json_lpath(db_path)
```

### 5.2 Summarize clusters

```python
cluster_summary = summarize_clusters(
    ranked_df=ranked_df,
    db_path=db_path,
    organism="Mus musculus",
    tissue="brain",
    min_markers=3,
    n_core=10,
)
```

`cluster_summary` (dict keyed by cluster ID) typically contains:

- `core_markers`: Top marker genes used for CellGuide matching.
- `most_common_cell_type`: List of candidate cell types supported by ≥ min markers.
- `cell_type_counts`: Number of core markers supporting each candidate cell type.
- `markers_for_most_common_cell_type`: Subset of markers supporting the top call(s).

Store this in the AnnData object:

```python
adata.uns["cell_type_annotation_raw"] = cluster_summary
```

---

## 6. Apply Controlled Vocabulary

If a vocabulary config exists for this organism+tissue, load it and map raw CellGuide names → controlled labels.

Use `load_vocab_index` and `load_cell_type_vocab_config` to load the appropriate vocab config (for example, for `"Mus musculus"` brain). The returned `vocab_config` contains:

- `allowed_vocab`: the controlled set of labels for that panel.
- `mapping_rules`: regex or string rules to map raw CellGuide names into the controlled vocabulary.

These fields are then used **downstream** to convert the raw `most_common_cell_type` entries in `cluster_summary` into final labels for `adata.obs["cell_type"]`. The full per-cluster summary and the vocab config should be stored in `adata.uns["cell_type_annotation"]` for transparency and reproducibility.

---
</method>

<workflows>
</workflows>

<library>
- `scanpy`
- `json`
- `pathlib`
- `xenium_cell_type` (helpers:
  - `load_json_lpath`
  - `load_vocab_index`
  - `load_cell_type_vocab_config`
  - `lookup_cellguide_celltypes`
  - `summarize_clusters`
  )
- CellGuide marker databases and vocab JSONs under
  `/opt/latch/plots-faas/runtime/mount/agent_config/context/technology_docs/xenium/steps/cell_type_annotation`
</library>

<self_eval_criteria>
- A valid clustering column and matching DGE key were found and used.
- `cluster_summary` contains interpretable `most_common_cell_type` entries and supporting `core_markers`.
- If a vocab config is available, final labels in `adata.obs["cell_type"]` are restricted to `allowed_vocab`.
- Spatial and UMAP views of `adata.obs["cell_type"]` show biologically plausible patterns without placeholder categories.
</self_eval_criteria>
