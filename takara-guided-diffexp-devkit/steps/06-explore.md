# Stage 6 — Exploratory mode

## When this unlocks

`results.csv` must exist **and** the enrichment decision must be resolved. Any
of three paths resolves it:

1. enrichment ran;
2. enrichment was declined — a pure state change, no job;
3. enrichment ran and failed.

The third matters: a failed optional stage opens the session rather than
trapping the user in it.

If DESeq2 has not succeeded, exploratory mode is **not** available. There is
nothing to explore without `results.csv`.

## Declining enrichment is not a one-way door

A user who declined can still ask for it later, and it genuinely runs — as long
as no enrichment has already succeeded. Stage 5 is not terminal. If they ask,
go back to `steps/05-gsea.md`.

## What is allowed here

Ad-hoc requests are not confined to this stage — the user may ask for a plot, a
table or a reshaped view at any point in the session, and `main.md` says where
that output goes. This file is about the limits, which are the same wherever the
request arrives.

Each ad-hoc request gets **its own tab, named for what it shows**, prefixed so
the watermark survives:

```
Exploration — <what it shows>
```

for example `Exploration — Volcano, cytokine genes` or
`Exploration — Top 50 by fold change`. The prefix is the watermark: anything in
an `Exploration` tab is outside the versioned result set. The rest of the name
is so the user can find it again among five step tabs and whatever else they
have asked for. Announce every one in chat by its full name when you create it,
and again when you add to it.

Do not reuse a step tab for an ad-hoc plot. **4. Differential Expression**
holds the workflow's own outputs; a hand-filtered volcano sitting next to them
looks like part of the result set, which is exactly what the prefix exists to
prevent.

Allowed:

- Plotting already-computed columns from `results.csv` and `gsea_results.csv` —
  filtering to a gene list, relabelling a volcano, a different cut of the same
  numbers.
- Tables, sorting, subsetting.
- Explaining what the existing results mean.

## What is forbidden

The rules in `SKILL.md` are not relaxed here. In particular:

- **No new statistics.** No re-fitting, no re-testing, no new p-values, no new
  fold changes, no multiple-testing correction, no clustering that gets
  reported as a result. That covers reaching for any Python statistical-testing
  or machine-learning package to substitute for one — the exact packages named
  in `SKILL.md`'s rules are still off-limits; this section just avoids
  repeating their names so this file's own prose does not trip the check that
  scans these templates for them.
- **No R.** Not a `.R` file, not the R interpreter invoked from a shell
  command.
- **No re-running a stage with changed parameters from here.** That is a real
  analysis, so it goes back through the proper stage with the parameter change
  announced in chat, and it lands in the versioned result set where it belongs.

These limits do not soften just because a request arrives early. "Can you show
me a PCA of the raw counts?" asked during stage 2 is the same request as during
stage 6: plotting a number a workflow already computed is fine, computing one
here is not, and if it is not computed yet the answer is that the stage that
computes it has not run.

If a user asks for something that needs a new statistic, say so plainly and
offer the parameterised re-run instead: every statistical parameter is a
workflow parameter, so almost any legitimate variation can be expressed as a
re-launch with a different value — visible in the launch params and recorded in
the execution, which is the whole point.

## Saying no well

"That would need a new statistical test, which I can't run in the notebook — it
has to go through the DESeq2 workflow so the parameters are recorded. I can
re-run stage 4 with `padj_cutoff` at 0.01 instead of 0.05 if that's what you're
after."

That is more useful than a refusal, and it keeps the audit trail intact.
