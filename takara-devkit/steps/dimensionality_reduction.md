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

<new_tab_notice>
The scree plot and the UMAP embeddings open in a **new tab** that the notebook does not switch to.
Name it in chat — see "Telling the user where results appeared" in `SKILL.md`:

> PCA and UMAP are done (10 PCs, neighbors=40). The scree plot and embedding are in a **new tab**
> named **Dimensionality reduction** — click it in the notebook to see them.

You are asking the user to judge an elbow and a separation, so they have to be looking at the plots
before you ask.
</new_tab_notice>
