# Stage 2 — Confirm sample groupings

Create a tab named exactly:

```
2. Sample Groups
```

Announce it in chat by that name, every time — the notebook does not switch to
it, so a user still looking at **1. Upload** sees nothing appear and
assumes you have stalled. The toggles they must click are in a tab they have
not opened, which is the same as no toggles at all.

This stage runs **no workflow**. Everything shown is read from
`profile.json` and `similarity.json`, which stage 1 already computed.

## Cell template

Insert verbatim. Substitute only `{{RUN_DIR}}` and `{{SKILL_DIR}}`.

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, "{{SKILL_DIR}}/lib")
import design
import render

from latch.ldata.path import LPath
from lplots.widgets.button import w_button
from lplots.widgets.plot import w_plot
from lplots.widgets.radio import w_radio_group
from lplots.widgets.table import w_table
from lplots.widgets.column import w_column
from lplots.widgets.grid import w_grid


def lread(lp):
    """Download an LPath to a local temp file and return its text."""
    p = Path(f"/tmp/{lp.node_id()}{Path(lp.name() or '').suffix}")
    lp.download(p, cache=True)
    return p.read_text()


run_dir = LPath("{{RUN_DIR}}")
profile = json.loads(lread(run_dir / "prepare_counts" / "profile.json"))
similarity = json.loads(lread(run_dir / "prepare_counts" / "similarity.json"))

samples = profile["samples"]
inferred = profile["condition"]

pickers = [
    w_radio_group(
        label=name,
        options=["control", "treated"],
        default=inferred.get(name, "control"),
        key=f"group_{name}",
    )
    for name in samples
]

# Reading .value subscribes this cell, so changing any radio re-runs it and the
# plot recolours. Nothing is recomputed: coords and nearest neighbours come
# from the counts alone and never depend on the labels.
condition = design.merge(samples, [p.value for p in pickers])
flagged = design.flagged(condition, similarity["nearest"])
errors = design.validate_condition(samples, condition)

confirm = w_button(label="Confirm grouping — run quality check")

with w_grid(columns=2) as grid:
    grid.add(item=w_plot(
        label="Sample similarity",
        source=render.similarity_figure(similarity, condition, flagged),
        key="similarity_plot",
    ))
    grid.add(item=w_column(items=[*pickers, confirm]))
    grid.add(item=w_table(
        label="Proposed design",
        source=render.design_table(samples, condition,
                                   similarity["nearest"], flagged),
        key="design_table",
    ), col_span=2)

if confirm.value and not errors:
    ordered = design.canonical_order(samples, condition)
    counts_text = lread(run_dir / "prepare_counts" / "counts.csv")
    header, *rows = counts_text.splitlines()
    cols = header.split(",")
    idx = [0] + [cols.index(s) for s in ordered]
    reordered = "\n".join(
        [",".join(cols[i] for i in idx)]
        + [",".join(r.split(",")[i] for i in idx) for r in rows]) + "\n"

    (run_dir / "confirmed").mkdirp()

    reordered_p = Path("/tmp/counts_confirmed.csv")
    reordered_p.write_text(reordered)
    (run_dir / "confirmed" / "counts.csv").upload_from(reordered_p)

    coldata_p = Path("/tmp/coldata_confirmed.csv")
    coldata_p.write_text(design.coldata_csv(ordered, condition))
    (run_dir / "confirmed" / "coldata_confirmed.csv").upload_from(coldata_p)
```

Counts and coldata are written **together, in matched order**, so the contrast
cannot flip.

## Editing the grouping in natural language

The toggles are one way to set the grouping. Typing is the other, and both work
at every moment — a user who says "sample 3 is treated" has done exactly what a
click would have done, and must not be told to go and click it.

Use the `set_widget` MCP tool to set the `w_radio_group` values yourself. Each
picker's key is `group_<sample name>`, matching the `key=f"group_{name}"` in the
template above; `set_widget` takes the **full** widget key in
`<tf_id>/<widget_id>` form, so read the key back with `get_widget` if you are
unsure of the prefix rather than guessing at it. The value is the option string,
`"control"` or `"treated"`.

Handle these the same way:

- **"move sample 3 to treated"** — positional. Resolve the position against the
  sample order in `profile.json`, not against the order the toggles happen to
  render in, and say which sample name you resolved it to.
- **"the WT ones are the controls"** — a pattern over sample names. Apply it to
  every sample whose name matches, and name them all when you report back.
- **"swap the groups"** — invert every picker.

Setting the widget re-runs the cell, because the cell reads `.value`. The
similarity plot recolours and the design table updates on their own; nothing is
recomputed, and you have not calculated anything.

**Always restate the resulting grouping in chat afterwards**, sample by sample,
so the user can see what you did without switching tabs to check. A silent
`set_widget` is indistinguishable from a misheard instruction. If a request is
ambiguous — "the first two are controls" over samples you cannot order
confidently — ask instead of guessing, and leave the toggles alone.

The user can still click any toggle at any time, including to undo something you
just set. Never disable a picker, never set `readonly`, and never ask the user to
stop clicking while you work.

## Spotlight the toggles

When you ask the user to confirm or adjust the grouping, call
`smart_ui_spotlight` with `keyword="widget_input"`. If a specific sample's
toggle is meant, pass its `widget_key` in the same `<tf_id>/<widget_id>` form
used with `set_widget` above. Best-effort: if the call fails, the toggles and
chat text still carry the gate.

## What to say in chat

- The inferred grouping and `order_note`, so the user knows why it was guessed.
- If `flagged` is non-empty: name each sample and say that its closest match by
  correlation sits in the other group, which usually means a swapped or
  mislabelled sample. Say plainly that this is advisory — nothing is removed
  automatically, and the user may proceed.
- If `errors` is non-empty: report each one and do **not** advance. The most
  common is fewer than two replicates in a group, which DESeq2 cannot fit.

## Gate

Cheap gate: an ambiguous reply resolves toward proceeding. "Looks right",
"go ahead", "yes" and clicking the button are all confirmation. A question is
answered with the gate left open.

When confirmed and `errors` is empty, go to `steps/03-qc.md`, which opens its
own tab.

## Handing off

Close the turn with `:cell{display_name="2. Sample Groups" type="markdown" cell_id="<id>"}`,
using the `cell_id` from this tab's heading cell — see `main.md`'s Notebook tab
discipline for the fallback when you don't have one.
