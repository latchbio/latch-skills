<goal>
Identify cell types in each cluster.
</goal>

<rctd_gate>
**If RCTD was launched in this session, this step does not start until its labels are in `adata.obs`.**

Normally you should never arrive here with RCTD still running: `<hard_stop>` in `steps/rctd.md` stops
the track at the launch point and does not release it until the run lands. This gate is the backstop
for the two ways that can be bypassed — the user explicitly chose to work ahead in parallel, or the
session resumed (or a pod restarted) with no memory of where the stop was. In either case the rule
here is the same, and it is not negotiable the way the parallel-work choice was: annotation consumes
RCTD's labels, so it cannot run without them.

Annotating first and folding RCTD in afterwards is not equivalent: the reference-based labels are
evidence used to *derive* and validate each cluster's label, not a footnote added to a finished
annotation, and re-annotating later leaves the user with two sets of labels to reconcile.

**Establish which of three states you are in before writing any annotation code.**

1. **RCTD was never run** — Trekker data, or the user declined it at `steps/rctd.md`. Proceed
   immediately with marker-based annotation. Do not wait, do not check Latch, and do not re-pitch
   RCTD here; the marker-based path below is complete on its own.
2. **RCTD ran and its labels are merged** — `first_type` / `second_type` / `spot_class` are present in
   `adata.obs`. Proceed, starting at method step 0.
3. **RCTD was launched but its labels are not in `.obs`** — **stop and wait.** Do not extract markers,
   do not label clusters, do not open an annotation tab.

**Checking, in state 3.** The notebook is not the source of truth — the execution runs on Latch
compute, outside this pod, and a notebook with no record of it finishing is not evidence that it is
still going. Follow `<resuming>` in `wf/rctd_wf.md`: look for `<run_name>_RCTD.h5ad` under
`output_directory/<run_name>/` in Latch Data. If it is there, the run finished — go to step 3 of
`steps/rctd.md`, merge the labels, and then come back here. If it is not, the run is still going or
failed; say so, and tell the user to check the workflows executions tab. Never answer by re-running
the RCTD launch cell — that is a second execution, not a status check.

**What to say while waiting.** Say plainly that this step is blocked on RCTD, why, and what will
unblock it — and point at the resume button by tab name, since nothing in Plots can start an agent
turn on its own.

**The wait may be long, so give the cost advice with it.** RCTD is a long-running workflow, and
reaching this point means every other step is already done — so the wait here is the longest idle
stretch the session can produce, with a notebook pod billing the whole time for nothing. Repeat the
`<long_running_guidance>` advice from `wf/rctd_wf.md` rather than leaving them to sit and watch: the
workflow runs on Latch compute, independently of this notebook, so **shutting the pod down stops the
notebook compute charges and does not interrupt the run**. They restart the pod and reopen the
notebook once it finishes. Unlike the pause at `steps/rctd.md`, this shutdown is not free — see the
save note below, which is the whole reason the stop belongs at the launch point instead.

> Clustering and DEG are done, so annotation is the last step — but RCTD is still running, and its
> per-bead labels are what I cross-check the clusters against. I'd rather not label the clusters
> twice, so let's wait for it.
>
> RCTD can run for a long while, and there's nothing left for the notebook to do in the meantime, so
> you don't need to sit here paying for an idle pod: the workflow runs on Latch compute, not in this
> notebook, so you can **shut the notebook pod down now to stop the notebook compute charges** — that
> will not interrupt RCTD. You can follow its progress in the workflows executions tab. When it
> finishes, restart the pod, reopen the notebook, go to the **RCTD** tab and click **Check my RCTD
> results**, then message me — I'll merge the labels in and annotate in one pass.

**Save the working object before they shut down.** The shutdown offered at `steps/rctd.md` costs
nothing because the QC-filtered object is already on Latch. This one comes *after* normalization →
feature selection → dimensionality reduction → clustering → DEG, and none of that survives a pod
restart if it lives only in the kernel. Before the user shuts down, make sure the working AnnData —
clusters, embeddings and DEG results included — is on Latch:
either it is the viewer-bound object persisting through `sync_to` (see `steps/data_loading.md`), or
you write it out explicitly to a directory the user picks. Offer to do that in the same message, and
say which path it went to, so that on their return you reload one file instead of recomputing five
steps. If the object is not saved, say so plainly rather than implying the shutdown is free.

If the user, having been told this, would rather annotate now on markers alone, that is their call:
proceed with the marker-based method below, and note that the RCTD labels can be cross-tabulated
against these clusters once the run finishes.
</rctd_gate>

<guard>
**Start the first annotation cell with the guard.** It is the only mechanical check in this step;
everything above it is instruction that a long session can lose track of. Resolve `takara/lib` per
"Helper library usage" in `SKILL.md`, then:

```python
from takara.annotation import require_rctd_for_annotation

basis = require_rctd_for_annotation(
    adata,
    kit="seeker",                       # or "trekker" — required, and it is not guessed
    output_dir=RCTD_OUTPUT_DIR,         # omit if RCTD was never launched this session
    run_name=RCTD_RUN_NAME,
)
print(basis.basis_line)
```

Put it above the marker extraction, not beside it — the point is that nothing is computed when the
precondition fails.

**What it does, by kit.** The kit argument is load-bearing, because missing RCTD labels mean
opposite things on either side of it:

| Situation | Result |
|---|---|
| **Trekker**, no RCTD labels | Passes silently. This is the intended flow — RCTD's doublet mode assumes Seeker's 1–3 cells per bead — so there is no warning to give. |
| **Seeker**, labels merged | Passes silently. Annotate with the cross-tabulation in method step 0. |
| **Seeker**, RCTD in flight or launched-but-unmerged | Raises `RctdPending`. Nothing is computed. |
| **Seeker**, RCTD declined | Passes, and renders a warning box saying what the labels do not rest on. |
| Latch unreachable | Passes with a warning that the status could not be confirmed. It fails open — blocking a real session over a network error is worse than the failure being guarded. |

**On `RctdPending`, stop and report — do not route around it.** Do not delete the guard, do not
pass `acknowledge_pending=True` on your own initiative, and do not fall back to marker-only
annotation as if the exception were an error to work through. Tell the user annotation is blocked,
that clustering and DEG are safe, and how to resume (the **RCTD** tab, **Check my RCTD results**),
then end the turn. `acknowledge_pending=True` exists for one case only: the user has been told a run
is pending and has said they want marker-only labels now regardless.

**Always print `basis.basis_line`, and put it in the annotation summary you write in chat.** Every
time — including the ordinary Trekker and labels-merged cases where nothing is wrong. Stating the
evidence unconditionally is what makes the odd case visible without anyone having to notice it
first: a user who launched RCTD and reads "marker gene expression alone" knows immediately.

The guard is a net, not a substitute for `<hard_stop>` in `steps/rctd.md`, which is what keeps the
session out of this situation to begin with.
</guard>

<method>
0. **If RCTD labels are present** (`first_type` / `second_type` / `spot_class` in `adata.obs`, written by `steps/rctd.md`): cross-tabulate `first_type` against the Leiden cluster column to get the per-cluster cell-type composition. For each cluster, derive the **majority RCTD `first_type`** as a reference-based consensus label, and note clusters where RCTD is mixed or mostly `reject`. Use this as independent evidence alongside the marker-based interpretation below — present both, and reconcile them (agreement strengthens the label; disagreement warrants a closer look at the markers). This is complementary: marker-based annotation below remains the default and is the sole method when RCTD was not run. If RCTD was launched but these columns are absent, do not fall through to step 1 — see `<rctd_gate>` above.

1. **Extract top 20 marker genes per cluster** (not just 5 - critical markers often appear in positions 6-20)

2. **Analyze and interpret each cluster**: Consider gene function, biological role, and tissue context. Write out your reasoning. When RCTD consensus labels exist (step 0), state whether the markers corroborate them.

3. **Apply descriptive labels**:
   - Preferred: Functional description (e.g., "Proliferating cells", "Steroidogenic cells")
   - If uncertain: Description + marker (e.g., "Stromal-like (Col1a1+)")
   - **NEVER**: "Cluster X"

4. **Validation checks**:
   - All clusters have biological interpretation (no "Cluster X" labels)
   - Proportions are biologically plausible
   - Create summary table with counts and percentages
   - Generate dot plot of top markers
   - Create one violin plot per cell type, comparing its enriched markers to other cell types. 
</method>

<workflows>
</workflows>

<library>
- `takara.annotation.require_rctd_for_annotation` — the RCTD precondition check. See `<guard>` above.
- `takara.annotation.RctdPending` — raised when Seeker annotation is attempted with RCTD outstanding.
- `takara.annotation.AnnotationBasis` — what the guard returns; `.basis_line` goes in the summary.
</library>

<self_eval_criteria>
- The user was told, in chat, which tab holds the labeled embeddings, summary table, and plots
- The first annotation cell called `require_rctd_for_annotation(...)` with the correct `kit` before extracting markers, and `basis.basis_line` was stated in the annotation summary — in every session, not only when something was wrong
- For Seeker data annotated without RCTD labels, the user saw the warning explaining what the labels do not rest on. For Trekker data, no such warning was given: skipping RCTD there is the intended flow, not a shortfall
- An `RctdPending` exception was reported to the user and ended the turn — it was not worked around by deleting the guard, passing `acknowledge_pending=True` unprompted, or annotating on markers instead
- If RCTD was launched earlier in the session, annotation did not begin until `first_type` / `second_type` / `spot_class` were present in `adata.obs` — the wait was explained in chat, and the RCTD status was judged from Latch Data rather than from notebook state
- Arriving at this step with RCTD still in flight was the exception, not the norm: the track had stopped at `<hard_stop>` in `steps/rctd.md` unless the user explicitly chose to work ahead
- If RCTD was never run, this step proceeded straight to marker-based annotation with no waiting and no re-pitch of RCTD
- If the user was asked to wait for RCTD, the same message told them the run is long, that they may shut the notebook pod down to stop notebook compute charges without interrupting it, and how to pick back up — and the working AnnData (clusters, embeddings, DEG) was saved to Latch, or its unsaved state was stated, before that shutdown was suggested
</self_eval_criteria>

<new_tab_notice>
The labeled embeddings, the summary table of counts and percentages, the dot plot, and the per-type
violin plots open in a **new tab** that the notebook does not switch to. Name it in chat — see
"Telling the user where results appeared" in `SKILL.md`:

> All 14 clusters are annotated. The labeled embeddings, summary table, and marker plots are in a
> **new tab** named **Cell type annotation** — click it in the notebook to review the labels.

Put your written per-cluster reasoning in the chat message itself, not only in that tab, so the user
can read it without switching away from wherever they are.
</new_tab_notice>
