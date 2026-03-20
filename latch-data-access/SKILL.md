---
name: latch-data-access
description: >
  Use this skill when selecting or browsing files in Latch Data, when the user
  mentions w_ldata_picker, w_ldata_browser, w_datasource_picker,
  w_registry_table_picker, w_registry_table, w_dataframe_picker, LPath,
  LatchFile, LatchDir, or when notebook code needs to move between latch://
  paths and local files.
---

# Latch Data Access

Use this skill for Latch-specific file selection, browsing, and path handling.

## Use this skill when

- the user needs to pick files or directories from Latch Data
- code needs `w_ldata_picker`, `w_ldata_browser`, `w_datasource_picker`, `w_registry_table_picker`, `w_registry_table`, or `w_dataframe_picker`
- a workflow parameter requires `LatchFile(...)` or `LatchDir(...)`
- a remote `latch://` object needs to be downloaded locally

## Selection rules

- Use `w_ldata_picker` to select files or directories.
- Use `w_ldata_browser` to browse a known directory.
- Widgets return values at `.value`.

## Path handling

- Use `LPath` only for remote `latch://` objects.
- Keep local files as `pathlib.Path`.
- When converting widget output into `LatchFile(...)` or `LatchDir(...)`, use `widget.value.path`.

## Download pattern

- Resolve the selected LPath.
- Use a stable local filename, typically from `node_id()` plus suffix.
- Download to a local `Path`.

---

## Widget API Reference

### w_ldata_picker

**Import:** `from lplots.widgets.ldata import w_ldata_picker`

Select files or directories from Latch Data.

**Arguments:**
- `label` (str, required): Label for the picker
- `readonly` (bool, optional): Whether widget is read-only. Default: False
- `default` (str, optional): Default latch:// path
- `required` (bool, optional): Whether selection is required. Default: False
- `file_type` (Literal["file", "dir", "any"], optional): Filter by type. Default: "any"
- `key` (str, optional): Unique widget identifier
- `appearance` (FormInputAppearance, optional): Styling options

**Example:**
```python
from lplots.widgets.ldata import w_ldata_picker
from latch.ldata.path import LPath
from pathlib import Path
import pandas as pd

csv = w_ldata_picker(
    label="CSV",
    default="latch:///path/file.csv",
    file_type="file"
)

if csv.value is not None:
    lp: LPath = csv.value
    fname = lp.name()
    suffix = Path(fname).suffix if fname else ""
    local_p = Path(f"{lp.node_id()}{suffix}")
    lp.download(local_p, cache=True)
    df = pd.read_csv(local_p)
```

---

### w_ldata_browser

**Import:** `from lplots.widgets.ldata import w_ldata_browser`

Display contents of a specific Latch Data directory for browsing.

**Arguments:**
- `label` (str, required): Label for the browser
- `dir` (str | LPath, required): Latch Data directory path to browse
- `readonly` (bool, optional): Whether widget is read-only. Default: False
- `required` (bool, optional): Whether selection is required. Default: False
- `key` (str, optional): Unique widget identifier
- `appearance` (FormInputAppearance, optional): Styling options

**Example:**
```python
from lplots.widgets.ldata import w_ldata_browser

browser = w_ldata_browser(label="Browse Files", dir="latch:///my_dir")
# browser.value returns the LPath to the directory
```

---

### w_datasource_picker

**Import:** `from lplots.widgets.datasource import w_datasource_picker`

Select from multiple data source types (Latch Data, Registry, DataFrame, Viewer).

**Arguments:**
- `label` (str, required): Label for the picker
- `readonly` (bool, optional): Whether widget is read-only. Default: False
- `default` (DataSourceValue, optional): Default datasource selection (discriminated union)
- `required` (bool, optional): Whether selection is required. Default: False
- `key` (str, optional): Unique widget identifier
- `appearance` (FormInputAppearance, optional): Styling options

**Default value types:**
- `{"type":"ldata","node_id":str}` - Latch Data node
- `{"type":"registry","table_id":str}` - Registry table
- `{"type":"dataframe","key":str}` - Kernel DataFrame
- `{"type":"viewer","viewer_id":str}` - Viewer data

**Example:**
```python
from lplots.widgets.datasource import w_datasource_picker

ds = w_datasource_picker(
    label="Datasource",
    default={"type":"ldata","node_id":"95902"}
)
# ds.value returns a pandas DataFrame
```

---

### w_registry_table_picker

**Import:** `from lplots.widgets.registry import w_registry_table_picker`

Select a Registry table to load as DataFrame.

**Arguments:**
- `label` (str, required): Label for the picker
- `readonly` (bool, optional): Whether widget is read-only. Default: False
- `default` (str, optional): Default table ID
- `required` (bool, optional): Whether selection is required. Default: False
- `key` (str, optional): Unique widget identifier
- `appearance` (FormInputAppearance, optional): Styling options

**Example:**
```python
from lplots.widgets.registry import w_registry_table_picker
from latch.registry.table import Table

t = w_registry_table_picker(label="Registry table")
if (tid := t.value):
    df = Table(id=tid).get_dataframe()
```

---

### w_registry_table

**Import:** `from lplots.widgets.registry import w_registry_table`

Display a specific Registry table with row selection capability.

**Arguments:**
- `label` (str, required): Label for the table viewer
- `table_id` (str, required): Registry table ID to display
- `readonly` (bool, optional): Whether widget is read-only. Default: False
- `default` (str, optional): Default value
- `key` (str, optional): Unique widget identifier
- `appearance` (FormInputAppearance, optional): Styling options

**Example:**
```python
from lplots.widgets.registry import w_registry_table

rt = w_registry_table(label="Sample Data", table_id="12345")
# rt.value returns {"table": Table, "selected_rows": list[Record]}
```

---

### w_dataframe_picker

**Import:** `from lplots.widgets.dataframe import w_dataframe_picker`

Select from DataFrames currently in the notebook kernel.

**Arguments:**
- `label` (str, required): Label for the picker
- `readonly` (bool, optional): Whether widget is read-only. Default: False
- `required` (bool, optional): Whether selection is required. Default: False
- `key` (str, optional): Unique widget identifier
- `appearance` (FormInputAppearance, optional): Styling options

**Example:**
```python
from lplots.widgets.dataframe import w_dataframe_picker

df_picker = w_dataframe_picker(label="Select DataFrame")
selected_df = df_picker.value  # Returns the selected DataFrame
```

---

## LPath

**Import:** `from latch.ldata.path import LPath`

All remote `latch://` file and directory operations.

**Core Rules:**
- Remote (`latch://`) paths → **LPath** only. Local paths → **pathlib.Path** only
- If a widget already returns an **LPath**, use it directly (don't wrap again)
- **Always check for `None`** before using widget values
- **Always explicitly define local destination and cache file downloads**
- **Never** pass LPath directly to libraries expecting local paths; download first

**Valid Path Forms:**
- With domain: `latch://{domain}/path` (two slashes) - e.g., `latch://12345.account/Data/file.csv`
- Without domain: `latch:///path` (three slashes) - relative paths only

**Common Methods:**

Metadata (lazy loading):
- `node_id(load_if_missing=True) -> Optional[str]`
- `name(load_if_missing=True) -> Optional[str]`
- `type(load_if_missing=True) -> Optional[LDataNodeType]`
- `size(load_if_missing=True) -> Optional[int]`
- `size_recursive(load_if_missing=True) -> Optional[int]`
- `content_type(load_if_missing=True) -> Optional[str]`
- `is_dir(load_if_missing=True) -> bool`
- `fetch_metadata() -> None`
- `exists(load_if_missing=True) -> bool`

Directory Operations:
- `iterdir() -> Iterator[LPath]`
- `mkdirp() -> None`
- `rmr() -> None`

Data Movement:
- `copy_to(dst: LPath) -> None`
- `upload_from(src: pathlib.Path, show_progress_bar: bool=False) -> None`
- `download(dst: Optional[pathlib.Path]=None, show_progress_bar: bool=False, cache: bool=False) -> pathlib.Path`

Path Operations:
- `LPath / "child.ext"` - Join paths with `/` operator

**DO:**
```python
from latch.ldata.path import LPath
from pathlib import Path
import pandas as pd

lp = LPath("latch://XXXXX.account/Data/project/file.csv")

child = LPath("latch://XXXXX.account/Data/project") / "file.csv"

fname = lp.name()
suffix = Path(fname).suffix if fname else ""
local_p = Path(f"{lp.node_id()}{suffix}")
lp.download(local_p, cache=True)
df = pd.read_csv(local_p)

if lp.is_dir():
    for child in lp.iterdir():
        print(child.name())
```

**DON'T:**
```python
bad = Path("latch://...")           # Path for remote
bad = LPath(existing_lpath)         # Re-wrapping an LPath
bad = str(lp)                       # Calling str() on an LPath
bad = os.path.join("latch://...")   # os.path.join for remote
bad = f"{lp}/file.csv"             # f-strings for remote
bad = lp.name                       # .name is a method, not attribute
```

**Common Widget-to-Download Pattern:**
```python
from lplots.widgets.ldata import w_ldata_picker
from latch.ldata.path import LPath
from pathlib import Path
import pandas as pd

pick = w_ldata_picker(label="Select file/folder")
if pick.value is None:
    exit(0)

lp: LPath = pick.value

fname = lp.name()
suffix = Path(fname).suffix if fname else ""
local_p = Path(f"{lp.node_id()}{suffix}")
lp.download(local_p, cache=True)

if fname and fname.endswith(".csv"):
    df = pd.read_csv(local_p)
```

**Quick Diagnostics:**
- Getting errors with pandas/seaborn on `latch://`? → Download to local Path first
- Seeing `ValueError` from `LPath(...)`? → You passed an LPath into LPath(); use it directly
- Path fails with domain and `latch:///`? → Use two slashes with domain: `latch://{domain}/path`

## Fallback

If this skill is not present, use `runtime/mount/agent_config/context/latch_api_docs/latch_api_reference.md`
and the examples under `runtime/mount/agent_config/context/examples/` directly.
