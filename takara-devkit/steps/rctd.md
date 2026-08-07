<goal>
Assign reference-based cell types to every bead using Robust Cell Type Deconvolution (RCTD), and merge the results back into the working AnnData so later annotation can use them.

**Seeker only.** Skip this step entirely for Trekker data — RCTD's doublet mode assumes ~1–3 cells per bead, which is a Seeker property. If the kit type is unknown, ask: "Was this data generated with a Seeker or Trekker kit?"

**Recommended, skippable, and separate.** For Seeker data, **always recommend RCTD**, and always run it **after QC + Filtering and before Normalization** — on the raw-count, pre-normalization AnnData. The user may decline; make skipping an explicit, easy choice rather than the default. RCTD is a separate reference-based track: it does **not** depend on normalization, feature selection, dimensionality reduction, clustering, or DEG, and those steps run unchanged whether or not RCTD is used. RCTD's per-bead labels are consumed later, at Cell Type Annotation (`steps/cell_typing.md`), to label and validate Leiden clusters — it complements, and does not replace, marker-based annotation.

The position in the order is not a preference — it is a requirement. RCTD reads raw counts, and normalization overwrites `.X`, so running it later means recovering raw counts or redoing QC. Recommend it at the point in the workflow where the object is already in the state RCTD needs.

**Division of labor.** *You* (the Agent) are responsible for finding the most appropriate reference for the user's tissue across multiple public atlases and presenting choices. The `rctd_reference_builder` workflow is a **pure converter** — give it one chosen reference (a `.h5ad`/`.rds` file or a download URL) and it returns a version-compatible spacexr `Reference` `.rds`. It does **not** search anything.
</goal>

<method>
### When to recommend
As soon as QC + Filtering completes — and **before** starting Normalization — recommend RCTD to every Seeker user. Recommend it, don't merely mention it, and state both the recommendation and the opt-out in the same message:

> "Now that filtering is done, I recommend running RCTD before we normalize. It assigns a cell type to each bead from a single-cell reference, which gives us reference-based labels to check the Leiden clusters against later. This is the right point for it — RCTD needs raw counts, and normalization overwrites them. Shall I go ahead, or would you rather skip RCTD and move straight to normalization?"

Ask this **every time** for Seeker data, even if the user has not mentioned cell typing. Do not run it for Trekker data, and do not raise it there.

**If the user declines, skip it cleanly.** Move straight to `steps/normalization.md` — no second ask, no repeated pitch, no implication that the rest of the analysis is degraded. It is not: steps 4–9 are complete on their own, and `steps/cell_typing.md` falls back to marker-based annotation. Note in passing that RCTD can still be run later from the QC-filtered object if they change their mind, and continue.

If the user agrees, proceed. RCTD needs the **QC-filtered, raw-count** AnnData (raw counts in `.X`, spatial coordinates in `.obsm`) — use it **before** normalization. If normalization has already overwritten `.X`, recover raw counts from the raw layer or re-derive from the QC-filtered object.

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

**Collect `run_name` and `output_directory` for the build in chat, in the same message that presents
the reference choice.** Do not render a picker for the output directory and then end your turn:
nothing in Plots can start an agent turn, so the user fills it in, nothing happens, and they
reasonably conclude you are stuck. This step has already produced that stall. See "Requesting files
from the user" in `SKILL.md`.

**1f. If the build fails, recover — don't stop and don't retry blindly.** A reference the workflow
cannot use is a normal outcome of picking one off the web, and recovering from it is *your* job: the
user cannot search the atlases themselves. The failed build uploads
`<run_name>_reference_FAILED.txt` to its output directory; read it, and follow `<failure_recovery>`
in `wf/rctd_reference_builder_wf.md` — it maps each `error code:` to the right recovery. In short:

1. Read the report and say, in plain language, which reference failed and why (out of memory, wrong
   cell-type column, dead download link, Seurat v5, …).
2. If it is a parameter problem (`CELL_TYPE_COLUMN_NOT_FOUND`, `CELL_TYPE_BELOW_MIN`), name the fix
   and offer to relaunch with it — the reference itself is fine.
3. Otherwise **ask the user whether you should go find a different reference**, stating the
   constraint the failure taught you (e.g. "smaller than ~300k cells", "one that ships raw counts",
   "a `.h5ad` rather than the Seurat v5 `.rds`"). On yes, return to **1b** and search again with that
   constraint applied, present candidates as in **1c**, and rebuild via **1e** under a new
   `run_name`.
4. Never carry on to Step 2 after a failed build — there is no `.rds` to deconvolve with — and never
   end the turn on a failure without both the explanation and the question.

If the user would rather not pursue a reference at all, skip RCTD cleanly per the opt-out above and
continue at `steps/normalization.md`.

### Step 2 — Run RCTD
1. Write the QC-filtered, raw-count AnnData to Latch as `.h5ad` (it must carry spatial coordinates in `.obsm["spatial"]` or `.obsm["X_spatial"]`).
2. Launch RCTD with that query and the reference `.rds` per `wf/rctd_wf.md`. Doublet mode is automatic — tell the user, and do not pass a mode parameter.

**Chain the handoff; do not re-ask.** The builder's `reference_data` path is fully determined by the
parameters you already passed it — `<output_directory>/<run_name>/<run_name>_reference.rds` — so
carry it straight into the RCTD resolve cell. Asking the user to supply or confirm it again is what
turns one handoff into several rounds of "yes, go ahead", and each of those is a chance to launch
something twice.

**One build, then one run, per reference.** Both launches go through `launch_workflow_once`
(`wf/rctd_reference_builder_wf.md`, `wf/rctd_wf.md`), so a repeated confirmation is a no-op with an
explanatory message rather than a second execution — but do not lean on that. Before you launch
either one in response to a "yes", check whether it is already running; see "Launching a workflow at
most once" in `SKILL.md`. A user who confirms twice is telling you they cannot see what is
happening, not that they want two runs.

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
- For Seeker data, RCTD was **recommended** — not merely offered — immediately after QC + Filtering and before any normalization, and the same message gave the user an explicit way to skip it.
- If the user skipped RCTD, the workflow continued straight to normalization without re-pitching it.
- The object handed to RCTD holds QC-filtered raw counts in `.X` (normalization had not yet run).
- The chosen reference's organism matches the data; its tissue, condition, and (if relevant) developmental stage are a sensible match for the sample.
- If the reference build failed, its `<run_name>_reference_FAILED.txt` was read and its cause was reported to the user in plain language — and the user was **asked** whether to find a different reference, rather than left with an unexplained failure or a blind relaunch of the same parameters.
- Reference and query share a non-zero set of genes (RCTD errors on zero overlap — the builder reports the reference gene count; sanity-check it against the query's genes before launching).
- The cell types present in the reference are plausible for the user's tissue.
- After running, the fraction of beads classified as `singlet`/`doublet` (vs `reject`) is reasonable; a very high reject rate suggests a reference/tissue mismatch — surface this to the user.
- `first_type`, `second_type`, `spot_class` are present in `adata.obs` and aligned to barcodes before proceeding to annotation.
</self_eval_criteria>

<long_running_guidance>
The RCTD run on Latch compute may take significant time. After launching, display the
`<long_running_guidance>` message from the respective workflow doc in full — including the advice
that the user may shut down the notebook pod while the workflow runs to save on compute costs,
then restart the pod and reopen the notebook when it completes.

The launch cell does not wait for the execution, so when the user returns, follow the `<resuming>`
block in `wf/rctd_wf.md`: check Latch Data for `<run_name>_RCTD.h5ad` under
`output_directory/<run_name>/` rather than judging from notebook state, then continue at Step 3
above. Never report that RCTD is still running just because the notebook has no record of it
finishing, and never answer a resume message by re-running the launch cell — that is a second
execution, not a status check.
</long_running_guidance>

<new_tab_notice>
Two tabs matter in this step, and the notebook switches to neither.

- The **launch cell and its resume button** (`wf/rctd_wf.md`) sit in their own tab. A resume button in
  an unopened tab is the same as no button at all, so when you hand off for the long run, tell the
  user which tab to come back to.
- The **`first_type` spatial/UMAP views and the `spot_class` distribution** from Step 3 open in
  another tab once results are merged.

Name both in chat as they appear — see "Telling the user where results appeared" in `SKILL.md`:

> RCTD is running on Latch compute. When it finishes, come back to the **RCTD** tab in this notebook
> and click **Check my RCTD results** — that button is in that tab, not this chat.
</new_tab_notice>
