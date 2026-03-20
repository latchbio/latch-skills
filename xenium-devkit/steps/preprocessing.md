# Step 2 — Preprocessing (run only if the user confirms)

<goal>
Create a clean, integrated embedding and cluster structure ready for differential expression and cell-type annotation.
</goal>

<method>
- If `adata.n_obs > 100_000`, you **must** use RAPIDS for preprocessing (see `technology_docs/rapids.md`) Otherwise use Scanpy to perform QC, normalization, PCA, Harmony (if needed), neighbors, UMAP, Leiden and DGE on the Xenium `AnnData`.
</method>

<workflows>
technology_docs/rapids.md
</workflows>

<library>
- `scanpy`
- `harmonypy` / `sce.pp.harmony_integrate`
- `rapids_singlecell`
- `plotly`
- `matplotlib`
</library>

<self_eval_criteria>
* QC filters remove low-quality cells without dropping all cells.
* PCA/UMAP embeddings and Leiden clusters are present and usable for downstream steps.
</self_eval_criteria>
