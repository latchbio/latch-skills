"""
Takara Devkit — Process Flow Diagram
Renders to process_flow.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np

# ── Canvas ─────────────────────────────────────────────────────────────────
FIG_W, FIG_H = 30, 38
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
fig.patch.set_facecolor("#0F1117")
ax.set_facecolor("#0F1117")

# ── Palette ────────────────────────────────────────────────────────────────
C = {
    "bg":         "#0F1117",
    "decision":   "#2D3748",
    "decision_bd":"#63B3ED",
    "wf":         "#1A4A7A",
    "wf_bd":      "#4299E1",
    "step":       "#1A4731",
    "step_bd":    "#48BB78",
    "seeker":     "#44337A",
    "seeker_bd":  "#9F7AEA",
    "preprocess": "#7B341E",
    "preprocess_bd":"#F6AD55",
    "output":     "#1D4044",
    "output_bd":  "#4FD1C5",
    "terminal":   "#1A202C",
    "terminal_bd":"#A0AEC0",
    "text":       "#F7FAFC",
    "subtext":    "#A0AEC0",
    "arrow":      "#718096",
    "arrow_yes":  "#48BB78",
    "arrow_no":   "#FC8181",
    "divider":    "#2D3748",
}

# ── Drawing helpers ─────────────────────────────────────────────────────────
def box(ax, x, y, w, h, label, sublabel=None,
        fc=C["wf"], ec=C["wf_bd"], radius=0.25, fontsize=9.5):
    patch = FancyBboxPatch((x - w/2, y - h/2), w, h,
                           boxstyle=f"round,pad=0,rounding_size={radius}",
                           fc=fc, ec=ec, lw=1.6, zorder=3)
    ax.add_patch(patch)
    if sublabel:
        ax.text(x, y + h*0.13, label, ha="center", va="center",
                color=C["text"], fontsize=fontsize, fontweight="bold", zorder=4,
                fontfamily="monospace")
        ax.text(x, y - h*0.22, sublabel, ha="center", va="center",
                color=C["subtext"], fontsize=fontsize - 1.5, zorder=4,
                fontstyle="italic")
    else:
        ax.text(x, y, label, ha="center", va="center",
                color=C["text"], fontsize=fontsize, fontweight="bold", zorder=4,
                fontfamily="monospace")

def diamond(ax, x, y, w, h, label, sublabel=None,
            fc=C["decision"], ec=C["decision_bd"], fontsize=9):
    dx, dy = w/2, h/2
    pts = np.array([[x, y+dy],[x+dx, y],[x, y-dy],[x-dx, y]])
    patch = plt.Polygon(pts, closed=True, fc=fc, ec=ec, lw=1.6, zorder=3)
    ax.add_patch(patch)
    if sublabel:
        ax.text(x, y + dy*0.25, label, ha="center", va="center",
                color=C["text"], fontsize=fontsize, fontweight="bold", zorder=4)
        ax.text(x, y - dy*0.35, sublabel, ha="center", va="center",
                color=C["subtext"], fontsize=fontsize-1.5, zorder=4, fontstyle="italic")
    else:
        ax.text(x, y, label, ha="center", va="center",
                color=C["text"], fontsize=fontsize, fontweight="bold", zorder=4)

def stadium(ax, x, y, w, h, label,
            fc=C["terminal"], ec=C["terminal_bd"], fontsize=9.5):
    patch = FancyBboxPatch((x - w/2, y - h/2), w, h,
                           boxstyle=f"round,pad=0,rounding_size={h/2}",
                           fc=fc, ec=ec, lw=1.8, zorder=3)
    ax.add_patch(patch)
    ax.text(x, y, label, ha="center", va="center",
            color=C["text"], fontsize=fontsize, fontweight="bold", zorder=4)

def parallelogram(ax, x, y, w, h, label,
                  fc=C["output"], ec=C["output_bd"], fontsize=9):
    skew = 0.18
    pts = np.array([
        [x - w/2 + skew, y + h/2],
        [x + w/2 + skew, y + h/2],
        [x + w/2 - skew, y - h/2],
        [x - w/2 - skew, y - h/2],
    ])
    patch = plt.Polygon(pts, closed=True, fc=fc, ec=ec, lw=1.6, zorder=3)
    ax.add_patch(patch)
    ax.text(x, y, label, ha="center", va="center",
            color=C["text"], fontsize=fontsize, fontweight="bold", zorder=4,
            fontfamily="monospace")

def arrow(ax, x1, y1, x2, y2, label="", color=C["arrow"], lw=1.4,
          connectionstyle="arc3,rad=0.0"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                connectionstyle=connectionstyle),
                zorder=2)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx + 0.12, my, label, color=color, fontsize=8,
                ha="left", va="center", zorder=5,
                bbox=dict(fc=C["bg"], ec="none", pad=1))

def section_label(ax, x, y, text):
    ax.text(x, y, text, color="#63B3ED", fontsize=11, fontweight="bold",
            ha="left", va="center", zorder=5,
            bbox=dict(fc="#1A2744", ec="#2B6CB0", pad=4, boxstyle="round,pad=0.3"))

# ═══════════════════════════════════════════════════════════════════════════
# LAYOUT  (y counts DOWN from top of figure; matplotlib y goes UP)
# We'll work in "figure units" 0-38, y=38 is top.
# ═══════════════════════════════════════════════════════════════════════════

TOP = 37.5   # start near top

# ── 0. Title ────────────────────────────────────────────────────────────────
ax.text(FIG_W/2, TOP, "Takara Devkit — Agent Process Flow",
        ha="center", va="top", color=C["text"],
        fontsize=17, fontweight="bold")
ax.text(FIG_W/2, TOP - 0.65,
        "Pre-analysis questions · Primary Analysis · Secondary Analysis",
        ha="center", va="top", color=C["subtext"], fontsize=10.5)

# ── 1. Entry ────────────────────────────────────────────────────────────────
EY = 36.0
stadium(ax, 13, EY, 3.2, 0.7, "User Begins")

# Pre-analysis question diamond
PAQ_Y = 34.7
diamond(ax, 13, PAQ_Y, 5.2, 1.4,
        "What data do you have?", "Pre-analysis question")
arrow(ax, 13, EY - 0.35, 13, PAQ_Y + 0.7)

# ── 2. Section divider ──────────────────────────────────────────────────────
DIV1 = 33.6
ax.axhline(DIV1, xmin=0.02, xmax=0.98, color=C["divider"], lw=0.8, ls="--")
section_label(ax, 0.6, DIV1 + 0.35, "PRIMARY ANALYSIS")

# Branches from PAQ
#  Left → Seeker  (x≈6)   Right → Trekker (x≈20)
#  Down-right → H5AD direct entry (x≈13, lower)

KIT_Y = 32.6
# "Raw FastQ" left arm to KIT diamond
arrow(ax, 13 - 2.6, PAQ_Y, 7.5, PAQ_Y, color=C["arrow"])
arrow(ax, 7.5, PAQ_Y, 7.5, KIT_Y + 0.7, color=C["arrow"])
ax.text(9.2, PAQ_Y + 0.15, "Raw FastQ files", color=C["arrow_yes"],
        fontsize=8.5, ha="center", va="bottom")

# "H5AD" right arm → Multiple H5AD decision → secondary entry
H5AD_DIRECT_Y = 19.5   # secondary entry y
H5AD_RIGHT_X  = 21.5   # x anchor for the H5AD branch
H5AD_MERGE_X  = 26.5   # x for the h5ad_merger_wf box (same-sample path)

# Arrow from PAQ right to branch point
arrow(ax, 13 + 2.6, PAQ_Y, H5AD_RIGHT_X, PAQ_Y, color=C["arrow"])
ax.text(H5AD_RIGHT_X + 0.2, PAQ_Y - 0.3, "Already have\nH5AD file(s)", color=C["arrow_no"],
        fontsize=8, ha="left", va="top")

# "Multiple H5AD files?" decision diamond
MULTI_Y = 32.5
arrow(ax, H5AD_RIGHT_X, PAQ_Y - 0.0, H5AD_RIGHT_X, MULTI_Y + 0.68, color=C["arrow"])
diamond(ax, H5AD_RIGHT_X, MULTI_Y, 5.0, 1.35, "Multiple H5AD\nfiles?")

# ── "No / distinct samples" path: straight down to SEC_ENTRY ────────────────
arrow(ax, H5AD_RIGHT_X, MULTI_Y - 0.68, H5AD_RIGHT_X, H5AD_DIRECT_Y,
      color=C["arrow_no"], label="No — single file\nor distinct samples")

# ── "Yes — same sample (tile stitching)" path: right → merger box → down ────
arrow(ax, H5AD_RIGHT_X + 2.5, MULTI_Y, H5AD_MERGE_X, MULTI_Y,
      color=C["wf_bd"])
ax.text(H5AD_RIGHT_X + 2.6, MULTI_Y + 0.12,
        "Yes — same sample\n(tile stitching)",
        color=C["wf_bd"], fontsize=7.5, ha="left", va="bottom")
arrow(ax, H5AD_MERGE_X, MULTI_Y - 0.68, H5AD_MERGE_X, 30.65, color=C["wf_bd"])

H5AD_MERGE_BOX_Y = 30.2
box(ax, H5AD_MERGE_X, H5AD_MERGE_BOX_Y, 5.0, 0.65,
    "h5ad_merger_wf", "Merge spatial tiles → H5AD",
    fc=C["wf"], ec=C["wf_bd"])

# From merger box down to H5AD_DIRECT_Y, then left to join main path
arrow(ax, H5AD_MERGE_X, H5AD_MERGE_BOX_Y - 0.32, H5AD_MERGE_X, H5AD_DIRECT_Y,
      color=C["arrow"])
arrow(ax, H5AD_MERGE_X, H5AD_DIRECT_Y, H5AD_RIGHT_X, H5AD_DIRECT_Y,
      color=C["arrow"])

# Kit type diamond
diamond(ax, 7.5, KIT_Y, 4.2, 1.3, "Kit type?")
arrow(ax, 7.5, PAQ_Y - 0.7, 7.5, KIT_Y + 0.65)

# ── 2a. SEEKER PATH  (x ≈ 3.5) ─────────────────────────────────────────────
SK_X = 3.5
SK_REF_Y = 31.0

arrow(ax, 7.5 - 2.1, KIT_Y, SK_X, KIT_Y, color=C["seeker_bd"])
arrow(ax, SK_X, KIT_Y, SK_X, SK_REF_Y + 0.35, color=C["seeker_bd"])
ax.text(5.2, KIT_Y + 0.15, "Seeker", color=C["seeker_bd"],
        fontsize=8.5, ha="center", va="bottom", fontweight="bold")

# Genome selection
box(ax, SK_X, SK_REF_Y, 4.6, 0.65,
    "seeker_pipeline_wf",
    "Collect genome + params",
    fc=C["seeker"], ec=C["seeker_bd"])

SK_LANES_Y = 29.9
diamond(ax, SK_X, SK_LANES_Y, 3.8, 1.1, "Multiple\nlanes?")
arrow(ax, SK_X, SK_REF_Y - 0.32, SK_X, SK_LANES_Y + 0.55)

SK_CONCAT_Y = 28.65
box(ax, SK_X - 1.8, SK_CONCAT_Y, 3.2, 0.62,
    "fastq_concatenator_wf", "Merge FASTQ lanes",
    fc=C["preprocess"], ec=C["preprocess_bd"], fontsize=8.5)
arrow(ax, SK_X - 0.9, SK_LANES_Y - 0.55, SK_X - 1.8, SK_CONCAT_Y + 0.31,
      label="Yes", color=C["arrow_yes"],
      connectionstyle="arc3,rad=0.0")

SK_WF_Y = 27.5
box(ax, SK_X, SK_WF_Y, 4.6, 0.65,
    "seeker_pipeline_wf",
    "Reads → Counts",
    fc=C["wf"], ec=C["wf_bd"])
arrow(ax, SK_X - 1.8, SK_CONCAT_Y - 0.31, SK_X - 1.8, SK_WF_Y,
      connectionstyle="arc3,rad=0.0")
arrow(ax, SK_X - 1.8, SK_WF_Y, SK_X - 2.3, SK_WF_Y,
      connectionstyle="arc3,rad=0.0")
arrow(ax, SK_X - 2.3, SK_WF_Y, SK_X - 2.3, SK_LANES_Y - 0.55,
      connectionstyle="arc3,rad=0.0")
# No lane arrow directly to wf
arrow(ax, SK_X + 0.9, SK_LANES_Y - 0.55, SK_X, SK_WF_Y + 0.32,
      label="No", color=C["arrow_no"])

SK_OUT_Y = 26.35
parallelogram(ax, SK_X, SK_OUT_Y, 4.0, 0.58, "H5AD + QC Report")
arrow(ax, SK_X, SK_WF_Y - 0.32, SK_X, SK_OUT_Y + 0.29)

SK_VIEW_Y = 25.25
box(ax, SK_X, SK_VIEW_Y, 4.0, 0.62,
    "view_report", "Inspect QC metrics",
    fc=C["step"], ec=C["step_bd"])
arrow(ax, SK_X, SK_OUT_Y - 0.29, SK_X, SK_VIEW_Y + 0.31)

# ── 2b. TREKKER PATH  (x ≈ 13) ─────────────────────────────────────────────
TK_X = 13.0

arrow(ax, 7.5 + 2.1, KIT_Y, TK_X, KIT_Y, color=C["wf_bd"])
arrow(ax, TK_X, KIT_Y, TK_X, 31.65, color=C["wf_bd"])
ax.text(11.0, KIT_Y + 0.15, "Trekker", color=C["wf_bd"],
        fontsize=8.5, ha="center", va="bottom", fontweight="bold")

TK_PLAT_Y = 31.1
diamond(ax, TK_X, TK_PLAT_Y, 5.0, 1.3, "Single-cell platform?")

# Standard platforms arrow (straight down)
TK_RXNS_Y = 29.1
arrow(ax, TK_X, TK_PLAT_Y - 0.65, TK_X, TK_RXNS_Y + 0.62,
      label="Standard\nplatforms", color=C["arrow_yes"])

# Preprocessing branches (fan out left)
PP_Y = 29.9
# FX/FLEX
FX_X = 8.5
box(ax, FX_X, PP_Y, 3.8, 0.62,
    "trekker_fxflex_demux_wf",
    "Barcode demux 16-slot",
    fc=C["preprocess"], ec=C["preprocess_bd"], fontsize=8)
arrow(ax, TK_X - 1.8, TK_PLAT_Y - 0.65, FX_X + 0.3, PP_Y + 0.31,
      label="FX/FLEX", color=C["preprocess_bd"],
      connectionstyle="arc3,rad=0.2")
arrow(ax, FX_X, PP_Y - 0.31, FX_X, TK_RXNS_Y,
      connectionstyle="arc3,rad=0.0")
arrow(ax, FX_X, TK_RXNS_Y, TK_X - 2.5, TK_RXNS_Y,
      connectionstyle="arc3,rad=0.0")

# U/PIP
UP_X = 17.5
box(ax, UP_X, PP_Y, 3.8, 0.62,
    "trekker_upip_preprocess_wf",
    "PIPseq format conversion",
    fc=C["preprocess"], ec=C["preprocess_bd"], fontsize=8)
arrow(ax, TK_X + 1.2, TK_PLAT_Y - 0.65, UP_X - 0.2, PP_Y + 0.31,
      label="U/PIP", color=C["preprocess_bd"],
      connectionstyle="arc3,rad=-0.2")
arrow(ax, UP_X, PP_Y - 0.31, UP_X, TK_RXNS_Y,
      connectionstyle="arc3,rad=0.0")
arrow(ax, UP_X, TK_RXNS_Y, TK_X + 2.5, TK_RXNS_Y,
      connectionstyle="arc3,rad=0.0")

# Q/P
QP_X = 20.5
box(ax, QP_X, PP_Y - 0.9, 3.5, 0.62,
    "trekker_qp_demux_wf",
    "Parse Evercode demux",
    fc=C["preprocess"], ec=C["preprocess_bd"], fontsize=8)
arrow(ax, TK_X + 2.5, TK_PLAT_Y - 0.65, QP_X, PP_Y - 0.58,
      label="Q/P", color=C["preprocess_bd"],
      connectionstyle="arc3,rad=-0.3")
arrow(ax, QP_X, PP_Y - 1.21, QP_X, TK_RXNS_Y,
      connectionstyle="arc3,rad=0.0")
arrow(ax, QP_X, TK_RXNS_Y, TK_X + 2.5, TK_RXNS_Y,
      connectionstyle="arc3,rad=0.0")

# Multiple reactions diamond
diamond(ax, TK_X, TK_RXNS_Y, 4.6, 1.2, "Multiple\nreactions?")

TK_LANES_Y = 27.6
# Yes arm: annotate, then drop to lanes
arrow(ax, TK_X - 1.1, TK_RXNS_Y - 0.6, TK_X - 3.0, TK_RXNS_Y - 0.6,
      color=C["arrow_yes"], connectionstyle="arc3,rad=0.0")
ax.text(TK_X - 2.0, TK_RXNS_Y - 0.44, "Yes", color=C["arrow_yes"],
        fontsize=8, ha="center")
ax.text(TK_X - 3.8, TK_RXNS_Y - 0.6,
        "Plan one run\nper reaction",
        color=C["subtext"], fontsize=7.5, ha="center", va="center",
        bbox=dict(fc="#1A2030", ec=C["divider"], pad=3, boxstyle="round,pad=0.3"))
arrow(ax, TK_X - 3.0, TK_RXNS_Y - 0.6, TK_X - 3.0, TK_LANES_Y + 0.6,
      color=C["arrow_yes"], connectionstyle="arc3,rad=0.0")
arrow(ax, TK_X - 3.0, TK_LANES_Y + 0.6, TK_X - 2.3, TK_LANES_Y + 0.6,
      color=C["arrow_yes"], connectionstyle="arc3,rad=0.0")

# No arm straight down
arrow(ax, TK_X, TK_RXNS_Y - 0.6, TK_X, TK_LANES_Y + 0.6,
      label="No", color=C["arrow_no"])

diamond(ax, TK_X, TK_LANES_Y, 4.2, 1.1, "Multiple\nlanes?")

TK_CONCAT_Y = 26.35
box(ax, TK_X - 1.8, TK_CONCAT_Y, 3.2, 0.62,
    "fastq_concatenator_wf", "Merge FASTQ lanes",
    fc=C["preprocess"], ec=C["preprocess_bd"], fontsize=8.5)
arrow(ax, TK_X - 0.9, TK_LANES_Y - 0.55, TK_X - 1.8, TK_CONCAT_Y + 0.31,
      label="Yes", color=C["arrow_yes"],
      connectionstyle="arc3,rad=0.0")

TK_WF_Y = 25.2
box(ax, TK_X, TK_WF_Y, 4.6, 0.65,
    "trekker_pipeline_wf",
    "Reads → Counts",
    fc=C["wf"], ec=C["wf_bd"])
arrow(ax, TK_X - 1.8, TK_CONCAT_Y - 0.31, TK_X - 1.8, TK_WF_Y,
      connectionstyle="arc3,rad=0.0")
arrow(ax, TK_X - 1.8, TK_WF_Y, TK_X - 2.3, TK_WF_Y)
arrow(ax, TK_X - 2.3, TK_WF_Y, TK_X - 2.3, TK_LANES_Y - 0.55)

arrow(ax, TK_X + 0.9, TK_LANES_Y - 0.55, TK_X, TK_WF_Y + 0.32,
      label="No", color=C["arrow_no"])

# Repeat loop for multiple reactions
TK_MERGE_Q_Y = 24.0
diamond(ax, TK_X, TK_MERGE_Q_Y, 4.8, 1.15,
        "All reactions\ncomplete?")
arrow(ax, TK_X, TK_WF_Y - 0.32, TK_X, TK_MERGE_Q_Y + 0.57)

# Loop back: repeat pipeline
ax.annotate("", xy=(TK_X + 2.4, TK_WF_Y),
            xytext=(TK_X + 2.4, TK_MERGE_Q_Y - 0.57),
            arrowprops=dict(arrowstyle="-|>", color=C["arrow_yes"],
                            lw=1.3, connectionstyle="arc3,rad=0.0"))
ax.text(TK_X + 3.1, (TK_WF_Y + TK_MERGE_Q_Y)/2,
        "No — run next\nreaction", color=C["arrow_yes"],
        fontsize=7.5, ha="left", va="center")

TK_MERGE_Y = 22.8
box(ax, TK_X, TK_MERGE_Y, 4.4, 0.65,
    "trekker_merger_wf", "Merge reaction outputs",
    fc=C["wf"], ec=C["wf_bd"])
arrow(ax, TK_X, TK_MERGE_Q_Y - 0.57, TK_X, TK_MERGE_Y + 0.32,
      label="Yes — merge", color=C["arrow_no"])

TK_OUT_Y = 21.7
parallelogram(ax, TK_X, TK_OUT_Y, 4.0, 0.58, "H5AD + QC Report")
arrow(ax, TK_X, TK_MERGE_Y - 0.32, TK_X, TK_OUT_Y + 0.29)

TK_VIEW_Y = 20.6
box(ax, TK_X, TK_VIEW_Y, 4.0, 0.62,
    "view_report", "Inspect QC metrics",
    fc=C["step"], ec=C["step_bd"])
arrow(ax, TK_X, TK_OUT_Y - 0.29, TK_X, TK_VIEW_Y + 0.31)

# ── 3. Convergence → Secondary Analysis entry ───────────────────────────────
DIV2 = 19.1
ax.axhline(DIV2, xmin=0.02, xmax=0.98, color=C["divider"], lw=0.8, ls="--")
section_label(ax, 0.6, DIV2 + 0.38, "SECONDARY ANALYSIS")

SEC_X = 13.0
SEC_ENTRY_Y = 18.55

# Arrow from Seeker view_report
arrow(ax, SK_X, SK_VIEW_Y - 0.31, SK_X, SEC_ENTRY_Y,
      connectionstyle="arc3,rad=0.0")
arrow(ax, SK_X, SEC_ENTRY_Y, SEC_X - 1.6, SEC_ENTRY_Y)

# Arrow from Trekker view_report
arrow(ax, TK_X, TK_VIEW_Y - 0.31, TK_X, SEC_ENTRY_Y,
      connectionstyle="arc3,rad=0.0")
arrow(ax, TK_X, SEC_ENTRY_Y, SEC_X + 1.6, SEC_ENTRY_Y)

# Arrow from H5AD branch (right side) into secondary analysis entry
arrow(ax, H5AD_RIGHT_X, H5AD_DIRECT_Y, SEC_X + 3.2, SEC_ENTRY_Y,
      connectionstyle="arc3,rad=0.0")

box(ax, SEC_X, SEC_ENTRY_Y, 5.5, 0.68,
    "Secondary Analysis Entry",
    fc="#1A2744", ec="#63B3ED", fontsize=10)

# ── 4. Secondary analysis steps (centered, stacked) ─────────────────────────
SA_X = SEC_X
SA_W  = 5.2
SA_H  = 0.65
SA_GAP = 1.1

def sa_step(y, name, sub, fc, ec):
    box(ax, SA_X, y, SA_W, SA_H, name, sub, fc=fc, ec=ec)

LOAD_Y = SEC_ENTRY_Y - 1.1
sa_step(LOAD_Y, "data_loading", "Load H5AD into notebook",
        C["step"], C["step_bd"])
arrow(ax, SA_X, SEC_ENTRY_Y - 0.34, SA_X, LOAD_Y + SA_H/2)

VIZ_Q_Y = LOAD_Y - 1.15
diamond(ax, SA_X, VIZ_Q_Y, 4.8, 1.15, "Continue with\nsecondary analysis?")
arrow(ax, SA_X, LOAD_Y - SA_H/2, SA_X, VIZ_Q_Y + 0.575)

VIZ_DONE_X = SA_X + 5.5
stadium(ax, VIZ_DONE_X, VIZ_Q_Y, 3.2, 0.62, "Analysis Complete")
arrow(ax, SA_X + 2.4, VIZ_Q_Y, VIZ_DONE_X - 1.6, VIZ_Q_Y,
      label="No", color=C["arrow_no"])

SK_Q_Y = VIZ_Q_Y - 1.3
diamond(ax, SA_X, SK_Q_Y, 4.4, 1.1, "Seeker data?")
arrow(ax, SA_X, VIZ_Q_Y - 0.575, SA_X, SK_Q_Y + 0.55,
      label="Yes", color=C["arrow_yes"])

BG_X = SA_X - 4.0
BG_Y = SK_Q_Y
box(ax, BG_X, BG_Y, 4.4, 0.65,
    "background_removal",
    "Remove spatial background\n(KitType 10×10 or 3×3)",
    fc=C["seeker"], ec=C["seeker_bd"])
arrow(ax, SA_X - 2.2, SK_Q_Y, BG_X + 2.2, BG_Y,
      label="Yes", color=C["seeker_bd"])

QC_Y = SK_Q_Y - 1.15
sa_step(QC_Y, "qc", "Quality control + cell filtering",
        C["step"], C["step_bd"])
arrow(ax, SA_X, SK_Q_Y - 0.55, SA_X, QC_Y + SA_H/2,
      label="No", color=C["arrow_no"])
# bg_removal merges into qc
arrow(ax, BG_X, BG_Y - SA_H/2, BG_X, QC_Y,
      connectionstyle="arc3,rad=0.0")
arrow(ax, BG_X, QC_Y, SA_X - SA_W/2, QC_Y)

steps_below = [
    ("normalization",          "Normalize + log-transform counts"),
    ("feature_selection",      "Select highly variable genes"),
    ("dimensionality_reduction","PCA → UMAP embedding"),
    ("clustering",             "Leiden community detection"),
]

prev_y = QC_Y
for name, sub in steps_below:
    ny = prev_y - SA_GAP
    sa_step(ny, name, sub, C["step"], C["step_bd"])
    arrow(ax, SA_X, prev_y - SA_H/2, SA_X, ny + SA_H/2)
    prev_y = ny

CLUST_Y = prev_y

# ── 5. Analysis goal diamond ────────────────────────────────────────────────
GOAL_Y = CLUST_Y - 1.2
diamond(ax, SA_X, GOAL_Y, 4.8, 1.2, "Analysis goal?")
arrow(ax, SA_X, CLUST_Y - SA_H/2, SA_X, GOAL_Y + 0.6)

DGE_X  = SA_X - 4.5
CELL_X = SA_X + 4.5
BOTH_X = SA_X
RES_Y  = GOAL_Y - 1.6

# Marker genes only
box(ax, DGE_X, RES_Y, 4.0, 0.65,
    "diff_gene_expression", "Differential gene\nexpression",
    fc=C["step"], ec=C["step_bd"])
arrow(ax, SA_X - 2.4, GOAL_Y - 0.6, DGE_X + 0.5, RES_Y + SA_H/2,
      label="Marker\ngenes", color=C["step_bd"],
      connectionstyle="arc3,rad=0.15")

# Cell types only
box(ax, CELL_X, RES_Y, 4.0, 0.65,
    "cell_typing", "Cell type annotation",
    fc=C["step"], ec=C["step_bd"])
arrow(ax, SA_X + 2.4, GOAL_Y - 0.6, CELL_X - 0.5, RES_Y + SA_H/2,
      label="Cell\ntypes", color=C["step_bd"],
      connectionstyle="arc3,rad=-0.15")

# Both
DGE2_Y  = RES_Y - 0.1
CELL2_Y = DGE2_Y - SA_GAP + 0.2
box(ax, BOTH_X, DGE2_Y, 4.0, 0.65,
    "diff_gene_expression", "Differential gene\nexpression",
    fc=C["step"], ec=C["step_bd"])
arrow(ax, SA_X, GOAL_Y - 0.6, BOTH_X, DGE2_Y + SA_H/2,
      label="Both", color=C["step_bd"])
box(ax, BOTH_X, CELL2_Y, 4.0, 0.65,
    "cell_typing", "Cell type annotation",
    fc=C["step"], ec=C["step_bd"])
arrow(ax, BOTH_X, DGE2_Y - SA_H/2, BOTH_X, CELL2_Y + SA_H/2)

# ── 6. Terminal nodes ────────────────────────────────────────────────────────
DONE_Y = CELL2_Y - 1.1
stadium(ax, DGE_X,  DONE_Y, 3.0, 0.62, "Analysis Complete")
stadium(ax, CELL_X, DONE_Y, 3.0, 0.62, "Analysis Complete")
stadium(ax, BOTH_X, DONE_Y, 3.0, 0.62, "Analysis Complete")

arrow(ax, DGE_X,  RES_Y - SA_H/2,   DGE_X,  DONE_Y + 0.31)
arrow(ax, CELL_X, RES_Y - SA_H/2,   CELL_X, DONE_Y + 0.31)
arrow(ax, BOTH_X, CELL2_Y - SA_H/2, BOTH_X, DONE_Y + 0.31)

# ── 7. Legend ────────────────────────────────────────────────────────────────
LEG_X, LEG_Y = 0.4, 9.5
ax.text(LEG_X, LEG_Y + 0.6, "Legend", color=C["text"],
        fontsize=10, fontweight="bold")
items = [
    (C["wf"],         C["wf_bd"],         "Primary analysis workflow  (wf/)"),
    (C["step"],       C["step_bd"],        "Secondary analysis step  (steps/)"),
    (C["seeker"],     C["seeker_bd"],      "Seeker-only step"),
    (C["preprocess"], C["preprocess_bd"],  "Platform preprocessing workflow"),
    (C["output"],     C["output_bd"],      "Data output artifact"),
    (C["decision"],   C["decision_bd"],    "Decision / branch point"),
]
for i, (fc, ec, label) in enumerate(items):
    yy = LEG_Y - i * 0.72
    patch = FancyBboxPatch((LEG_X, yy - 0.2), 0.55, 0.38,
                           boxstyle="round,pad=0,rounding_size=0.08",
                           fc=fc, ec=ec, lw=1.4, zorder=3)
    ax.add_patch(patch)
    ax.text(LEG_X + 0.72, yy - 0.01, label, color=C["text"],
            fontsize=8.8, va="center")

# ── Save ─────────────────────────────────────────────────────────────────────
OUT = "/Users/kutchmaa/Documents/Code/takara-devkit/latch-skills/takara-devkit/process_flow.png"
plt.savefig(OUT, dpi=180, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print(f"Saved → {OUT}")
