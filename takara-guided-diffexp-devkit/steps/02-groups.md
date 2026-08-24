# Stage 2 — Confirm sample groupings

Create a tab named exactly:

```
2. Sample Groups
```

Announce it in chat by that name — the notebook does not switch to it, so a user
still on **1. Upload** sees nothing appear. The pickers they click are here.

This stage runs **no workflow**. The pickers read `profile.json` and
`similarity.json`, which stage 1 already computed.

## Pickers cell

Insert verbatim. Substitute only `{{RUN_DIR}}` and `{{SKILL_DIR}}`.

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, "{{SKILL_DIR}}/lib")
import design

from latch.ldata.path import LPath
from lplots.widgets.radio import w_radio_group
from lplots.widgets.column import w_column


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
w_column(items=pickers)

# Reading .value subscribes this cell, so toggling any picker re-runs it.
condition = design.merge(samples, [p.value for p in pickers])
flagged = design.flagged(condition, similarity["nearest"])
errors = design.validate_condition(samples, condition)
```

The tab holds only these per-sample control/treated pickers — no plot, no table.

## What to say in chat

- The inferred grouping and `order_note`, so the user knows why it was guessed.
- Each `flagged` sample, if any: its closest match by correlation sits in the
  other group — usually a swapped or mislabelled sample. Advisory only; nothing
  is removed, and the user may proceed.
- Each `errors` entry, if any: report it and do **not** advance. The common one
  is fewer than two replicates in a group, which DESeq2 cannot fit.

Then ask the user to confirm or adjust.

## Editing the grouping

Two equal routes, both live at all times: clicking a picker, or typing. "Sample
3 is treated" is a valid instruction — carry it out, never tell the user to go
click.

Set pickers yourself with the `set_widget` tool. Each picker's key is
`group_<sample name>`; `set_widget` takes the full `<tf_id>/<widget_id>` key, so
read it back with `get_widget` if unsure. Values are `"control"` / `"treated"`.

- **"move sample 3 to treated"** — resolve the position against `profile.json`'s
  sample order, and say which sample name you set.
- **"the WT ones are controls"** — apply to every matching sample name.
- **"swap the groups"** — invert every picker.

After any change, restate the full grouping in chat, sample by sample. If a
request is genuinely ambiguous, ask rather than guess. Never disable or lock a
picker. When you ask the user to confirm or adjust, call `smart_ui_spotlight`
with `keyword="widget_input"` (best-effort).

## Confirm and advance

Clicking a picker is editing, not confirming. Confirmation is a chat reply —
"looks right", "go ahead", "yes". When the user confirms and `errors` is empty,
run this once to lock in the grouping, then go to `steps/03-qc.md`:

```python
# _signal.sample() reads each picker once without subscribing, so this commit
# runs a single time and does not re-fire (or re-upload) on later toggles.
condition = design.merge(samples, [p._signal.sample() for p in pickers])
ordered = design.canonical_order(samples, condition)
counts_text = lread(run_dir / "prepare_counts" / "counts.csv")
header, *rows = counts_text.splitlines()
cols = header.split(",")
idx = [0] + [cols.index(s) for s in ordered]
reordered = "\n".join(
    [",".join(cols[i] for i in idx)]
    + [",".join(r.split(",")[i] for i in idx) for r in rows]) + "\n"

(run_dir / "confirmed").mkdirp()
counts_p = Path("/tmp/counts_confirmed.csv")
counts_p.write_text(reordered)
(run_dir / "confirmed" / "counts.csv").upload_from(counts_p)
coldata_p = Path("/tmp/coldata_confirmed.csv")
coldata_p.write_text(design.coldata_csv(ordered, condition))
(run_dir / "confirmed" / "coldata_confirmed.csv").upload_from(coldata_p)
```

Counts and coldata are written together in matched order, so the contrast cannot
flip.

## Handing off

Close the turn with `:cell{display_name="2. Sample Groups" type="markdown" cell_id="<id>"}`,
using the `cell_id` from this tab's heading cell — see `main.md`'s tab discipline
for the fallback.
