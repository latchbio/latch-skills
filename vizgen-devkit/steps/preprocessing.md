<goal>
Determine preprocessing path based on dataset size and route to the appropriate workflow or Scanpy-based preprocessing.
</goal>

<method>
1/ **Check dataset size**  
   - Inspect the AnnData object and determine whether it contains **more than 100,000 cells**.

2/ **If `n_cells > 100,000`**  
   - **Always follow the RAPIDS preprocessing instructions** described in `wf/rapids_wf.md`.  
   - Launch and complete the GPU-accelerated preprocessing workflow before moving forward.  
   - Proceed directly to the **Spatial Analysis Step** afterward.

3/ **If `n_cells ≤ 100,000`**  
   - **Skip RAPIDS**.  
   - **Always follow the Scanpy preprocessing instructions** described in `steps/scanpy_preprocessing.md`.  
   - After completing these steps, proceed to the **Spatial Analysis Step**.
</method>


<workflows>
wf.__init__.rapids_single-cell_preprocessing
</workflows>

<library>
</library>

<self_eval_criteria>
</self_eval_criteria>
