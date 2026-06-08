<goal>
Apply biological QC filtering on RNA metrics (mitochondrial, ribosomal, globin fractions), normalize counts for sequencing depth, and select highly variable genes (HVGs) for downstream dimensionality reduction and clustering.
</goal>

<method>
1. Load filtered `.h5mu` from the previous step and work on the `gene_expression` modality.

2. Annotate gene categories for QC:
   ```python
   import scanpy as sc
   
   adata = mdata["gene_expression"]
   
   # Mitochondrial genes
   adata.var["mt"] = adata.var_names.str.startswith("MT-")
   # Ribosomal genes
   adata.var["ribo"] = adata.var_names.str.startswith(("RPS", "RPL"))
   # Globin genes
   adata.var["globin"] = adata.var_names.str.startswith("HB") & ~adata.var_names.str.startswith("HBS")
   
   sc.pp.calculate_qc_metrics(adata, qc_vars=["mt", "ribo", "globin"], inplace=True)
   ```

3. Apply biological QC thresholds:
   ```python
   # Default thresholds
   MITO_THR = 10       # max % mitochondrial
   RIBO_THR = 60       # max % ribosomal
   GLOBIN_THR = 10     # max % globin
   NGENES_THR = 250    # min genes per cell
   NCOUNT_THR = 1000   # min UMI counts per cell
   
   adata = adata[
       (adata.obs["pct_counts_mt"] < MITO_THR) &
       (adata.obs["pct_counts_ribo"] < RIBO_THR) &
       (adata.obs["pct_counts_globin"] < GLOBIN_THR) &
       (adata.obs["n_genes_by_counts"] >= NGENES_THR) &
       (adata.obs["total_counts"] >= NCOUNT_THR)
   ].copy()
   ```

4. Filter genes expressed in too few cells:
   ```python
   sc.pp.filter_genes(adata, min_cells=MIN_CELLS_EXPRESSED)  # default: 3
   ```

5. Normalize and log-transform:
   ```python
   # Store raw counts
   adata.layers["raw_counts"] = adata.X.copy()
   
   # Normalize to median total counts
   sc.pp.normalize_total(adata)
   sc.pp.log1p(adata)
   ```

6. Select highly variable genes:
   ```python
   sc.pp.highly_variable_genes(
       adata,
       n_top_genes=N_VAR_GENES,  # default: 2500
       flavor="seurat_v3",
       layer="raw_counts"
   )
   ```

7. Optionally remove immune receptor variable (IRV) and mitochondrial genes from HVGs:
   ```python
   if REMOVE_IRV:
       irv_pattern = "^(IGH|IGK|IGL|TRA|TRB|TRD|TRG)"
       adata.var["highly_variable"] &= ~adata.var_names.str.match(irv_pattern)
   if REMOVE_MITO:
       adata.var["highly_variable"] &= ~adata.var["mt"]
   ```

8. Optionally regress out covariates (e.g., cell cycle, sample batch):
   ```python
   if REGRESS_COVAR is not None:
       sc.pp.regress_out(adata, [REGRESS_COVAR])
   ```

Parameters (all thresholds are tissue-dependent starting points — adjust based on QC distributions):
- `MITO_THR`: max mitochondrial % (default: 10; may need to be higher for metabolically active tissues)
- `RIBO_THR`: max ribosomal % (default: 60; rarely needs adjustment)
- `GLOBIN_THR`: max globin % (default: 10; relevant mainly for blood/bone marrow)
- `NGENES_THR`: min genes per cell (default: 250; increase for deeper-sequenced libraries)
- `NCOUNT_THR`: min UMI counts per cell (default: 1000; should align with cell-calling threshold)
- `MIN_CELLS_EXPRESSED`: min cells a gene must be detected in (default: 3)
- `N_VAR_GENES`: number of HVGs to select (default: 2500; adjust based on dataset complexity)
- `REMOVE_IRV`: drop immune receptor variable genes from HVGs (default: True; set False for immune-focused studies)
- `REMOVE_MITO`: drop mitochondrial genes from HVGs (default: True)
- `REGRESS_COVAR`: obs column to regress out (default: None)

Note: Gene prefix patterns assume human genome annotation (e.g., "MT-", "RPS", "RPL", "HB"). For other organisms, adjust the prefix patterns accordingly.
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- QC violin/scatter plots are generated for mito%, ribo%, globin%, n_genes, n_counts
- Biological filtering does not remove more than 30% of cells (if it does, thresholds may be too strict)
- After filtering: no cells with >MITO_THR% mitochondrial reads
- HVG selection produces N_VAR_GENES genes (minus any removed IRV/mito)
- Raw counts are preserved in adata.layers["raw_counts"]
- Normalized log-transformed data is in adata.X
</self_eval_criteria>
