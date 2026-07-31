<goal>
Identify top differentially expressed genes between clusters.
</goal>

<method>
- identify **marker genes per cluster** using rank-based DGE tests:
- Default method: t-test_overestim_var (automatically selected in the widget unless the user specifies another method).
- Allow the user to choose alternative methods (e.g., wilcoxon, logreg).
- Report top marker genes for each cluster and Make dot plots with scanpy.
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- The user was told, in chat, which tab holds the marker tables, dot plots, and the method widget
</self_eval_criteria>

<new_tab_notice>
The per-cluster marker tables, the dot plots, and the method-selection widget open in a **new tab**
that the notebook does not switch to. Name it in chat — see "Telling the user where results
appeared" in `SKILL.md`:

> Marker genes are computed for all 14 clusters (t-test_overestim_var). The tables and dot plots are
> in a **new tab** named **Differential expression** — click it in the notebook. The method selector
> is in that tab too if you'd like to try wilcoxon or logreg.
</new_tab_notice>
