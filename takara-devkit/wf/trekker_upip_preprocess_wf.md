<goal>
Convert TrekkerU_PIP (PIPSeeker) FASTQ and scRNA-seq files into Trekker-compatible formats before running the Trekker pipeline
</goal>

<parameters>
- **FASTQ directory** → `fastq_dir` (`LatchDir`, **required**)
  - Directory on Latch containing all TrekkerU_PIP R1 `.fastq.gz` files for the sample. No spaces in path.
- **FASTQ filename prefix** → `fastq_prefix` (`str`, **required**)
  - The shared filename prefix across all R1 FASTQ files in `fastq_dir`.
  - Example: if the files are `sample1_01_R1.fastq.gz` and `sample1_02_R1.fastq.gz`, the prefix is `"sample1"`.
  - No spaces allowed.
- **Single-cell directory** → `sc_directory` (`LatchDir`, **required**)
  - Directory containing the Fluent BioSciences PIPseeker pipeline output. Must contain exactly:
    - `barcodes.tsv.gz`
    - `features.tsv.gz`
    - `matrix.mtx.gz`
- **Chemistry** → `chemistry` (`str`, **required**)
  - The Fluent BioSciences chemistry version used. Ask the user and map to the correct string:

    | String value | Chemistry |
    |---|---|
    | `"V"` | PIPseq V |
    | `"v3"` | PIPseq v3 |
    | `"v4"` | PIPseq v4 |

- **Output directory** → `output_directory` (`LatchOutputDir`, **required**)
  - Destination directory on Latch for all converted output files.
  - Must be provided by the user — do not use a default or placeholder value.
</parameters>

<outputs>
The workflow writes the following to `output_directory`:

```
<output_directory>/
    <fastq_prefix>_converted_R1.fastq.gz   ← converted Read 1
    converted_sc/
        barcodes.tsv.gz                     ← converted barcodes
        features.tsv.gz                     ← unchanged copy
        matrix.mtx.gz                       ← unchanged copy
```

**Feeding outputs into the Trekker pipeline:**
- Use `<fastq_prefix>_converted_R1.fastq.gz` as `fastq_cb` (Read 1) for Trekker.
- Use the **original** R2 `.fastq.gz` file (unchanged, from the user's input data) as `fastq_tags` (Read 2) for Trekker.
- Use the `converted_sc/` output directory as `sc_outdir` for Trekker — **do not** use the original `sc_directory`.
</outputs>

<example>
```python
from lplots.widgets.workflow import w_workflow
from latch.types import LatchFile, LatchDir

params = {
    "fastq_dir": LatchDir("latch://38771.account/.../pip_fastqs/"),
    "fastq_prefix": "sample1",
    "sc_directory": LatchDir("latch://38771.account/.../fluent_sc_output/"),
    "chemistry": "V",                             # "V", "v3", or "v4"
    "output_directory": LatchDir("<latch://...>"),  # required — set by user
}

w = w_workflow(
    wf_name="wf.__init__.trekker_upip_converter",
    key="trekker_upip_preprocess_run_1",
    version="1.0.0",
    params=params,
    automatic=True,
    label="TrekkerU_PIP preprocessing",
)
execution = w.value

if execution is not None:
    res = await execution.wait()

    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        workflow_outputs = list(res.output.values())
```
</example>
