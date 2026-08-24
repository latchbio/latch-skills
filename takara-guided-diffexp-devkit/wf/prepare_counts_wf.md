# Launching `takara_de_prepare_counts`

Fast stage — a `@small_task` that parses the table. `automatic=True` is fine.

```python
ingest = w_workflow(
    label="Profile the counts table",
    wf_name="takara_de_prepare_counts.workflow.prepare_counts",
    params={"counts_file": <LPath>.path, "run_dir": "{{RUN_DIR}}"},
    automatic=True,
    key="ingest_launch",
)
```

This cell goes in the tab named **1. Upload**, beside the example counts
table. Name that tab in chat when you create it.

`key` is the idempotency handle: re-running this cell with the same key does not
relaunch. Never omit it.

**Outputs**, under `{{RUN_DIR}}/prepare_counts/`: `counts.csv`, `coldata_inferred.csv`,
`profile.json`, `similarity.json`.

`coldata_inferred.csv` is a proposal, not a design. Never pass it to `takara_de_qc` or
`takara_de_deseq2` — those take `coldata_confirmed.csv`, which stage 2 writes.
