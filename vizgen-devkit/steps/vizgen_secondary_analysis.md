<goal>
Perform secondary analysis on Vizgen MERFISH data, including cell-type annotation and spatial domain detection.
</goal>

<method>
1/ **Cell Type Annotation**  
   - Prompt the user for **tissue** and **organism** using lplots widgets.  
   - Assign biological meaning to clusters using curated **marker-gene dictionaries**.  
   - Display **dot plots** showing cluster-level markers and corresponding annotated cell types.

2/ **Prepare AnnData for Domain Detection**  
   - Ensure spatial coordinates exist under `adata.obsm["X_spatial"]`.  
     - If `adata.obsm["Spatial"]` exists, rename it to `adata.obsm["X_spatial"]`.  
   - Allow the user to choose:
     - A **filename** for the processed H5AD.  
     - A **directory** in LData where the file will be saved.  
   - Write the processed object to H5AD and upload it to the selected LData location.

3/ **BANSkY / Domain Detection Workflow Launch**  
   - Expose a small form for:
     - `run_name`  
     - `output_dir` (`LatchDir`)  
     - `lambda_list` (string of values)  
   - Use these values to construct the workflow `params` dictionary.  
   - Invoke the BANSkY workflow using `w_workflow` and wait for completion before moving forward.

4/ **Post-Workflow Actions**  
   - Load domain assignments and spatial/domain embeddings from the workflow output directory.  
   - Prepare the updated AnnData object for downstream spatial analysis.
</method>

<workflows>
wf.__init__.domain_detection_wf
</workflows>

<library>
</library>

<self_eval_criteria>
</self_eval_criteria>
