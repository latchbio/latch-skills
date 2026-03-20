<goal>
Infer cell types by finding cluster markers **within each sample**, then consolidating evidence across samples.
</goal>

<method>
## Prerequisites
- `adata.obs["cluster"]`
- If multi-sample: `sample` / `condition` / `batch`
- Expression in `adata.X` or a relevant layer
- Organism + tissue context

## Workflow
1. **Check samples**
   - Multi-sample → annotate per sample
   - Single-sample → annotate once

2. **Find markers**
   - Run **1-vs-all DE** per cluster
   - If multi-sample, do this **within each sample**

3. **Build consensus**
   - For each cluster, identify:
     - **Core markers** (recurrent across samples)
     - **Majority markers** (recurrent in most samples)

4. **Manual labeling**
   - Read top markers
   - Assign best-fit cell type in tissue context
   - Note alternates if shared markers

5. **Finalize across samples**
   - High confidence if markers and identity agree across samples

</method>
