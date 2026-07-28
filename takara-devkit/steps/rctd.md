<goal>
Assign reference-based cell types to every bead using Robust Cell Type Deconvolution (RCTD), and merge the results back into the working AnnData so later annotation can use them.

**Seeker only.** Skip this step entirely for Trekker data — RCTD's doublet mode assumes ~1–3 cells per bead, which is a Seeker property. If the kit type is unknown, ask: "Was this data generated with a Seeker or Trekker kit?"

**Optional and separate.** RCTD is an optional, reference-based track that runs **after QC + Filtering** on the raw-count, pre-normalization AnnData. It does **not** depend on normalization, feature selection, dimensionality reduction, clustering, or DEG, and those steps run unchanged whether or not RCTD is used. RCTD's per-bead labels are consumed later, at Cell Type Annotation (`steps/cell_typing.md`), to label and validate Leiden clusters — it complements, and does not replace, marker-based annotation.

**Division of labor.** *You* (the Agent) are responsible for finding the most appropriate reference for the user's tissue across multiple public atlases and presenting choices. The `rctd_reference_builder` workflow is a **pure converter** — give it one chosen reference (a `.h5ad`/`.rds` file or a download URL) and it returns a version-compatible spacexr `Reference` `.rds`. It does **not** search anything.
</goal>

<method>
### When to offer
After QC + Filtering completes, offer RCTD to Seeker users:
> "Optionally, I can run RCTD to assign cell types to each bead using a single-cell reference. This complements the cluster-based annotation later. Would you like to run it?"

If yes, proceed. RCTD needs the **QC-filtered, raw-count** AnnData (raw counts in `.X`, spatial coordinates in `.obsm`) — use it **before** normalization. If normalization has already overwritten `.X`, recover raw counts from the raw layer or re-derive from the QC-filtered object.

### Step 1 — Find and choose a reference (Agent-driven)

RCTD needs a single-cell reference whose cell types and genes match the tissue. Drive this conversationally:

**1a. Collect tissue details.** Ask the user (combine into one or two friendly prompts; don't interrogate):
- **Organism** (required) — e.g. human, mouse, rat, zebrafish, axolotl, …. Any organism is allowed; the reference just has to exist somewhere.
- **Tissue / anatomical region** (required) — e.g. kidney cortex, hippocampus, whole embryo, lung.
- **Disease / condition** (required) — e.g. healthy/normal, tumor, fibrosis, a specific disease.
- **Developmental stage** (optional, ask only when it matters) — e.g. adult, neonatal, a specific embryonic stage (E12.5). Stage is pivotal for developmental/embryo samples; skip it for ordinary adult tissue.
- If anything is ambiguous (sub-region, exact condition, granularity of cell types wanted), ask a brief follow-up before searching.

**1b. Search multiple sources for candidates.** Using your web-search / browsing capability, look across **several** atlases — do not rely on a single source. Good starting points by domain:
- **CZ CELLxGENE Discover** (`cellxgene.cziscience.com`) — human + mouse, standardized `cell_type` ontology, per-dataset `.h5ad` download. The best default when it has the tissue.
- **Tabula Sapiens** (human) / **Tabula Muris** (mouse) — broad healthy multi-tissue references (`.h5ad` on CELLxGENE / figshare).
- **Allen Brain Cell Atlas / Allen Brain Map** — brain and nervous-system references.
- **TOME — Trajectories of Mouse Embryogenesis** (Qiu et al. 2022, E3.5–E13.5) and **MOCA — Mouse Organogenesis Cell Atlas** (Cao et al. 2019) — the right place for **mouse embryo / developmental stages**, which general atlases cover sparsely.
- **NCBI GEO** — processed reference matrices/objects in dataset supplementary files (use when a specific study is the best match).
- **Others as appropriate** — Human Cell Atlas Data Portal, organism-specific atlases (e.g. zebrafish/axolotl atlases), study-specific datasets. For non-human/mouse organisms, organism-specific atlases and GEO studies are usually the only option.

For each candidate, capture: organism, tissue/region, disease/condition, developmental stage, **number of cells**, **number of distinct cell types**, the cell-type label column, the source/atlas, and a **direct download URL** to a `.h5ad` or `.rds` (or, if no public direct link, note that the user must download and attach it).

**1c. Present candidates and let the user choose.** Show **1–10** options as a short numbered list with those descriptions, ordered best-match first, with a one-line recommendation. Prefer references that match organism (required) → tissue → disease → developmental stage, have appropriately granular cell types, and a stable downloadable file. Ask the user to pick one (or ask a clarifying question if several tie).

**1d. If no compatible reference is found.** Don't dead-end:
1. Tell the user what you searched and why nothing matched, then **ask for more detail** (a more specific or a broader tissue term, an alternative organism name, a related model system, does the user have a particular repository that they want to search) and **search again**.
2. If it still fails, fall back to **user-supplied**: ask the user to either
   - download a reference to **LData** and provide it either by selecting it in a `w_ldata_picker` (`file_type="file"`) you render, or with the attach button in the Agent interface (a `.h5ad`, or a `.rds` that is a spacexr `Reference` or Seurat object), **or**
   - paste a **direct download URL** to such a file.

**1e. Convert the chosen reference.** Hand the single chosen reference to the builder (`wf/rctd_reference_builder_wf.md`):
- A **download URL** (from your search or from the user) → pass as `reference_url`.
- A **user-attached LData file** → pass as `reference_file`.
- Confirm the **cell-type column**: CELLxGENE references use `cell_type`; for other sources or user files, confirm which `.obs` / `meta.data` column holds the labels and pass it as `cell_type_column` (if it's wrong the builder lists the available columns so you can correct and relaunch).

The builder downloads (if a URL), standardizes, curates (drops tiny cell types, caps cells per type), and emits `<run_name>_reference.rds` — a spacexr `Reference` built under the pinned Seurat 4.4.0 stack, so it is guaranteed compatible with RCTD regardless of the original format. That `.rds` becomes `reference_data`. See `wf/rctd_reference_builder_wf.md`.

### Step 2 — Run RCTD
1. Write the QC-filtered, raw-count AnnData to Latch as `.h5ad` (it must carry spatial coordinates in `.obsm["spatial"]` or `.obsm["X_spatial"]`).
2. Launch RCTD with that query and the reference `.rds` per `wf/rctd_wf.md`. Doublet mode is automatic — tell the user, and do not pass a mode parameter.

### Step 3 — Merge results back
After RCTD completes, load `<run_name>_RCTD.h5ad` (or `<run_name>_RCTD_annotation.txt`) and merge `first_type`, `second_type`, and `spot_class` into the working AnnData's `.obs`, joined on the bead barcode (align indices; not every input bead is necessarily classified). Then:
- Visualize `first_type` on the spatial embedding (and on UMAP once it exists) with `w_h5`.
- Report the distribution of `spot_class` (singlet / doublet_certain / doublet_uncertain / reject) and the cell-type composition.

These `.obs` columns persist for `steps/cell_typing.md`, which cross-tabulates `first_type` against the Leiden clusters. After merging, continue the normal secondary-analysis track (normalization → … → annotation).
</method>

<workflows>
- `wf/rctd_reference_builder_wf.md` — converts the chosen reference (file or URL) into a compatible `.rds`.
- `wf/rctd_wf.md` — runs the deconvolution.
</workflows>

<library>
</library>

<self_eval_criteria>
- The chosen reference's organism matches the data; its tissue, condition, and (if relevant) developmental stage are a sensible match for the sample.
- Reference and query share a non-zero set of genes (RCTD errors on zero overlap — the builder reports the reference gene count; sanity-check it against the query's genes before launching).
- The cell types present in the reference are plausible for the user's tissue.
- After running, the fraction of beads classified as `singlet`/`doublet` (vs `reject`) is reasonable; a very high reject rate suggests a reference/tissue mismatch — surface this to the user.
- `first_type`, `second_type`, `spot_class` are present in `adata.obs` and aligned to barcodes before proceeding to annotation.
</self_eval_criteria>

<long_running_guidance>
The RCTD run on Latch compute may take significant time. After launching, use the long-running guidance in the respective workflow doc ("safe to close this tab; reopen when complete and the agent resumes").
</long_running_guidance>
