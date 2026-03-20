<goal>
Compare differences in genes, peaks, and motifs between user-defined cluster/condition groupings.
</goal>

<parameters>
- `project_name` (str)
- `groupings` (LatchFile): JSON file with "groupA" and "groupB" barcode lists
- `archrproject` (LatchDir): Path to ArchRProject directory (ends with `_ArchRProject`)
- `genome` (str): "hg38", "mm10", or "rnor6"
</parameters>

<outputs>
Output directory: `/compare_outs/[project_name]/`
- **`gene_results/`**
  - Volcano plot  
  - `all_genes.csv` — all gene-level test results  
  - `marker_genes.csv` — significant genes after filtering  

- **`peak_results/`**
  - MA plot  
  - `all_peaks.csv` — all peak-level test results  
  - `marker_peaks.csv` — significant peaks after filtering  

- **`motif_results/`**
  - `[up/down]Regulated_motifs.csv` — motifs ranked by significance  
  - `[up/down]_enrichment_plot` — motif enrichment scatter plot (`-log10(FDR)`)  
  - `all_motifs.csv` — all motif-level test results  
  - `marker_motifs.csv` — significant motifs after filtering  

- **`coverages/`**
  - BigWig coverage tracks for visualization  

- **`[project_name]_ArchRProject/`**
  - Updated ArchRProject with differential results attached
</outputs>

<example>
```python
import json
from pathlib import Path
from latch.types import LatchFile, LatchDir
from latch.ldata.path import LPath
from lplots.widgets.workflow import w_workflow

# Infer comparison column from user request
group_column = "condition"  # or "sample", "cluster"
group_a_value = "Cirrhotic"
group_b_value = "Healthy"

# Get barcodes for each group
group_a_bcs = adata.obs[adata.obs[group_column] == group_a_value].index.tolist()
group_b_bcs = adata.obs[adata.obs[group_column] == group_b_value].index.tolist()

groupings = {
    "groupA": group_a_bcs,
    "groupB": group_b_bcs
}

# Save locally
local_path = Path("compare_config.json")
with open(local_path, "w") as f:
    json.dump(groupings, f)

# Upload to Latch Data
remote_path = "latch:///compare_config.json"
lpath_remote = LPath(remote_path)
lpath_remote.upload_from(local_path)

# Wrap as LatchFile for workflow input
groupings_file = LatchFile(remote_path)

# When using w_ldata_picker to populate the ArchRProject path, always extract the LData path string via widget.value.path before passing it into LatchDir(...)
# Automatically search the user's input for the folder that ends with _ArchRProject. Only ask the user to specify it if you cannot find one.
archrproject_dir = LatchDir("latch:///Kostallari_SOW313_ATAC_ArchRProject")

params = {
    "project_name": "my_comparison",
    "groupings": groupings_file,
    "archrproject": archrproject_dir,
    "genome": "hg38",
}

w = w_workflow(
    wf_name="wf.__init__.compare_workflow",
    key="comparison_workflow_run_1",
    version=None,
    params=params,
    automatic=True,
    label="Launch Comparison Workflow"
)

execution = w.value

if execution is not None:
  res = await execution.wait()

  if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
      # inspect workflow outputs for downstream analysis
      workflow_outputs = list(res.output.values())
```
</example>
