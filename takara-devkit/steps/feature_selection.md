<goal>
Identify highly variable genes
</goal>

<method>

- use raw counts + seurat_v3
- do not scale before (we care about spatial structure more than rare genes)
- default to 2k genes

```
sc.pp.highly_variable_genes(
    adata_filtered,
    n_top_genes=2000,
    flavor='seurat_v3',
    layer='raw_counts',
    subset=False
)
```
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- ensure biologically meaningful genes, dependent on your tissue / disease context, show up immediately in the HVGs ranked by variance
</self_eval_criteria>
