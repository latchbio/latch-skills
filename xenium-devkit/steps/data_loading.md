# Step 1 — Data Loading

<goal>
Load `.h5ad` Xenium data, attach spatial imagery, and expose basic structure (cells, genes, embeddings, clusters) to the user.
</goal>

<method>
- Use Scanpy to read `.h5ad`, infer spatial coordinates in `adata.obsm`, and render with `w_h5(adata, spatial_dir)`.

- For multiple `.h5ad`s, merge them and add a `batch_key`.

- **Assumptions**: Each sample has a ready-to-use `.h5ad` with counts, metadata, and spatial coordinates stored in `adata.obsm` under a key that:
   - contains the word `"spatial"`, and
   - is a numeric array with shape `(n_cells, 2–3)`.

- **Guidelines**:
   - Load the `.h5ad` and render with `w_h5(adata, spatial_dir)`, where `spatial_dir` is the folder containing the `.pmtiles` (usually the same as the `.h5ad` directory).
   - Before preprocessing, auto-detect existing results:
     - Treat any `adata.obsm` entry as an embedding if it is a numeric 2D array with shape `(n_cells, k)` where `k` is small (e.g. 2–50).
     - Treat any `adata.obs` column as a cluster label if it is categorical or low-cardinality.
     - If such embeddings or clusters are found, assume they are valid and do **not** recompute yet; ask for confirmation in Step 2 before overwriting.
   - If multiple samples are provided:
     - Merge `.h5ad` files into a single `AnnData` and add `adata.obs["batch_key"]` to track sample of origin.
     - Create `adata.obsm["Offset"]` by shifting each sample’s spatial coordinates by a sample-specific offset so they appear side-by-side instead of overlapping.
````
</method>

<workflows>
</workflows>

<library>
- `scanpy`
- `lplots.widgets.h5` (or equivalent `w_h5`)
</library>

<self_eval_criteria>
- Spatial coordinates are detected and displayed correctly in the viewer.
- For multi-sample inputs, `adata.obs["batch_key"]` is present and valid.
- Pre-existing embeddings and cluster labels, if present, are preserved and not overwritten without confirmation.
</self_eval_criteria>
