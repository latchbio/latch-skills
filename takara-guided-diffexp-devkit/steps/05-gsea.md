# Stage 5 — Optional gene set enrichment

**Offer it. Never launch it automatically.**

Create the tab only once the user has consented — an empty **5 (optional). GSEA** tab
sitting there reads as a promise you have not been given permission to keep.
When you do create it, name it exactly:

```
5 (optional). GSEA
```

and announce it in chat by that name, both when it is created and when the
results land in it.

## Making the offer

Say what it does and what it costs: it ranks every gene from the DESeq2 result
and tests GO biological process terms for enrichment; it takes roughly a minute
and a half on a small dataset and longer on a full table, because GO biological
process is a large term space.

Ask with `AskUserQuestion`.

## Gate — the bias is inverted here

This is the **expensive** gate. An ambiguous answer resolves toward **asking
again**, never toward running.

- Consent: "yes", "run it", "go ahead", clicking the button.
- Decline: "no", "no thanks", "skip it" — a pure state change. Run nothing.
- Anything else, including "maybe", "what would that show me?", or any
  question — answer it and leave the offer open. A question is not consent.

## Preconditions

Enrichment is human gene symbols only, via `org.Hs.eg.db`. Read `id_format` and
`organism` from `profile.json` and pass them through. Do not translate
identifiers yourself and do not guess an organism — a non-human dataset reports
that nothing mapped, which is an honest outcome.

## Cell template

```python
from lplots.widgets.workflow import w_workflow

gsea = w_workflow(
    label="Run gene set enrichment",
    wf_name="takara_de_gsea.workflow.gsea",
    params={
        "results_file": "{{RUN_DIR}}/deseq2/results.csv",
        "run_dir": "{{RUN_DIR}}",
        "id_format": "{{ID_FORMAT}}",
        "organism": "{{ORGANISM}}",
    },
    automatic=True,
    key="gsea_launch",
)
```

`ontology`, `min_gs_size`, `max_gs_size`, `pvalue_cutoff` and `seed` are omitted
so their defaults apply. The seed default of 42 matters: fgsea is randomised, so
changing it changes the results.

## What to show

Render `gsea_dotplot.png` if it exists, and the terms from `gsea_metrics.json`
with `w_table` — Term, Size, NES, adjusted p.

`gsea_results.csv` is written **even when empty**, so its existence does not
mean there were hits. Check `n_terms`.

Four outcomes, all honest, all reportable as-is:

1. **Hits** — report how many terms and the strongest, with its NES direction.
2. **No significant terms** — a real result, not a failure. The expression
   changes simply do not concentrate in any one annotated process.
3. **Fewer than 50 genes mapped** — report the results with the caveat that
   they should be read with care.
4. **Nothing mapped** — say why, using `id_format` and `organism`. The
   differential expression results are unaffected.

## After

Whether it ran, was declined, or failed, go to `steps/06-explore.md`.

## Handing off

If the tab was created — the user consented — close the turn with
`:cell{display_name="5 (optional). GSEA" type="markdown" cell_id="<id>"}`,
using the `cell_id` from this tab's heading cell. If enrichment was declined
before the tab existed, there is nothing to link — say so in chat instead.
