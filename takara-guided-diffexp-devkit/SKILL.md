---
name: takara-guided-diffexp-devkit
description: >
  Use this skill for differential expression analysis of any count matrix with
  DESeq2 — bulk RNA-seq, pseudobulk single-cell RNA-seq, ATAC-seq or ChIP-seq
  peak counts, CUT&RUN, Ribo-seq, CRISPR screen counts, or any features-by-samples
  matrix of raw integer counts. Also use it when the user mentions DESeq2,
  differential expression, DEGs, log2 fold change, adjusted p-values, a volcano
  plot, an MA plot, a counts table or coldata, comparing two sample groups or
  conditions, or gene set enrichment and GO analysis on a ranked gene list.
  Accepts CSV or TSV with genes in rows and samples in columns; identifiers may
  be HGNC symbols, Ensembl gene IDs, or Ensembl-ID/symbol pairs. Guides a
  five-stage workflow with confirmation gates, launching versioned Latch
  workflows for all computation.
---

# Guided DESeq2 differential expression

Five stages, each gated on the user's confirmation:

1. **Upload** — pick a raw counts table → launch `takara_de_prepare_counts` → `steps/01-upload.md`
2. **Confirm groupings** — per-sample control/treated picker → `steps/02-groups.md`
3. **Review QC** — launch `takara_de_qc`, show PCA and correlation → `steps/03-qc.md`
4. **Run DESeq2** — launch `takara_de_deseq2` → `steps/04-deseq2.md`
5. **Optional enrichment** — offer `takara_de_gsea`, never automatic → `steps/05-gsea.md`

After stage 4 succeeds and the stage-5 decision is resolved, exploratory mode
becomes available → `steps/06-explore.md`. Ad-hoc plots and tables are available
at **any** stage, under the same limits.

Each stage owns one notebook tab, named exactly: `1. Upload`,
`2. Sample Groups`, `3. Quality Check`,
`4. Differential Expression`, `5 (optional). GSEA`, plus
`Exploration — <what it shows>` tabs created on demand. See `main.md`.

## Absolute rules

These are not style preferences. Violating any one of them breaks the
guarantee this skill exists to provide.

- **Never author or execute R.** Never write a `.R` file. Never call `Rscript`
  through `Bash`. All R lives in the workflow repo and runs inside a versioned
  container.
- **Never compute a statistic in a notebook cell.** No `scipy.stats`, no
  `statsmodels`, no hand-rolled p-values, fold changes, normalisation or
  multiple-testing correction. Every number shown to the user comes from a
  workflow output file.
- **Never edit a cell template.** Insert the code blocks in `steps/` verbatim,
  substituting only the declared `{{PLACEHOLDERS}}`. You choose which template
  and when; you never choose what it does.
- **Never launch a workflow with a non-default statistical parameter without
  saying so in chat first**, naming the parameter, the default, and the new
  value.
- **Never skip a gate.** Each stage waits for confirmation, by button or by
  chat. Both routes work at every gate, always.
- **Never report output without naming the tab it is in.** The notebook does not
  switch to a new tab, so a result the user cannot find is a result they never
  got. Never use "above", "below" or any other spatial reference in chat.

## Reading order

Read `main.md` before starting. Read each `steps/*.md` at the moment you reach
that stage, not in advance.
