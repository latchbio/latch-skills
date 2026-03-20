<goal>
Configure Vizgen MERFISH cell segmentation and launch the workflow.
</goal>

<method>
1/ Ask the user for the **top-level Vizgen dataset directory** on Latch Data (for `vizgen_images`).  
2/ Interactively configure one or more segmentation tasks and generate a fresh `algorithm.json` in LData (ignoring any existing files).  
3/ Collect:
   - `vizgen_images` (`LatchDir`)
   - `cell_segmentation_algorithm` (`LatchFile` pointing to the new algorithm.json)
   - `output_directory` (`LatchDir` or `LatchOutputDir`, with a sensible default)
   - `run_name` (string label for this run)  
4/ Invoke the **cell segmentation workflow** using these parameters and wait for completion before any downstream analysis.  
5/ Refer to the linked workflow spec for full widget behavior, JSON schema, and implementation details.
</method>

<workflows>
wf.__init__.vizgen_cell_segmentation_wf
</workflows>

<library>
</library>

<self_eval_criteria>
</self_eval_criteria>
