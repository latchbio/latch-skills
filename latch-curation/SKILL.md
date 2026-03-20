---
name: latch-curation
description: >
  Use this skill when curating, harmonizing, or standardizing external data
  (GEO/GSE/GSM, collaborator uploads, paper data) into Latch-compatible AnnData
  objects with ontology-annotated metadata.
---

# Latch Curation

Use this skill for data curation pipelines that download, parse, standardize,
and harmonize external datasets into Latch-compatible AnnData objects.

## Use this skill when

- User mentions "curate", "harmonize", "standardize", or "publish"
- Working with external data (paper, collaborator, GSE/GSM accession)
- User has paper text to incorporate into analysis
- Needs metadata cleanup for sharing
- Needs to convert gene symbols to Ensembl IDs
- Needs to add ontology-annotated `latch_*` columns

## Library setup

```python
import sys
sys.path.insert(0, "/opt/latch/plots-faas/.claude/skills/latch-curation/lib")
from curate import (
    gsm_to_gse,
    get_subseries_ids,
    construct_study_metadata,
    download_gse_supplementary_files,
    list_gse_supplementary_files,
    download_gse_metadata,
    download_srp_metadata,
    is_valid_ensembl,
    ensembl_to_symbol,
    symbol_to_ensembl,
    convert_and_swap_symbol_index,
    reindex_and_fill_list,
    validate_counts_object,
    format_validation_report,
    all_checks_passed,
)
```

---

## Pipeline overview

Only ask for:
1. **GSE ID or uploaded files** (required)
2. **Paper text** (strongly encouraged) — via widget, not chat

### Plan

1. Download → see **Step 1: Download**
2. Construct Counts → see **Step 2: Construct Counts**
3. **Merge with technology-specific plan** → detect platform from metadata, then load the matching technology skill
4. Harmonize Metadata → see **Step 3: Harmonize Metadata** (run at end of analysis)

### Platform detection

After download + construct_counts, detect platform from `tmp/{accession}/study_metadata.txt`:

| Indicator in metadata | Technology skill |
|-----------------------|-----------------|
| "Xenium" or GPL33896 | xenium skill |
| "Visium" | visium skill |
| "Vizgen" or "MERFISH" | vizgen skill |
| "Takara" or "ICELL8" | takara skill |
| "AtlasXomics" | atlasxomics skill |

Follow the technology-specific plan for QC, normalization, clustering, cell typing.
At each step, supplement with curation context from `study_metadata.txt` and `paper_text.txt`.

### Inference rules

Infer from data — do not ask upfront:

| Field | Source |
|-------|--------|
| Organism | Gene ID prefix (ENSG → human, ENSMUSG → mouse) |
| Platform | `study_metadata.txt` platform_id, label_ch1 |
| Tissue | GEO source_name_ch1 or paper methods |
| Disease | GEO characteristics or paper |
| Cell types | Analysis results → Cell Ontology |

Only ask when inference is ambiguous or validation fails.

---

## Step 1: Download

**Goal**: Download study metadata and supplementary files from GEO. Collect paper context.

**1. Create paper text widget first (do not skip):**
```python
from lplots.widgets.text import w_text_input

paper_input = w_text_input(label="Paper Text")
```
Tell user: "Paste paper text (abstract/methods/results) in the widget while I download the GEO data."

**2. Setup and convert GSM → GSE if needed:**
```python
from pathlib import Path

if accession.upper().startswith("GSM"):
    accession = gsm_to_gse(accession) or accession

CONTEXT_DIR = Path(f"/opt/latch/plots-faas/.claude/skills/latch-curation/tmp/{accession}")
CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
```

**3. Download metadata and files:**
```python
(CONTEXT_DIR / "study_metadata.txt").write_text(construct_study_metadata(accession))
downloaded_paths = download_gse_supplementary_files(accession, target_dir)
(CONTEXT_DIR / "downloaded_files.txt").write_text("\n".join(str(p) for p in downloaded_paths))
```

**4. Save paper text (after user fills widget):**
```python
if paper_input.value and paper_input.value.strip():
    (CONTEXT_DIR / "paper_text.txt").write_text(paper_input.value)
```

**Self-eval:**
- Paper text widget displayed and user informed to fill it
- `study_metadata.txt` written with platform info
- `downloaded_files.txt` written with valid file paths
- `paper_text.txt` written (confirm user provided input)

---

## Step 2: Construct Counts

**Goal**: Parse downloaded supplementary files into a standardized AnnData with Ensembl gene IDs, sample identifiers, and raw counts.

**Context files** (read from download step):
- `tmp/{accession}/study_metadata.txt`
- `tmp/{accession}/paper_text.txt`
- `tmp/{accession}/downloaded_files.txt`

**1. Inspect downloaded files:**
- Read `downloaded_files.txt` to get file paths
- Examine file types (.csv, .tsv, .h5ad, .mtx, etc.)
- Use paper_text and study_metadata for context

**2. Parse files into AnnData:**

For existing H5AD:
```python
import anndata as ad
adata = ad.read_h5ad(input_path)
```

For CSV/TSV count matrices:
```python
import pandas as pd
from anndata import AnnData

counts_df = pd.read_csv(counts_path, index_col=0)
adata = AnnData(X=counts_df.values, obs=pd.DataFrame(index=counts_df.index), var=pd.DataFrame(index=counts_df.columns))
```

For 10X MTX format:
```python
import scanpy as sc
adata = sc.read_10x_mtx(mtx_dir)
```

**3. Standardize gene IDs:**
```python
if not all(is_valid_ensembl(g) for g in adata.var_names[:100]):
    adata = convert_and_swap_symbol_index(adata)
```

**4. Add sample identifier:**
```python
adata.obs["latch_sample_id"] = sample_name
adata.obs_names = [f"{sample_name}_{bc}" for bc in adata.obs_names]
```

**5. Prefix author metadata:**
```python
for col in adata.obs.columns:
    if col != "latch_sample_id" and not col.startswith("author_"):
        adata.obs.rename(columns={col: f"author_{col}"}, inplace=True)
```

**6. Merge multiple samples:**
```python
import anndata as ad

adatas = reindex_and_fill_list(adatas)
combined = ad.concat(adatas, join="outer")
```

**7. Validate:**
```python
validation_log = validate_counts_object(adata)
print(format_validation_report(validation_log))

if not all_checks_passed(validation_log):
    # Fix issues and re-validate
    pass
```

**8. Save and record path:**
```python
output_path = Path("./output.h5ad")
adata.write_h5ad(output_path)
(CONTEXT_DIR / "constructed_h5ad.txt").write_text(str(output_path.resolve()))
```

**Self-eval:**
- All validation checks pass (`all_checks_passed()`)
- Cell count roughly matches paper expectation
- `constructed_h5ad.txt` written with valid path
- No data loss (didn't subset/sample/drop cells)

---

## Step 3: Harmonize Metadata

**Goal**: Add required `latch_*` columns with ontology terms, inferred from analysis results and context files. Run at end of analysis after cell typing is complete.

Read `tmp/{accession}/study_metadata.txt` and `paper_text.txt`. Map inferred values to ontology terms.

### Required obs columns

| Column | Format | Source |
|--------|--------|--------|
| `latch_sample_id` | string | GEO title or user input |
| `latch_cell_type_lvl_1` | "name/CL:NNNNNNN" | Cell typing results |
| `latch_disease` | "name/MONDO:NNNNNNN" | Paper/metadata |
| `latch_tissue` | "name/UBERON:NNNNNNN" | GEO source_name or paper |
| `latch_organism` | "Homo sapiens" / "Mus musculus" | Gene ID prefix |
| `latch_sequencing_platform` | "name/EFO:NNNNNNN" | Platform from metadata |
| `latch_subject_id` | string | GEO characteristics |
| `latch_condition` | free text | Paper/GEO metadata |
| `latch_sample_site` | string | GEO characteristics |

### Required var columns

- `var.index`: Ensembl gene IDs (ENSG/ENSMUSG format)
- `gene_symbols`: Human-readable gene names (unique)

---

## Library API reference

### curate.geo

**`gsm_to_gse(gsm_id: str) -> str | None`**
GSM sample ID → parent GSE series ID. Returns None if not found.
Call this first if user provides a GSM. All other functions expect GSE.

**`get_subseries_ids(gse_id: str) -> list[str]`**
Returns list of SubSeries GSE IDs for a SuperSeries.

**`download_gse_metadata(gse_id: str) -> pd.DataFrame`**
Downloads and returns GEO sample metadata as a DataFrame.

**`download_srp_metadata(gse_id: str) -> pd.DataFrame | None`**
Downloads SRA metadata for a GSE. Returns None if not found.

**`construct_study_metadata(gse_id: str) -> str`**
Combines SRP and GSE metadata into a formatted string with `<srp_metadata>` and `<gse_metadata>` tags.

**`list_gse_supplementary_files(gse_id: str) -> list[str]`**
Preview available supplementary filenames without downloading.

**`download_gse_supplementary_files(gse_id: str, target_dir: Path) -> list[Path]`**
Downloads all supplementary files to `target_dir`. Returns list of local paths.

### curate.parsing

**`is_valid_ensembl(id_: str) -> bool`**
Checks if a string matches the Ensembl gene ID pattern (`ENS[A-Z0-9]{0,5}G\d{11}`).

**`ensembl_to_symbol(id_: str) -> str | None`**
Converts an Ensembl ID to gene symbol. Returns None if not found.

**`symbol_to_ensembl(sym: str) -> str | None`**
Converts a gene symbol to Ensembl ID. Returns None if not found.

**`convert_and_swap_symbol_index(adata: AnnData) -> AnnData`**
Converts gene symbols in `var.index` to Ensembl IDs. Moves original symbols to `var["gene_symbols"]`. Drops genes without a mapping. Deduplicates.

**`reindex_and_fill_list(adatas: list[AnnData]) -> list[AnnData]`**
Reindexes a list of AnnData objects to the union of all gene features, filling missing genes with zeros. Use before `ad.concat()`.

### curate.validation

**`validate_counts_object(adata: AnnData) -> list[tuple[str, str]]`**
Runs all validation checks. Returns list of `(status, message)` tuples where status is "pass" or "fail".

Checks: `latch_sample_id` exists, var index is Ensembl, `gene_symbols` exists and unique, obs/var index unique, counts non-negative integers, matrix has non-zero values, `author_*` columns not all NaN.

**`format_validation_report(validation_log: list[tuple[str, str]]) -> str`**
Formats validation log as a human-readable report.

**`all_checks_passed(validation_log: list[tuple[str, str]]) -> bool`**
Returns True if all checks passed.

---

## Self-eval criteria (final)

- Required obs columns present with valid ontology terms
- `var.index` contains valid Ensembl IDs
- `gene_symbols` exists and is unique
- Counts are raw integers (ingestion) or normalized (after transform)
- No "unknown" where paper/metadata provides information
- Cell type proportions biologically plausible
- Organism matches gene ID prefix (ENSG=human, ENSMUSG=mouse)
