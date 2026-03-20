<goal>
Compare differences in genes, peaks, and motifs between user-defined cluster/condition groupings.
</goal>

<method>
### Creating compare_config.json

- Inspect the user's input folder and automatically load any `combined_sm_ge.h5ad` file found into an AnnData object.
- Visualize H5AD file with `w_h5`

Create groupings dictionary with "groupA" and "groupB" barcode lists based on user's comparison request (e.g., by condition, sample, or cluster). Save as JSON and upload to Latch Data as LatchFile.

### Formatting Correct Input to `archrproject`

- When using `w_ldata_picker` to populate the `ArchRProject` path, always extract the LData path string via `widget.value.path` before passing it into LatchDir(...).
- Automatically search the user's input for the folder that ends with `_ArchRProject`. Only ask the user to specify it if you cannot find one.

**Workflow Duration**: 30 minutes - 1+ hour. Wait for workflow to complete before proceeding.
</method>

<workflows>
wf.__init__.compare_workflow
</workflows>

<library>
</library>

<self_eval_criteria>
</self_eval_criteria>
