<goal>
Perform strict QC and filtering of Vizgen MERFISH data.
</goal>

<method>
For each QC metric — **total counts**, **detected genes**, and **cell volume** — perform the following:

1/ Compute all QC metrics using Scanpy.  
2/ Make **mandatory histograms** for every metric.  
3/ For **cell volume**, always visualize its distribution (must never be skipped).  
4/ Plot spatial coordinates at different threshold ranges to reveal morphological effects.  
5/ Expose each filtering threshold using `w_text_input` (one metric at a time).  
6/ Report how many cells would be removed before filtering.  
7/ Ask the user for confirmation using lplots widgets.  
8/ If declined, revert to the original AnnData with no changes.  
9/ If approved, apply the filter and proceed to the next metric.

Always follow this sequence honestly and strictly.
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- QC histograms show expected distributions (not all cells at extremes)
- Cell volume distribution reflects biological variation (not uniform)
- Detected genes per cell is substantial (hundreds from MERFISH panel)
- Filtering removes <30% of cells (excessive removal suggests threshold issues)
- Spatial patterns remain coherent after filtering (no large spatial gaps)
</self_eval_criteria>