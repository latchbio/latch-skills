<goal>
Assess DBiT-seq epigenomic experiment quality and systematically explore clustering parameter combinations. Generate multiple H5AD outputs—each clustered with different parameter settings—along with summary statistics to guide downstream analysis.
</goal>

<parameters>
**Required**:
- `project_name` (str)
- `genome` (Enum): "hg38", "mm10", "rnor6"
- `runs` (List[Run]): Each with:
  - `run_id` (str)
  - `fragments_file` (LatchFile)
  - `spatial_dir` (LatchDir)
  - `condition` (str, optional)

**Recommended Defaults**:
- `n_features`: [25_000, 50_000, 100_000]
- `resolution`: [0.5, 1.0, 1.25, 1.5] (AtlasXomics needs ≥0.5)
- `n_comps`: [30, 50]

**Optional Parameters**:
- `combined_h5ad_override` (LatchFile): Precomputed `combined.h5ad` to use instead of building one from the runs
- `tile_size` (int): Genomic bin size (default: 5000)
- `varfeat_iters` (List[int]): Variable feature iterations (default: [1])
- `leiden_iters` (int): Leiden iterations, `-1` = until convergence (default: -1)
- `min_cluster_size` (int): Minimum cells per cluster (default: 20)
- `min_tss` (float): Minimum TSS enrichment (default: 2.0)
- `min_frags` (int): Minimum fragments per cell (default: 10)
- `subsample_fraction` (float or None): Fraction of cells to retain before optimization
- `subsample_n_cells` (int or None): Absolute number of cells to retain
- `subsample_seed` (int): Random seed for subsampling (default: 42)
- `pt_size` (int or None): Point size for spatial plots
- `qc_pt_size` (int or None): Point size for QC plots
</parameters>

<outputs>
Output directory: `/epi_optimize_snap/[project_name]/`  (legacy: `/snap_opts/`, briefly `/atac_optimize_snap/`)
- `combined.h5ad`: the shared combined AnnData (tile matrix, filters, spatial coords)
- `figures/`: `all_umaps.png`, `all_spatialdim.png`, `spatial_qc.png`, `tss_frags.png` — one page per parameter set
- `all_umaps.html`, `all_spatialdim.html`, `spatial_qc.html`: browsable galleries for side-by-side comparison of sets
- `medians.csv`: QC metrics summary for all samples
- `_intermediate/_mapped_sets/[set]/`: per-parameter-set outputs, each with its own `combined.h5ad`
</outputs>

<example>
```python
from dataclasses import dataclass
from enum import Enum
from latch.types import LatchFile, LatchDir
from latch.ldata.path import LPath
from lplots.widgets.ldata import w_ldata_picker
from lplots.widgets.text import w_text_output, w_text_input
from lplots.widgets.select import w_select
from lplots.widgets.workflow import w_workflow

class Genome(Enum):
    mm10 = "mm10"
    hg38 = "hg38"
    rnor6 = "rnor6"

@dataclass
class Run:
    run_id: str
    fragments_file: LatchFile
    spatial_dir: LatchDir
    condition: str = "None"

# 1) Pick the two source folders.
#    Fragments and spatial folders live in SEPARATE top-level directories:
#      fastq2frags/[Run_ID]/chromap_output/fragments.tsv.gz
#      spatials/[Run_ID]/spatial
#    (Legacy layout kept both under one Raw_Data/[Run_ID]/ folder — if you're
#     working with older data, point both pickers at that same folder.)
frags_dir = w_ldata_picker(label="Fragments Directory (fastq2frags)")
spatial_dir_root = w_ldata_picker(label="Spatial Directory (spatials)")
if frags_dir.value is None or spatial_dir_root.value is None:
    w_text_output(
        content="Select the fastq2frags and spatials folders (each contains per-run subfolders).",
        appearance={"message_box": "warning"}
    )
    exit(0)

frags_root: LPath = frags_dir.value      # already an LPath
spatial_root: LPath = spatial_dir_root.value

# 2) Samples + condition map
samples = adata.obs["sample"].unique()
cond_map = (adata.obs.groupby("sample")["condition"].first().to_dict()
            if "condition" in adata.obs.columns
            else {s: "None" for s in samples})

# 3) Helper to join remote paths (LPath uses "/" join)
def rpath(root: LPath, *parts: str) -> LPath:
    p = root
    for part in parts:
        p = p / part
    return p  # still LPath

# 4) Build runs (convert to LatchFile/Dir via .path, not str())
runs = []
for s in samples:
    print(s)
    frag_lp: LPath = rpath(frags_root, str(s), "chromap_output", "fragments.tsv.gz")
    spat_lp: LPath = rpath(spatial_root, str(s), "spatial")

    runs.append(
        Run(
            run_id=str(s),
            fragments_file=LatchFile(frag_lp.path),  # latch://...
            spatial_dir=LatchDir(spat_lp.path),      # latch://...
            condition=cond_map[str(s)],
        )
    )

# 5) Construct params with minimal form for user input
project_name = w_text_input(label="Project name", default="atlasx_clustering")
genome = w_select(label="Genome", options=[g.value for g in Genome], default="hg38")
resolution = w_text_input(label="Resolution(s)", default="0.5")

def to_list_of_floats(text: str):
    return [float(x.strip()) for x in text.split(",") if x.strip()]

params = {
     "runs": runs, 
     "combined_h5ad_override": LatchFile("latch:///combined.h5ad"),  # optional
     "genome": genome.value,
     "project_name": project_name.value,
     "tile_size": 5000,
     "n_features": [25000],
     "resolution": to_list_of_floats(resolution.value),
     "varfeat_iters": [1],
     "n_comps": [30],
     "min_cluster_size": 20,
     "min_tss": 2.0,
     "min_frags": 10,
     "pt_size": None,
     "qc_pt_size": None,
}

w = w_workflow(
  wf_name="wf.__init__.opt_workflow",
  key="clustering_workflow_run_1",
  version=None,  # None = latest registered version; pin a "<version>-<hash>" string only if you need reproducibility
  params=params,
  automatic=True,
  label="Run clustering workflow",
)

execution = w.value

if execution is not None:
  res = await execution.wait()

  if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
      # inspect workflow outputs for downstream analysis
      workflow_outputs = list(res.output.values())
```
</example>

