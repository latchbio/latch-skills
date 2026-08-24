"""Rendering for the guided workflow. Displays precomputed numbers only.

Palette: slots 1-2 of the reference categorical palette, validated with
scripts/validate_palette.js --pairs all in both modes (all six checks PASS;
worst CVD dE 24.7 light / 26.8 dark, normal-vision 33.6 / 31.8). Do not
substitute colours without re-running the validator.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

LIGHT = {"control": "#2a78d6", "treated": "#eb6834",
         "surface": "#fcfcfb", "ink": "#1a1a19", "muted": "#6b6a63"}
DARK = {"control": "#3987e5", "treated": "#d95926",
        "surface": "#1a1a19", "ink": "#ffffff", "muted": "#c3c2b7"}


def similarity_figure(similarity, condition, flagged_samples, theme=LIGHT):
    """Sample-similarity map, coloured by the CURRENT grouping selection.

    Deliberately not a PCA. The authoritative variance-stabilised PCA belongs
    to the QC stage; two plots that look like they answer the same question can
    appear to contradict each other, and a correlation-similarity map answers a
    different one.
    """
    fig, ax = plt.subplots(figsize=(6.0, 5.0), facecolor=theme["surface"])
    ax.set_facecolor(theme["surface"])

    seen = set()
    for point in similarity["coords"]:
        name = point["sample"]
        label = condition.get(name, "control")
        colour = theme.get(label, theme["control"])
        is_flagged = name in flagged_samples
        ax.scatter(
            point["x"], point["y"],
            s=180, c=colour, zorder=3,
            # A 2px surface ring keeps overlapping markers separable; a dark
            # ring is the flagged state -- secondary encoding, never colour
            # alone, because colour already carries group identity.
            edgecolors=theme["ink"] if is_flagged else theme["surface"],
            linewidths=2.5 if is_flagged else 2.0,
            label=label if label not in seen else None)
        seen.add(label)
        ax.annotate(
            f"{name} ⚠" if is_flagged else name,
            (point["x"], point["y"]), xytext=(0, 12),
            textcoords="offset points", ha="center", fontsize=9,
            color=theme["ink"], zorder=4)

    ax.set_xlabel("Similarity axis 1", color=theme["muted"], fontsize=10)
    ax.set_ylabel("Similarity axis 2", color=theme["muted"], fontsize=10)
    ax.set_title("Sample similarity (rank correlation of log-CPM)",
                 color=theme["ink"], fontsize=12, pad=12)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(theme["muted"])
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=theme["muted"], labelsize=9)

    legend = ax.legend(loc="best", frameon=False, fontsize=10)
    for text in legend.get_texts():
        text.set_color(theme["ink"])

    fig.tight_layout()
    return fig


def design_table(samples, condition, nearest, flagged_samples):
    """The proposed design as a table, with the mislabel warning column."""
    rows = []
    for name in samples:
        near = (nearest or {}).get(name) or {}
        rows.append({
            "sample": name,
            "condition": condition.get(name, ""),
            "closest sample": near.get("sample", ""),
            "correlation": near.get("correlation", ""),
            "": "⚠ closest match is in the other group"
                 if name in flagged_samples else "",
        })
    return pd.DataFrame(rows)
