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
- The user was told, in chat, which tab holds the labeled embeddings, summary table, and plots
</self_eval_criteria>

<new_tab_notice>
The labeled embeddings, the summary table of counts and percentages, the dot plot, and the per-type
violin plots open in a **new tab** that the notebook does not switch to. Name it in chat — see
"Telling the user where results appeared" in `SKILL.md`:

> All 14 clusters are annotated. The labeled embeddings, summary table, and marker plots are in a
> **new tab** named **Cell type annotation** — click it in the notebook to review the labels.

Put your written per-cluster reasoning in the chat message itself, not only in that tab, so the user
can read it without switching away from wherever they are.
</new_tab_notice>
