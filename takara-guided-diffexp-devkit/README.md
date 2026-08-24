# takara-guided-diffexp-devkit

## Repo Structure

This devkit is for the Latch Agent to run guided differential expression
analysis (DESeq2) on a raw count matrix. It walks the user through a gated,
five-step workflow — upload counts, confirm sample groupings, review QC, run
DESeq2, and optionally run gene set enrichment — where each computational step
is a registered Latch workflow and the LLM never performs the statistics itself.

Components:
- `SKILL.md` — discovery metadata and the top-level operating rules
- `main.md` — the plan the agent follows, the notebook-tab discipline, and the
  registered-workflow reference table
- `steps/` — one file per user-facing step (upload, groups, QC, DESeq2, GSEA,
  and free-form exploration)
- `wf/` — one launch spec per registered Latch workflow: the `w_workflow`
  parameter-entry, launch, and resume cells
- `lib/` — notebook-side rendering and design helpers used by the step cells

## Registered workflows

The step and `wf/` cells launch these workflows on Latch compute, separately
from the notebook pod:

| Stage | `wf_name` |
|-------|-----------|
| Prepare counts | `takara_de_prepare_counts.workflow.prepare_counts` |
| Quality control | `takara_de_qc.workflow.qc` |
| Differential expression | `takara_de_deseq2.workflow.deseq2` |
| Gene set enrichment (optional) | `takara_de_gsea.workflow.gsea` |

The workflow source lives in a separate repository; this devkit contains only
the Agent-facing skill.
