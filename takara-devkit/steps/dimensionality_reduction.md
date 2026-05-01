<goal>
PCA then UMAP to reduce dimensions
</goal>

<method>

1/ PCA:
- Pick the number of PCs at the point where additional PCs contribute more technical noise than biological signal identified by the elbow in the scree plot
- Do not use z score scaling (we care about spatially variable genes not just rare genes).k
- Use nPCs=10 as default when in doubt

2/ UMAP:
- Try multiple values, measure biological separation using markers in tissue/disease context, and pick winner empirically. Start around neighbors=40 (spatial has more mixing per bead)

</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
1/ PCA
Make sure number of PCs chosen at point of loss of: 
- interpretable gene loadings: biologically meaningful examining positive and negative loading gene sets in context of tissue and disease
- additional PCs contribute more technical noise than biological signal

2/ UMAP
- Chosen parameters achieve best separation of tissue/disease specific markers
</self_eval_criteria>

<long_running_guidance>
If adata.n_obs > 200000, display this message to the user after running the UMAP cell:

"Your Dimensionality Reduction analysis is running on this pod notebook and may take some time to complete. Please leave this notebook open until the analysis is completed."
</long_running_guidance>
