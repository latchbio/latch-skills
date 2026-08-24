# Launching `takara_de_gsea`

**Only after explicit consent.** See the inverted gate bias in
`steps/05-gsea.md`.

Same non-blocking launch-plus-resume pattern as `wf/deseq2_wf.md`; this is the
slowest stage, so it matters more here.

```python
gsea = w_workflow(
    label="Run gene set enrichment",
    wf_name="takara_de_gsea.workflow.gsea",
    params={"results_file": "{{RUN_DIR}}/deseq2/results.csv",
            "run_dir": "{{RUN_DIR}}",
            "id_format": "{{ID_FORMAT}}", "organism": "{{ORGANISM}}"},
    automatic=True,
    key="gsea_launch",
)
```

The launch and resume cells go in the tab named **5 (optional). GSEA**, created only after the user consents. Name it in chat when you
create it and again when the results land in it.

Outputs under `{{RUN_DIR}}/gsea/`: `gsea_results.csv` (always, even when empty),
`gsea_metrics.json`, and `gsea_dotplot.png` only when there are hits.

If the run fails, the session still opens — go to `steps/06-explore.md`. Do not
trap the user in a failed optional stage.
