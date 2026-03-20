<goal>
Fast exploratory cell type annotation by scoring curated marker gene panels. No clustering required.
</goal>

<method>

## Workflow Summary

0. **Check dataset scale** — Inspect samples, cells, and memory usage
   - **⚠️ CRITICAL**: Large datasets (>2GiB) require sample-by-sample processing
   - **NEVER** process all samples together - causes memory crashes and poor annotations
   - **Required approach for multi-sample data:**
     1. Subset to ONE sample
     2. Complete ENTIRE workflow on subset
     3. Validate results thoroughly
     4. Only then repeat for remaining samples

1. **Select cell types** — Choose 5-10 major types expected in tissue
2. **Curate markers** — Extract 40-50 genes per type from CellGuide  
3. **Filter markers** — Keep discriminatory genes (high fold change)
4. **Balance markers** — Ensure equal counts across cell types
5. **⚠️ CRITICAL: Normalize scores** - z-score or min-max
6. **Assign & visualize cell types** — Label by highest normalized score. 
7. 
---

## Step 1: Select Expected Cell Types

Choose **5-10 major cell types** realistic for your tissue and organism. Focus on broad categories rather than fine subtypes.

---

## Step 2: Curate Marker Panels from CellGuide

Extract **40-50 top-ranked markers** per cell type from the CellGuide database.

**Note**
- CellGuide names may not match the cell type names you’re looking for exactly.
- The database is comprehensive and includes broad categories, subtypes, and synonyms.
- Prioritize biological equivalence over exact string matches when searching for cell types and markers. 

**Why 40-50?**
- Expect 20-40% retention after discriminatory filtering
- Ensures ≥5 markers remain per cell type after filtering
- CellGuide ranks by marker strength — top markers are highest quality

**Data source:** `latch:///cellguide_marker_gene_database_per_celltype.json` from Latch Data

Filter to genes present in your dataset (`adata.var_names`)

---

## Step 3: Filter for Discriminatory Markers

**⛔ STOP**: If the dataset exceeds 2 GiB, you must subset to a single sample before running this step.

Evaluate each marker's ability to distinguish cell types by computing **median fold change** across all cluster pairs.

### Recommended Thresholds by Assay Type

| Assay Type | Threshold | Expected Retention | Rationale |
|------------|-----------|-------------------|-----------|
| **ATAC-seq gene activity** | **1.2×** | 20-40% | Lower dynamic range, sparser signal |
| RNA-seq (scRNA/spatial) | 1.5-2.0× | 30-50% | Higher sensitivity and dynamic range |
| Protein (CITE-seq) | 2.0-3.0× | 40-60% | High specificity required |

**Key insight:** ATAC-seq gene activity scores are inherently sparser than RNA expression. **1.2× threshold** is recommended for ATAC-seq data.

**Method:** For each marker, compute median expression per cluster, then calculate pairwise fold changes. Keep markers where median fold change across all pairs exceeds threshold.

**Quality check:** After filtering, verify **each cell type retains ≥2 markers AND there are ≥3 cell types**. If not, lower threshold to 1.05-1.1× or increase initial marker count to 50-60.

---

## Step 4: Balance Marker Counts (Target: 5 markers per cell type)

### ⚠️ CRITICAL: Prevent Scoring Bias

**Problem:** Unequal marker counts create systematic bias. A cell type with 20 markers will outscore one with 5 markers regardless of biological signal.

**Solution:** Equalize marker counts across all cell types.

**Method:**
1. Calculate target count (median or minimum of filtered marker counts)
2. Enforce minimum of 2 markers per cell type
3. Take top 5 markers by fold change for each cell type
4. Only include cell types with ≥3 final markers

**Result:** All cell types have equal "voting power" during scoring.

---

## Step 5: Compute Raw Gene Set Scores

Calculate **mean expression** across each cell type's marker panel for every cell.

**Formula:** For each cell and cell type, score = mean(expression of all markers for that cell type)

This produces a score matrix: cells × cell types

---

## Step 6: ⚠️ CRITICAL — Normalize Scores

### Why Normalization is Non-Negotiable

**Raw mean scores are NOT comparable across cell types** due to:
- Different baseline expression levels across marker sets
- Varying dynamic ranges of marker expression
- Technical biases in specific gene accessibility

**Without normalization:** Cell types with high baseline marker expression will dominate predictions (typically 80-99% mis-classification to a single type).

### Normalization Methods

**Z-score normalization (RECOMMENDED for ATAC-seq):**
- Centers each cell type at mean=0, std=1
- Formula: `(score - mean) / std` for each cell type
- Makes scores directly comparable across all cell types

**Min-max scaling (alternative):**
- Scales each cell type to 0-1 range
- Formula: `(score - min) / (max - min)`
- Useful when z-scores have outliers

**Rank-based (conservative):**
- Converts scores to percentile ranks
- Most robust but loses magnitude information

**For ATAC-seq data: Always use z-score normalization.**

---

## Step 7: Assign Cell Types

After normalization:
1. For each cell, identify the cell type with the **highest normalized score**
2. Calculate **prediction confidence** = difference between top and second-highest score
3. Add predictions and confidence to `adata.obs`
4. Visualize predicted cell types.

Higher confidence (>0.3) indicates clear cell type identity. Lower confidence (<0.15) suggests ambiguous or mixed populations.

</method>
