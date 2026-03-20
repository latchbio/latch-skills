<goal>
Load Vizgen MERFISH data into AnnData with spatial context.
</goal>

<method>
1/ **Accept user input**
- Allow the user to provide either:
  - an **H5AD file**, or  
  - a **directory with raw Vizgen MERSCOPE images**.

2/ **Case A – User provides an H5AD file**
- Check that the input is a valid H5AD and load it with **Scanpy** into an `AnnData` object.
- If the user provided **only** an H5AD file:
  - Ask them to also provide a **spatial directory**.
  - The spatial directory must contain **pmtiles**.
- Once both are available:
  - Call **`w_h5`** with:
    - the loaded `AnnData` object, and  
    - the spatial directory path.
- Use this widget to visualize the data + spatial context.
- Note: spatial coordinates are typically stored in `adata.obsm["spatial"]` or `adata.obsm["X_spatial"]`; confirm their presence.

3/ **Case B – User provides a raw Vizgen MERSCOPE dataset directory**
- Verify that the images directory contains:
  - `cell_metadata.csv`
  - `cell_by_gene.csv`
  - `micron_to_mosaic_pixel_transform.csv`
- Define:
  - `dataset_dir` → top-level MERFISH dataset directory
  - `counts_file` → path to `cell_by_gene.csv`
  - `meta_file` → path to `cell_metadata.csv`
  - `transformation_file` → path to `micron_to_mosaic_pixel_transform.csv`
- Create an `AnnData` object using **Squidpy**:
  ```python
  adata = sq.read.vizgen(
      path=dataset_dir,
      counts_file=counts_file,
      meta_file=meta_file,
      transformation_file=transformation_file,
  )

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- AnnData shows ~50,000 cells (typical for Vizgen MERFISH)
- Gene count reflects Vizgen gene panel (hundreds of genes, not full transcriptome)
- Spatial coordinates are present and span biologically plausible ranges
- Cell metadata includes expected fields (e.g., volume, spatial positions)
</self_eval_criteria>
