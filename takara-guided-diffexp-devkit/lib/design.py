"""Design helpers for the grouping-confirmation cell.

Contains NO statistics. Merging widget values, checking rules, and formatting
CSV are the only things here.

The validation rules are VENDORED from deseq2_core.groups.validate_condition
because the skill is deployed by cloning into the Plots pod's .claude/skills/,
where this repo is not importable. tests/test_skill_lib.py asserts the two
implementations agree; do not edit one without the other.
"""
from __future__ import annotations

CONTROL = "control"
TREATED = "treated"
LEGAL = (CONTROL, TREATED)
MIN_REPLICATES = 2


def merge(samples, widget_values):
    """Zip sample names with the radio-group values into a condition map."""
    samples = [str(s) for s in samples]
    values = list(widget_values)
    if len(values) != len(samples):
        raise ValueError(
            f"got {len(values)} selections for {len(samples)} samples")
    return dict(zip(samples, (str(v) for v in values)))


def validate_condition(samples, condition):
    """Return human-readable rule failures; empty list means valid."""
    errors = []
    samples = [str(s) for s in samples]
    known = set(samples)

    for name in samples:
        if name not in condition:
            errors.append(f"sample {name!r} has no condition label")

    for name in condition:
        if name not in known:
            errors.append(
                f"unknown sample {name!r} is not a column in the counts table")

    for name, label in condition.items():
        if label not in LEGAL:
            errors.append(
                f"sample {name!r} has label {label!r}; must be one of {LEGAL}")

    counted = {c: 0 for c in LEGAL}
    for name in samples:
        label = condition.get(name)
        if label in counted:
            counted[label] += 1
    for label, n in counted.items():
        if n < MIN_REPLICATES:
            errors.append(
                f"group {label!r} has {n} replicate(s); DESeq2 needs at least "
                f"{MIN_REPLICATES} per group to estimate dispersion")

    return errors


def flagged(condition, nearest):
    """Samples whose nearest correlation partner is in the other group.

    A pure lookup over precomputed values -- no statistics run here. The
    nearest-neighbour identities come from similarity.json and do not depend on
    the labels, so this stays correct however the user regroups.
    """
    out = []
    for name in condition:
        near = (nearest or {}).get(name) or {}
        other = near.get("sample")
        if other and other in condition and condition[other] != condition[name]:
            out.append(name)
    return sorted(out)


def canonical_order(samples, condition):
    """Control samples first, then treated, so the contrast cannot flip.

    NOT the same as deseq2_core.counts.canonical_sample_order, despite the
    similar name. That one takes a `method` argument and deliberately returns
    the samples untouched when the grouping came from column order rather than
    sample names. Here the user has explicitly confirmed every label, so
    reordering is always correct and there is no method to consult.
    """
    controls = [s for s in samples if condition.get(s) == CONTROL]
    treated = [s for s in samples if condition.get(s) == TREATED]
    return controls + treated


def coldata_csv(ordered_samples, condition):
    rows = ["sample,condition"]
    for s in ordered_samples:
        rows.append(f"{s},{condition[s]}")
    return "\n".join(rows) + "\n"
