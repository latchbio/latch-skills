---
name: latch-plots-ui
description: >
  Use this skill when working with Latch widgets in Plots notebooks, including
  output widgets (w_h5, w_plot, w_table, w_text_output, w_ann_data, w_igv,
  w_logs_display), user input widgets (w_text_input, w_select, w_multi_select,
  w_radio_group, w_checkbox, w_number_slider_input, w_range_slider_input,
  w_button), or layout widgets (w_row, w_column, w_grid).
---

# Latch Plots UI

Use this skill for Latch widget rendering and notebook UI conventions.

## Use this skill when

- the plan needs `w_h5`, `w_plot`, `w_table`, `w_text_output`, or any output widget
- the plan needs user input widgets (`w_select`, `w_text_input`, `w_checkbox`, etc.)
- the plan needs layout widgets (`w_row`, `w_column`, `w_grid`)
- the user asks how to render AnnData, tables, or plots in Plots
- a technology doc requires plot widgets or viewer output

## Widget Core Concepts

- Every widget is a Python object. Assign to a variable; the live user selection is at `.value`.
- Widgets render in **call order**.
- **Reactive execution:** any cell that touches `some_widget.value` re-runs when that value changes. To read once without reactivity, use `some_widget._signal.sample()`.

## Output rules

- Use `w_text_output` for short status or validation messages.
- Use `w_table` for DataFrames.
- Use `w_plot` for Plotly or Matplotlib figures.
- Use `w_h5` for AnnData exploration and spatial / embedding inspection.
- Use `w_logs_display` + `submit_widget_state()` for long-running progress.
- Never use bare `print()`, `display()`, or `plt.show()` for user-visible output.

---

## Output / Visualization Widgets

### w_text_output

**Import:** `from lplots.widgets.text import w_text_output`

Display text output with optional message box styling.

**Arguments:**
- `content` (str, required): Text content to display
- `appearance` (TextOutputAppearance, optional): Styling with message_box option
- `key` (str, optional): Unique widget identifier

**Message box types:** "danger", "info", "success", "warning", "primary", "neutral"

**Example:**
```python
from lplots.widgets.text import w_text_output

w_text_output(
    content="Analysis complete: 1,234 cells passed QC",
    appearance={"message_box": "success"}
)
```

---

### w_plot

**Import:** `from lplots.widgets.plot import w_plot`

Display matplotlib, seaborn, or plotly figures.

**Arguments:**
- `label` (str, optional): Label for the plot
- `source` (Figure | SubFigure | Axes | BaseFigure | FacetGrid | PairGrid | JointGrid, optional): Plot object
- `appearance` (OutputAppearance, optional): Styling options
- `key` (str, optional): Unique widget identifier

**Critical rules:**
- The plot source must be a named **global variable**.
- Each `w_plot` must reference **its own unique variable** — reusing a variable causes all plots to render the same content.
- **DO NOT** use `globals()` or dynamic variable naming in loops.
- Explicitly declare each variable with a unique name (e.g., `fig_plot1`, `fig_plot2`).
- For `scanpy` dot or violin plots, convert the returned object into a Matplotlib figure: call `.show()` then access `.fig`.

**Example:**
```python
from lplots.widgets.plot import w_plot
import plotly.express as px

fig_scatter = px.scatter(df, x='x', y='y')
w_plot(label="First Plot", source=fig_scatter)

fig_bar = px.bar(df, x='x', y='y')
w_plot(label="Second Plot", source=fig_bar)
```

**Scanpy conversion:**
```python
dp = sc.pl.dotplot(
    adata, var_names=plot_genes, groupby='cell_type',
    dendrogram=True, return_fig=True, show=False, figsize=(14, 6),
)
dp.show()
fig_dotplot = dp.fig
w_plot(label="Dot Plot", source=fig_dotplot)
```

**WRONG — do not do this:**
```python
for i, data in enumerate(datasets):
    fig = px.scatter(data, x='x', y='y')
    globals()[f'fig_{i}'] = fig
    w_plot(label=f"Plot {i}", source=globals()[f'fig_{i}'])
```

---

### w_table

**Import:** `from lplots.widgets.table import w_table`

Display pandas DataFrames.

**Arguments:**
- `label` (str, optional): Label for the table
- `source` (DataFrame, optional): DataFrame to display
- `appearance` (OutputAppearance, optional): Styling options
- `key` (str, optional): Unique widget identifier

The source must be a named global variable.

**Example:**
```python
from lplots.widgets.table import w_table
import pandas as pd

df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
w_table(label="Data", source=df)
```

---

### w_h5

**Import:** `from lplots.widgets.h5 import w_h5`

Interactive AnnData/H5AD viewer for single-cell and spatial data.

**Arguments:**
- `label` (str, optional): Label for the viewer
- `ann_data` (AnnData, optional): AnnData object to visualize
- `spatial_dir` (LPath, optional): Path to spatial data directory
- `ann_tiles` (LPath, optional): Path to annotation tiles
- `readonly` (bool, optional): Whether viewer is read-only. Default: False
- `appearance` (OutputAppearance, optional): Styling options
- `viewer_presets` (ViewerPreset, optional): Configuration for viewer defaults
- `key` (str, optional): Unique widget identifier

**Viewer presets options:**
- `genes_of_interest` (list[str]): Genes to highlight
- `default_color_by` (ColorByObs | ColorByVar): Default coloring scheme
- `default_obsm_key` (str): Default embedding to display (e.g., "X_umap", "spatial")
- `cell_markers` (CellMarkers): Marker size and opacity settings
- `categorical_color_palette` (list[str]): Colors for categorical data
- `continuous_color_palette` (list[str]): Colors for continuous data

**Example:**
```python
from lplots.widgets.h5 import w_h5

viewer = w_h5(
    ann_data=adata,
    readonly=False,
    viewer_presets={
        "genes_of_interest": ["CD3D", "CD4"],
        "default_color_by": {"type": "obs", "key": "cell_type"},
        "default_obsm_key": "X_umap",
        "cell_markers": {"default_size": 3, "default_opacity": 0.8},
        "categorical_color_palette": ["red", "blue"],
        "continuous_color_palette": ["blue", "white", "red"]
    }
)

v = viewer.value
# v["lasso_points"]: list[list[(x,y)]]
# v["lasso_points_obsm"]: str | None
# v["image_alignment_step"]: current step in image alignment workflow
```

**Keeping in sync:** After running code that updates `adata.obs` or `adata.obsm`, call `h5_refresh` on any `w_h5` widgets using that object.

---

### w_ann_data

**Import:** `from lplots.widgets.ann_data import w_ann_data`

Display or interact with AnnData objects (lighter alternative to w_h5).

**Arguments:**
- `ann_data` (AnnData, optional): AnnData object
- `readonly` (bool, optional): Whether widget is read-only. Default: False
- `appearance` (OutputAppearance, optional): Styling options
- `key` (str, optional): Unique widget identifier

**Example:**
```python
from lplots.widgets.ann_data import w_ann_data

ann_widget = w_ann_data(ann_data=adata, readonly=False)
```

---

### w_igv

**Import:** `from lplots.widgets.igv import w_igv, IGVOptions`

Display genomics data (BAM, VCF, BED, BigWig) in IGV browser.

**Arguments:**
- `label` (str, optional): Label for the viewer
- `options` (IGVOptions, required): IGV.js configuration dictionary
- `key` (str, optional): Unique widget identifier

**IGVOptions fields:**
- `genome` (str): Reference genome ID (e.g., "hg38", "mm10")
- `locus` (str | list[str]): Initial genomic locus
- `tracks` (list[TrackOptions]): Track configurations
- `showNavigation`, `showIdeogram`, `showRuler` (bool): UI toggles

**Track fields:**
- `name` (str), `type` (str: "alignment", "variant", "annotation", "wig")
- `url` (str), `indexURL` (str): Data and index file paths
- `color` (str), `height` (int), `displayMode` (str), `autoscale` (bool)

**Example:**
```python
from lplots.widgets.igv import w_igv, IGVOptions
from latch.account import Account

workspace_id = Account.current().id
options: IGVOptions = {
    "genome": "hg38",
    "locus": "chr1:155,100,000-155,200,000",
    "tracks": [{
        "name": "Alignment",
        "type": "alignment",
        "url": f"latch://{workspace_id}.account/Covid/covid.bam",
        "indexURL": f"latch://{workspace_id}.account/Covid/covid.bam.bai",
        "color": "steelblue",
        "height": 150
    }]
}
w_igv(options=options)
```

---

### w_logs_display

**Import:** `from lplots.widgets.logs import w_logs_display`

Display logs and progress messages. Must call `submit_widget_state()` after creating.

**Arguments:**
- `label` (str, optional): Label for the logs display
- `appearance` (FormInputAppearance, optional): Styling options
- `key` (str, optional): Unique widget identifier

**Example:**
```python
from lplots.widgets.logs import w_logs_display
from lplots import submit_widget_state

w_logs_display()
submit_widget_state()
```

---

## User Input Widgets

### w_text_input

**Import:** `from lplots.widgets.text import w_text_input`

**Arguments:**
- `label` (str, required): Label for the input
- `readonly` (bool, optional): Default: False
- `default` (str, optional): Default text value
- `appearance` (FormInputAppearance, optional): Styling (placeholder, detail, help_text, error_text, description)
- `key` (str, optional): Unique widget identifier

**Example:**
```python
from lplots.widgets.text import w_text_input

name = w_text_input(label="Name", default="Alice")
user_name = name.value
```

---

### w_select

**Import:** `from lplots.widgets.select import w_select`

Single selection from a list of options.

**Arguments:**
- `label` (str, required)
- `options` (Iterable[str | int | float | bool | datetime], required)
- `readonly` (bool, optional): Default: False
- `default` (str | int | float | bool | datetime, optional)
- `required` (bool, optional): Default: False
- `key` (str, optional)
- `appearance` (FormInputAppearance, optional)

**Example:**
```python
from lplots.widgets.select import w_select

sel = w_select(label="Choose", options=["a", "b", "c"], default="a")
choice = sel.value
```

---

### w_multi_select

**Import:** `from lplots.widgets.multiselect import w_multi_select`

Multiple selection from a list of options.

**Arguments:**
- `label` (str, required)
- `options` (Iterable[str | int | float | bool | datetime], required)
- `readonly` (bool, optional): Default: False
- `default` (Iterable[str | int | float | bool | datetime], optional)
- `required` (bool, optional): Default: False
- `key` (str, optional)
- `appearance` (FormInputAppearance, optional)

**Example:**
```python
from lplots.widgets.multiselect import w_multi_select

ms = w_multi_select(
    label="Tags", options=["alpha", "bravo", "charlie"], default=["alpha"]
)
selected = ms.value
```

---

### w_radio_group

**Import:** `from lplots.widgets.radio import w_radio_group`

Single selection using radio buttons.

**Arguments:**
- `label` (str, required)
- `options` (Iterable[str | int | float | bool | datetime], required)
- `readonly` (bool, optional): Default: False
- `default` (str | int | float | bool | datetime, optional)
- `direction` (Literal["horizontal", "vertical"], optional): Default: "horizontal"
- `required` (bool, optional): Default: False
- `key` (str, optional)
- `appearance` (FormInputAppearance, optional)

**Example:**
```python
from lplots.widgets.radio import w_radio_group

rg = w_radio_group(label="One", options=[1, 2, 3], default=1, direction="horizontal")
selected = rg.value
```

---

### w_checkbox

**Import:** `from lplots.widgets.checkbox import w_checkbox`

Boolean checkbox input.

**Arguments:**
- `label` (str, required)
- `default` (bool, optional): Default: False
- `readonly` (bool, optional): Default: False
- `appearance` (CheckboxInputAppearance, optional): error_text, description
- `key` (str, optional)

**Example:**
```python
from lplots.widgets.checkbox import w_checkbox

cb = w_checkbox(label="Enable filtering", default=False)
is_checked = cb.value
```

---

### w_number_slider_input

**Import:** `from lplots.widgets.slider import w_number_slider_input`

Numeric input with slider interface.

**Arguments:**
- `label` (str, required)
- `readonly` (bool, optional): Default: False
- `default` (int | float, optional)
- `min` (int | float, optional)
- `max` (int | float, optional)
- `step` (int | float, optional)
- `tooltip_formatter` (Literal["number", "percentage", "currency", "decimal", "integer", "scientific", "bytes"], optional)
- `scale_type` (Literal["linear", "logarithmic"], optional)
- `marks` (dict[int | float, str], optional)
- `key` (str, optional)
- `appearance` (FormInputAppearance, optional)

**Example:**
```python
from lplots.widgets.slider import w_number_slider_input

slider = w_number_slider_input(
    label="Threshold", default=0.5, min=0.0, max=1.0, step=0.1,
    scale_type="linear", tooltip_formatter="percentage"
)
value = slider.value
```

---

### w_range_slider_input

**Import:** `from lplots.widgets.slider import w_range_slider_input`

Select a numeric range with two-handle slider.

**Arguments:**
- `label` (str, required)
- `readonly` (bool, optional): Default: False
- `default` (tuple[int, int] | tuple[float, float], optional)
- `min` (int | float, optional)
- `max` (int | float, optional)
- `step` (int | float, optional)
- `tooltip_formatter`, `scale_type`, `marks`, `key`, `appearance` (same as w_number_slider_input)

**Example:**
```python
from lplots.widgets.slider import w_range_slider_input

rs = w_range_slider_input(label="Range", default=(0.2, 0.8), min=0.0, max=1.0, step=0.1)
range_values = rs.value  # tuple (min, max)
```

---

### w_button

**Import:** `from lplots.widgets.button import w_button`

Trigger actions with a button click.

**Arguments:**
- `label` (str, required): Button label
- `readonly` (bool, optional): Whether button is disabled. Default: False
- `key` (str, optional)

**Example:**
```python
from lplots.widgets.button import w_button

button = w_button(label="Click to Run")
if button.value:
    # logic only runs when button is clicked
    pass
```

---

## Layout Widgets

### w_row

**Import:** `from lplots.widgets.row import w_row`

Arrange widgets horizontally.

**Arguments:**
- `items` (list[BaseWidget], required): List of widgets to arrange
- `key` (str, optional)

**Example:**
```python
from lplots.widgets.row import w_row

w_row(items=[widget1, widget2, widget3])
```

---

### w_column

**Import:** `from lplots.widgets.column import w_column`

Arrange widgets vertically.

**Arguments:**
- `items` (list[BaseWidget], required): List of widgets to arrange
- `key` (str, optional)

**Example:**
```python
from lplots.widgets.column import w_column

w_column(items=[widget1, widget2, widget3])
```

---

### w_grid

**Import:** `from lplots.widgets.grid import w_grid`

Arrange widgets in a grid with custom spans.

**Arguments:**
- `columns` (int, required): Number of columns
- `rows` (int, optional): Number of rows (auto if not specified)
- `key` (str, optional)

**Methods:**
- `add(item, col_span=1, row_span=1)`: Add widget with span

**Example:**
```python
from lplots.widgets.grid import w_grid

with w_grid(columns=12) as g:
    g.add(item=widget1, col_span=4, row_span=1)
    g.add(item=widget2, col_span=8, row_span=1)
```

## Fallback

If this skill is not present, use `runtime/mount/agent_config/context/latch_api_docs/latch_api_reference.md`
and the examples under `runtime/mount/agent_config/context/examples/` directly.
