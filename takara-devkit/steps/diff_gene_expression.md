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
</self_eval_criteria>
