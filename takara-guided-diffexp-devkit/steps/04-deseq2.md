# Stage 4 — Run DESeq2

Create a tab named exactly:

```
4. Differential Expression
```

Announce it in chat by that name when you create it, and again when the results
render in it. This is the longest wait in the session, so it is the tab most
likely to fill up while the user is looking somewhere else.

## Cell template

```python
from lplots.widgets.workflow import w_workflow

deseq2 = w_workflow(
    label="Run DESeq2",
    wf_name="takara_de_deseq2.workflow.deseq2",
    params={
        "counts_file": "{{RUN_DIR}}/confirmed/counts.csv",
        "coldata_file": "{{RUN_DIR}}/confirmed/coldata_confirmed.csv",
        "run_dir": "{{RUN_DIR}}",
    },
    automatic=True,
    key="deseq2_launch",
)
```

**Do not `await deseq2.value.wait()` here.** Use the resume-cell pattern in
`wf/deseq2_wf.md`.

All seven statistical parameters are omitted so their defaults apply:
`ref_level="control"`, `min_row_sum=10`, `lfc_shrink_type="apeglm"`,
`padj_cutoff=0.05`, `lfc_cutoff=1.0`, `top_n=30`, `heatmap_top_n=10`.
If a user asks to change any of them, name the parameter, its default and the
new value in chat **before** launching.

## What to show

Render `volcano.png`, `ma_plot.png` and `heatmap.png` with `w_plot`, and the
`top` rows from `de_metrics.json` with `w_table`.

Report from `de_metrics.json` — do not compute anything: `n_tested`, `n_sig`,
`n_up`, `n_down`, and the strongest genes by adjusted p-value. If you want a
number that is not in that file, say you do not have it.

Two things worth explaining if the user asks:

- The volcano colours points on `padj < 0.05` **alone**, not on fold change.
  A large fold change that is not significant is grey.
- Fold changes are apeglm-shrunken, so a low-count gene's effect size is pulled
  toward zero. That is what makes the ranking trustworthy.

There is deliberately no PCA here — `pca.png` belongs to stage 3.

## If it fails

`results.csv` missing is a hard error and the stage does not advance. Reopen the
QC gate and show the error.

## Then

Go to `steps/05-gsea.md` and make the offer. Do not launch anything yet.

## Handing off

Close the turn with `:cell{display_name="4. Differential Expression" type="markdown" cell_id="<id>"}`,
using the `cell_id` from this tab's heading cell — see `main.md`'s Notebook tab
discipline for the fallback when you don't have one.
