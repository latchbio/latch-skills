<goal>
Neighborhood and clustering (eg. Leiden).
</goal>

<method>

- PCA
Compute neighbors if it doesn't exist, apply **Leiden clustering** (start with
a reasonable range of resolutions like [0.2, 0.5, 0.7]) on the neighborhood
graph. **Always** display clusters on the UMAP and spatial embedding using
`w_h5`.
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- Ensure ~70k–90k beads for Seeker 3x3 or ~0.8–1.1M beads for Seeker 10x10
- Ensure there are ~30K gene features
</self_eval_criteria>
