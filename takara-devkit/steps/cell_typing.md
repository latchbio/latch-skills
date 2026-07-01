<goal>
Identify cell types in each cluster.
</goal>

<method>
0. **If RCTD labels are present** (`first_type` / `second_type` / `spot_class` in `adata.obs`, written by `steps/rctd.md`): cross-tabulate `first_type` against the Leiden cluster column to get the per-cluster cell-type composition. For each cluster, derive the **majority RCTD `first_type`** as a reference-based consensus label, and note clusters where RCTD is mixed or mostly `reject`. Use this as independent evidence alongside the marker-based interpretation below — present both, and reconcile them (agreement strengthens the label; disagreement warrants a closer look at the markers). This is complementary: marker-based annotation below remains the default and is the sole method when RCTD was not run.

1. **Extract top 20 marker genes per cluster** (not just 5 - critical markers often appear in positions 6-20)

2. **Analyze and interpret each cluster**: Consider gene function, biological role, and tissue context. Write out your reasoning. When RCTD consensus labels exist (step 0), state whether the markers corroborate them.

3. **Apply descriptive labels**:
   - Preferred: Functional description (e.g., "Proliferating cells", "Steroidogenic cells")
   - If uncertain: Description + marker (e.g., "Stromal-like (Col1a1+)")
   - **NEVER**: "Cluster X"

4. **Validation checks**:
   - All clusters have biological interpretation (no "Cluster X" labels)
   - Proportions are biologically plausible
   - Create summary table with counts and percentages
   - Generate dot plot of top markers
   - Create one violin plot per cell type, comparing its enriched markers to other cell types. 
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
</self_eval_criteria>
