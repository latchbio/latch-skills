<goal>
Identify cell types using either fast gene set scoring or detailed cluster-based annotation approaches.
</goal>

<method>
## Critical Decision (MUST ASK)

Ask user:
1. "Are you confident in your current clustering quality?"
2. "Do you prefer fast exploratory annotation or slower detailed annotation?"

**Choose approach:**
- Unsatisfactory clusters OR want fast (~minutes per sample) → **Gene Set Scoring** (`steps/cell_type_annotation/gene_set_scoring.md`)
- Good clusters AND can wait >30 minutes → **Cluster-based** (`steps/cell_type_annotation/cluster_based.md`)

## Input: `*_sm_ge.h5ad` (gene activity scores)

## CellGuide Databases

Curated reference from CELLxGENE linking cell types to canonical marker genes across tissues/species. Aggregates annotations from thousands of single-cell studies with standardized marker sets.

Load databases from Latch Data:
- `latch:///cellguide_marker_gene_database_per_gene.json` - Maps genes to cell types (use for automated annotation)
- `latch:///cellguide_marker_gene_database_per_celltype.json` - Maps cell types to marker genes (use for validation)
- `latch:///tissues_per_organism.json` - Available tissues per organism (use for input validation)
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- Cell type proportions are biologically plausible
- Use capture image tool and check whether spatial location of cell types make sense
- Inspect violin plots and verify that canonical markers show enrichment for the predicted cell type versus all others
</self_eval_criteria>
