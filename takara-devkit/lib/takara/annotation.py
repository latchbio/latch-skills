"""The RCTD precondition for cell type annotation.

`steps/cell_typing.md` consumes RCTD's per-bead labels, so it is the one step in secondary
analysis that cannot run correctly while an RCTD deconvolution is still in flight. Every other
guard against that is prose in the step docs, and prose is checked by whatever attention the agent
has left after nine steps and a possible pod restart -- which is exactly the state a real Seeker
test session reached before annotating all its clusters with RCTD still running.

That failure is silent. Marker-based annotation succeeds on its own, so the notebook shows a
confident, complete, plausible-looking set of labels and nothing anywhere says the reference
evidence was missing. This module makes it loud instead: called at the top of the first annotation
cell, it raises before any markers are extracted.

**It is kit-aware, because "no RCTD labels" means opposite things per kit.**

- **Trekker** -- RCTD is not applicable at all (its doublet mode assumes the ~1-3 cells per bead
  that is a Seeker property). Annotating from markers alone is the intended, correct flow, so this
  passes in silence. No warning, ever: a caveat here would be noise that teaches the user to
  ignore the real one.
- **Seeker** -- RCTD is recommended for every dataset. Missing labels are therefore either a
  mistake in progress (a run is still going) or a deliberate choice whose downside the user should
  see stated once at the point it takes effect.

Nothing here second-guesses a decision the user already made. Declining RCTD is a supported flow,
and `steps/rctd.md` is explicit that a session which skips it is not degraded; the Seeker warning
below says what was not used, not that the analysis is bad.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from takara.launch import ExecutionQueryError, find_live_executions, notice, read_claim

# The workflow name to look for. `find_live_executions` matches loosely on the last dotted
# segment, which is what makes this work across the three spellings RCTD is registered under.
RCTD_WF_NAME = "rctd_wf"

# The claim `steps/rctd.md` writes when it launches, via `launch_workflow_once(key_prefix="rctd")`.
RCTD_KEY_PREFIX = "rctd"

# Written into `.obs` by step 3 of `steps/rctd.md`. `first_type` is the one annotation actually
# cross-tabulates; the others travel with it.
RCTD_OBS_COLUMNS = ("first_type", "second_type", "spot_class")


class Kit(str, Enum):
    """Seeker vs Trekker -- the assay, which is what decides whether RCTD applies.

    Not to be confused with `takara.background_removal.TileType`, which is the capture-area size
    (`10x10` / `3x3`) and says nothing about the assay. Both get called "the kit type" in
    conversation; that collision is why the other one is named for the tile.
    """

    SEEKER = "seeker"
    TREKKER = "trekker"


class RctdPending(RuntimeError):
    """Annotation was attempted while an RCTD run was in flight or unmerged.

    Raised rather than warned: the point is that no labels get produced. A warning would scroll
    past and leave a finished annotation on screen, which is the outcome being prevented.
    """


@dataclass
class AnnotationBasis:
    """What evidence this annotation is entitled to use. Returned when the gate passes.

    `basis_line` is the sentence to include in the annotation summary. State it every time --
    unconditionally, not only when something is wrong. An agent that must always name its evidence
    has no "notice the problem" step left to fail, and the user sees `markers alone` in a session
    where they launched RCTD without anyone having had to diagnose it.
    """

    kit: Kit
    rctd_used: bool
    rctd_applicable: bool
    basis_line: str
    warned: bool = False
    check_error: Optional[str] = None


def _coerce_kit(kit: Any) -> Kit:
    if isinstance(kit, Kit):
        return kit
    text = str(kit or "").strip().lower()
    for member in Kit:
        if text == member.value or member.value in text:
            return member
    raise ValueError(
        "kit must be 'seeker' or 'trekker' -- the RCTD precondition differs entirely between "
        f"them, so this gate will not guess (got {kit!r}). Establish the kit type first; "
        "`steps/rctd.md` says to ask the user outright when it is unknown."
    )


def _has_rctd_labels(adata: Any) -> bool:
    if adata is None:
        return False
    try:
        return "first_type" in adata.obs.columns
    except Exception:
        return False


def require_rctd_for_annotation(
    adata: Any = None,
    *,
    kit: Any,
    output_dir: Any = None,
    run_name: Optional[str] = None,
    acknowledge_pending: bool = False,
) -> AnnotationBasis:
    """Check the RCTD precondition before annotating. Call this before extracting markers.

    Args:
        adata: the working AnnData. Checked first, so the ordinary success path costs no network.
        kit: `"seeker"` or `"trekker"` (or a `Kit`). Required -- see `_coerce_kit`.
        output_dir / run_name: the RCTD output directory and run name, if RCTD was launched this
            session. Only used to find the launch claim, i.e. to catch a run that finished but was
            never merged. Omitting them weakens that one branch and nothing else.
        acknowledge_pending: proceed despite a pending run. Set this **only** after telling the
            user a run is in flight and hearing that they want marker-only labels now anyway.

    Returns:
        `AnnotationBasis` -- put `basis_line` in the annotation summary.

    Raises:
        `RctdPending` if Seeker data has an RCTD run in flight, or one whose results were never
        merged, unless `acknowledge_pending`.
        `ValueError` if `kit` is missing or unrecognized.
    """
    kit = _coerce_kit(kit)

    # --- Trekker: RCTD does not apply. Silent pass is the whole behavior. -------------------
    if kit is Kit.TREKKER:
        return AnnotationBasis(
            kit=kit,
            rctd_used=False,
            rctd_applicable=False,
            basis_line=(
                "Cell types were annotated from marker gene expression. RCTD was not used, which "
                "is expected for Trekker data -- its doublet mode assumes the 1-3 cells per bead "
                "that is a Seeker property."
            ),
        )

    # --- Seeker, labels already merged: the intended path. ----------------------------------
    if _has_rctd_labels(adata):
        return AnnotationBasis(
            kit=kit,
            rctd_used=True,
            rctd_applicable=True,
            basis_line=(
                "Cell types were annotated from marker gene expression, cross-checked against "
                "RCTD reference-based labels (`first_type`) per cluster."
            ),
        )

    # --- Seeker, no labels: mistake in progress, or a deliberate skip? -----------------------
    # Ask Latch, never the notebook. The execution runs outside this pod, so kernel state cannot
    # answer, and a pod restart is exactly when this question gets asked.
    check_error: Optional[str] = None
    pending_detail: Optional[str] = None
    try:
        live = find_live_executions(RCTD_WF_NAME)
        if live:
            pending_detail = "; ".join(e.describe() for e in live[:3])
    except ExecutionQueryError as e:
        # Fail open. Blocking a legitimate session because the API was unreachable is a worse
        # failure than the one this guards -- and `steps/rctd.md` already tells the agent how to
        # check by hand. Surface the uncertainty rather than swallowing it.
        check_error = str(e)

    # A run can also be finished-but-unmerged: nothing live, yet a claim file records the launch.
    # Without output_dir this branch simply cannot run; that is a weaker gate, not a broken one.
    if pending_detail is None and check_error is None and output_dir is not None:
        claim = read_claim(output_dir, run_name, RCTD_KEY_PREFIX)
        if claim:
            pending_detail = (
                f"a launch recorded under {run_name or output_dir} whose labels are not in "
                "`adata.obs` -- the run may have finished without step 3 (merge) being done"
            )

    if pending_detail is not None and not acknowledge_pending:
        raise RctdPending(
            "Cell type annotation is blocked: this is Seeker data with RCTD "
            f"outstanding ({pending_detail}).\n\n"
            "Annotation cross-tabulates RCTD's per-bead labels against the Leiden clusters, so "
            "running it now would produce labels derived without evidence that is about to "
            "arrive, and they would have to be redone and reconciled.\n\n"
            "Do not re-run the RCTD launch cell to check on it -- that starts a second "
            "execution. Check Latch Data for `<run_name>_RCTD.h5ad`, or use the 'Check my RCTD "
            "results' button in the RCTD tab. When it is there, merge the labels (step 3 of "
            "`steps/rctd.md`) and re-run this cell.\n\n"
            "If the user has been told this and wants marker-only labels now regardless, pass "
            "acknowledge_pending=True."
        )

    if pending_detail is not None:  # acknowledged: proceed, but on the record
        notice(
            "**Annotating without RCTD, by request.** An RCTD run is still outstanding "
            f"({pending_detail}). These labels come from marker genes alone and will not reflect "
            "it; once the run lands, its `first_type` labels can be cross-tabulated against these "
            "clusters.",
            key="cell_typing_rctd_acknowledged",
            box="warning",
        )
        return AnnotationBasis(
            kit=kit,
            rctd_used=False,
            rctd_applicable=True,
            basis_line=(
                "Cell types were annotated from marker gene expression alone. An RCTD run was "
                "still outstanding and its reference-based labels were not used."
            ),
            warned=True,
            check_error=check_error,
        )

    if check_error is not None:
        # Say only what is true: the check failed, so whether a run is in flight is unknown. The
        # branch below would claim RCTD "was not run", which this path has no way to establish.
        notice(
            "**Could not confirm RCTD status.** Latch could not be reached to check for a running "
            f"RCTD execution ({check_error}), so this gate let annotation proceed rather than "
            "block on a network failure. This is Seeker data and there are no RCTD labels on the "
            "object, so if a run is in flight these labels will not reflect it -- check the "
            "workflows executions tab, or Latch Data for `<run_name>_RCTD.h5ad`, before relying "
            "on them.",
            key="cell_typing_rctd_check_degraded",
            box="warning",
        )
        return AnnotationBasis(
            kit=kit,
            rctd_used=False,
            rctd_applicable=True,
            basis_line=(
                "Cell types were annotated from marker gene expression alone. No RCTD labels were "
                "present on the object, and RCTD's run status could not be confirmed."
            ),
            warned=True,
            check_error=check_error,
        )

    # Seeker, nothing pending: RCTD was declined (or never raised). Supported -- state the
    # trade-off once, here, where it takes effect. Not a re-pitch: there is nothing to launch
    # in time for this annotation, and `steps/rctd.md` forbids re-asking.
    notice(
        "**Annotating without RCTD labels.** This is Seeker data, where RCTD is recommended: it assigns "
        "each bead a cell type from a single-cell reference, giving an independent check on the "
        "marker-based labels below and catching clusters that are mixed or ambiguous. Without it "
        "these labels rest on marker interpretation alone -- a valid and standard approach, but a "
        "single line of evidence. RCTD can still be run later from the QC-filtered object, and its "
        "labels cross-tabulated against these clusters.",
        key="cell_typing_no_rctd_seeker",
        box="warning",
    )
    return AnnotationBasis(
        kit=kit,
        rctd_used=False,
        rctd_applicable=True,
        basis_line=(
            "Cell types were annotated from marker gene expression alone. No RCTD labels were "
            "present for this Seeker dataset, so there is no reference-based cross-check on "
            "these labels."
        ),
        warned=True,
        check_error=check_error,
    )


__all__ = [
    "AnnotationBasis",
    "Kit",
    "RctdPending",
    "require_rctd_for_annotation",
]
