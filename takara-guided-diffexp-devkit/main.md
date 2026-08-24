# Running the guided DESeq2 workflow

## Before you start

Ask, using `AskUserQuestion`, only what you cannot determine from the data:

- Where the counts table is, if the user has not already pointed at one.
- Nothing else. Sample groupings, gene identifier format and organism are all
  detected by `takara_de_prepare_counts` and confirmed by the user in stage 2.
  Do not ask the user to describe their experimental design in prose.

## Plan

```
<plan>
1. Upload counts       -> takara_de_prepare_counts -> profile.json, similarity.json
2. Confirm groupings   -> (no workflow)             -> coldata_confirmed.csv
3. Review QC            -> takara_de_qc              -> pca.png, sample_correlation.png
4. Run DESeq2           -> takara_de_deseq2          -> results.csv + figures
5. Optional enrichment  -> takara_de_gsea            -> gsea_results.csv + dot plot
</plan>
```

## Gate discipline

Every gate is answerable two ways: clicking the `w_button`, or typing in chat.
Both must work — a user who types "looks right, go ahead" has confirmed.

The bias is deliberately **asymmetric**:

- At the **cheap** gates (stages 2 and 3), an ambiguous answer resolves toward
  proceeding. Re-running QC costs little.
- At the **expensive** gate (stage 5), an ambiguous answer resolves toward
  **asking again**, never toward running. A wrong yes costs roughly ninety
  seconds of compute. "Maybe", "what would that tell me?", or any question is
  not consent.

An unrelated question while a gate is open is answered normally, and the gate
stays open.

Typing is not only for confirming — it can change what is on the canvas. At
stage 2, "move sample 3 to treated" is a valid instruction, and you carry it out
with the `set_widget` tool rather than asking the user to click. See
`steps/02-groups.md`. The widgets stay live and clickable throughout; the two
routes are alternatives, never a substitution of one for the other.

## Notebook tabs

The notebook canvas is the left-hand area; you are in the chat panel on the
right. **Each stage owns exactly one tab**, created by that stage's step file
with `create_tab`, named exactly as written here:

| Tab | Created by | Holds |
|---|---|---|
| `1. Upload` | `steps/01-upload.md` | The example counts table and the `w_ldata_picker`; after `takara_de_prepare_counts`, the data-check findings and the detected identifier format |
| `2. Sample Groups` | `steps/02-groups.md` | Per-sample `w_radio_group` toggles beside the reactive similarity plot, and the design table with its mislabel warning column |
| `3. Quality Check` | `steps/03-qc.md` | `takara_de_qc` outputs: PCA, sample correlation, flagged samples |
| `4. Differential Expression` | `steps/04-deseq2.md` | `takara_de_deseq2` outputs: volcano, MA, heatmap, top-genes table |
| `5 (optional). GSEA` | `steps/05-gsea.md`, only after consent | `takara_de_gsea` outputs: dot plot, enriched terms table |
| `Exploration — <what it shows>` | `steps/06-explore.md`, on demand | Anything ad-hoc, at any stage |

Names are exact, including the leading number and the period. They are how you
refer to a tab in chat, and a user hunting for "3. Quality Check" among tabs
called something else has been given a wrong direction. In chat prose, spell
enrichment out ("gene set enrichment"); "GSEA" is the tab name only.

## Notebook tab discipline

**The notebook does not switch to a newly created tab.** The user stays on the
tab they were already looking at and sees nothing happen — to them the agent has
stalled. A `w_text_output` saying "results are ready" renders inside the very tab
they have not clicked, invisible to exactly the person who needs it.

There are now six or more tabs in a finished session, so this matters more than
it did, not less:

- **After `create_tab`, wait until the next turn** before creating or editing
  cells in that tab. The tab marker shifts subsequent cell positions, so
  writing into it in the same turn can land cells in the wrong place.
- **End the turn with a `:cell{}` directive pointing at that tab's heading
  cell — this is the primary mechanism, not the tab name alone.** It renders as
  a clickable chip in chat that takes the user straight there:
  `:cell{display_name="<tab name>" type="markdown" cell_id="<id>"}`. The `id` is
  the `cell_id` that `create_markdown_cell` returned when you wrote that tab's
  heading — never invent or guess one. If you do not have it at hand, fall back
  to naming the tab in bold text rather than emitting a directive with a
  made-up id.
- **Announce every tab by its exact name in chat, every time** you create one or
  add to one. Not just the first — users do not generalise from one mention, and
  a missed tab reads as a broken agent rather than a missed click.
- **Say what is in it** and what the user should look for when they get there.
- **Never write "above", "below", "on the left", "the plot on the right", or "in
  the cell I just ran" in chat.** Relative to the tab the user is on, those
  things are somewhere else entirely. Name the tab, then place things inside it.
  Inside a `w_text_output`, which sits next to the thing it points at, "below" is
  fine.
- **Put the finding itself in chat as text**, not only in a widget. The widget is
  for the user who has clicked through; chat is for everyone.
- It matters most for anything the user must **click**. A launch button, a resume
  button or a grouping toggle sitting in an unopened tab is the same as no button
  at all.

Template — adapt the specifics, keep the structure:

> The volcano, MA plot, heatmap and top-genes table are ready. 312 genes are
> significant at padj < 0.05.
> :cell{display_name="4. Differential Expression" type="markdown" cell_id="<id from create_markdown_cell>"}

## Ad-hoc requests, at any stage

The five stages are the spine, not a cage. At **any** point the user may ask for
another visualization, another table, a different cut of numbers already
computed — before QC, while waiting on DESeq2, after enrichment, whenever.

Two rules:

1. **Anything with visual output goes into the notebook**, in a new tab named
   for what it shows (`Exploration — <what it shows>`), announced in chat by that
   name. Never answer a request for a plot or a table with chat text alone, and
   never bury it in a step tab where it will be mistaken for a workflow output.
2. **The limits do not move.** Ad-hoc means plotting and reshaping results that
   already exist — filtering, sorting, relabelling, re-plotting. It is never a
   new statistic, never R, never a re-run with changed parameters done by hand. A
   parameter change is a re-launch through its proper stage, announced in chat.

`steps/06-explore.md` holds the full list of what is allowed and what is not, and
how to say no usefully. Read it when the first ad-hoc request arrives, whatever
stage that happens at — not only after stage 5.

## Long-running workflows

**Never `await execution.wait()` on `takara_de_deseq2` or `takara_de_gsea`.** The cell parks
indefinitely and does not survive a notebook pod restart. Use the launch cell
plus a separate resume cell that polls Latch Data for the expected output
files, as shown in `wf/deseq2_wf.md`.

**Always set `key=` on `w_workflow`.** It is the idempotency handle: re-running
a cell with the same key does not relaunch. A missing key is the most likely
cause of an accidental duplicate execution, and duplicate executions cost money.

## Cell template placeholders

Every template declares its placeholders. These are the only substitutions you
ever make, and you make no others:

| Placeholder | Value |
|---|---|
| `{{RUN_DIR}}` | The `latch://` path of this run's directory in Latch Data. Fixed for the whole session; create it once at stage 1 and reuse it. |
| `{{SKILL_DIR}}` | Absolute path of this skill's directory in the pod, normally `/opt/latch/plots-faas/.claude/skills/takara-guided-diffexp`. |
| `{{ID_FORMAT}}` | `id_format` read from `profile.json`. Never invent it. |
| `{{ORGANISM}}` | `organism` read from `profile.json`. Never invent it. |

Substituting anything else, or editing a line that is not a placeholder, breaks
the guarantee that the analysis path is what is in git.

## Reporting numbers

You narrate; you do not calculate. Read `de_metrics.json`, `qc_metrics.json` and
`gsea_metrics.json` and report what they say. If a number you want is not in a
metrics file, say you do not have it — do not derive it.

## When a stage fails

- **QC or DESeq2 fails** — the stage does not advance. Reopen the previous gate
  and show the error. Offer to retry or to regroup.
- **Enrichment fails** — the session still opens; exploratory mode becomes
  available. Do not trap the user in a failed optional stage.
- **Nothing mapped in enrichment** — that is a real result, not a failure. Read
  the readout from `gsea_metrics.json` and report it plainly.
