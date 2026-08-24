# Stage 1 — Upload the counts table

Create a tab named exactly:

```
1. Upload
```

Create it with `create_tab` and **announce it in chat by that name.** The
notebook does not switch to a new tab: a user left on the previous tab sees
nothing happen and concludes you have stalled. A `w_text_output` pointer is no
help — it renders inside the very tab they have not clicked. Chat is the only
surface always in view.

## What renders before the user uploads anything

The first cell in the tab shows an **example** counts table beside the file
picker, so the user can see the shape their file has to have before they go
looking for it. The example is obviously synthetic — nobody should mistake
`GeneA` in `control_1` for their own data — and it is there purely to say what
"features in rows, samples in columns, raw integer counts" looks like.

Say the requirement in chat too, not only in the widget — the user may be
looking at another tab.

## Cell template — expected shape and the file picker

Insert verbatim. Substitute only `{{RUN_DIR}}`.

```python
import pandas as pd

from lplots.widgets.ldata import w_ldata_picker
from lplots.widgets.column import w_column
from lplots.widgets.grid import w_grid
from lplots.widgets.table import w_table
from lplots.widgets.text import w_text_output
from lplots.widgets.workflow import w_workflow

example_counts = pd.DataFrame(
    {
        "gene_id": ["GeneA", "GeneB", "GeneC", "GeneD", "GeneE"],
        "control_1": [412, 0, 1875, 33, 96],
        "control_2": [389, 2, 1802, 41, 88],
        "treated_1": [455, 1, 942, 37, 310],
        "treated_2": [478, 0, 1011, 29, 287],
    }
)

example_table = w_table(
    label="Example only — not your data",
    source=example_counts,
    key="example_counts_table",
)

requirements = w_text_output(
    content=(
        "Your counts table needs to look like the example beside this text:\n"
        "- raw integer counts — not normalised, not log-transformed, "
        "not TPM, FPKM or CPM\n"
        "- features in rows, samples in columns\n"
        "- the first column is the feature identifier (gene symbol, "
        "Ensembl ID, or peak ID)\n"
        "- CSV or TSV\n"
        "Sample names do not have to contain 'control' or 'treated' — "
        "you confirm the grouping yourself at the next step."
    ),
    appearance={"message_box": "info"},
)

counts_picker = w_ldata_picker(
    label="Raw counts table (CSV or TSV, genes in rows)",
    key="counts_picker",
)

with w_grid(columns=2) as upload_grid:
    upload_grid.add(item=w_column(items=[example_table, requirements]))
    upload_grid.add(item=counts_picker)

if counts_picker.value is not None:
    ingest = w_workflow(
        label="Profile the counts table",
        wf_name="takara_de_prepare_counts.workflow.prepare_counts",
        params={"counts_file": counts_picker.value.path,
                "run_dir": "{{RUN_DIR}}"},
        automatic=True,
        key="ingest_launch",
    )
```

The example DataFrame is illustrative, not computed. It is hard-coded literal
numbers — there is no statistic in it, and there is nothing to derive from it.
Do not replace it with a sample of the user's data: the whole point is that it
renders **before** any file exists.

Note `counts_picker.value.path` rather than `str(counts_picker.value)` —
calling `str()` on an `LPath` is a documented source of bugs.

## Spotlight the file picker

After that cell renders, call `smart_ui_spotlight` with `keyword="file_upload"`
to draw the user's eye to `counts_picker`. Best-effort only — if the call
fails, the requirement text above still stands and the picker still works.

## After it completes

The findings from `profile.json` — the data check and the detected identifier
format — belong in the **1. Upload** tab as a `w_text_output`, and in
chat as text. Say them in chat every time: the tab does not come forward on its
own, and a finding only the notebook knows about is a finding nobody read.

Read `{{RUN_DIR}}/prepare_counts/profile.json` and report, in chat:

- how many samples and genes were found;
- the inferred grouping **and the reason** — quote `order_note` and say whether
  `method` was `sample names` or `column order`. A user who knows the guess came
  from column position rather than sample names will check it more carefully;
- any entry in `issues`, verbatim from its `detail` and `suggestion`. Every issue
  has severity `block`. Do not proceed past a blocking issue without saying so
  explicitly and getting the user to decide;
- if `conclusive` is `false`, say the gene identifier format could not be
  determined and ask the user, with `AskUserQuestion`, rather than guessing.
  There is no model inside the ingest task to fall back on.

### If parsing failed

`profile.json` can come back with `parse_failed: true` instead of the fields
above — auto-detection could not make sense of the file. Do not show the raw
`error` traceback. Read `preview` instead and diagnose in plain language:
what the file's first line actually looks like, its `detected_delimiter` and
`n_columns`, and how that mismatches what a counts table needs (a gene
column and >=2 sample columns). Then either propose a concrete fix —
`skip_lines` / `delimiter` / `gene_column` / `drop_columns` — and confirm it
with the user, or use `AskUserQuestion` if the structure is genuinely
ambiguous. Once confirmed, re-run the "Profile the counts table"
`w_workflow` with those parameters added.

This is structural repair only — delimiter, header row, annotation columns,
gene column. If the data is log-transformed, normalized, contains negative
values, or has too few replicates, that is a blocking scientific issue
(`issues`, `severity: "block"`), not a formatting problem: report it and
stop. Do not "repair" it.

## Handing off

**1. Upload** is the default tab, the one the user is already looking at
when the session starts. There is nowhere new to send them, so no `:cell{}`
directive is needed here — do not manufacture one. Say the findings above in
chat and move on.

Then go to `steps/02-groups.md`, which opens its own tab.
