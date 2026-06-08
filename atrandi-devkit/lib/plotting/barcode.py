#!/usr/bin/env python3

import polars as pl
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams, gridspec
import plotnine as gg

from math import log10
from string import ascii_uppercase
from scipy.signal import argrelextrema
from scipy.ndimage import gaussian_filter1d
from pathlib import Path

from upsetplot import from_memberships, UpSet

from lib.common_const import (
    BARCODE_A,
    BARCODE_B,
    BARCODE_C,
    BARCODE_D,
    BARCODE,
    BARCODE_POSITION,
    READS,
    PRIMER,
    HUMAN_READABLE_NAMES,
    INDEX,
)

from lib.plotting.common import convert_df_to_upset_data, convert_membership_names
from lib.dataframe_toolkit import get_most_freq_df


def prepare_barcode_occurence_data(
    df: pl.DataFrame,
    reference_list: pl.DataFrame,
) -> pl.DataFrame:
    letters_enum = pl.Enum(list(ascii_uppercase)[::-1])
    num_enum = pl.Enum([str(i) for i in list(range(1, 13))[::-1]])
    rich_ref_list = reference_list.with_columns(
        row=pl.col(INDEX).str.extract("[A-Z]{1}", 0).cast(letters_enum),
        column=pl.col(INDEX).str.extract(r"[0-9]{1,}", 0).cast(num_enum),
    )
    all = []
    for barcode_position in [BARCODE_A, BARCODE_B, BARCODE_C, BARCODE_D]:
        temp = (
            df.select(BARCODE_A, BARCODE_B, BARCODE_C, BARCODE_D)
            .unique()
            .select(barcode_position)
            .join(rich_ref_list, left_on=barcode_position, right_on=BARCODE)
            .drop(barcode_position)
        )
        all.append(temp)
    concatenated = pl.concat(all)

    summarized_data = (
        concatenated.group_by("row", "column", BARCODE_POSITION)
        .agg(pl.len().alias("# Barcode"))
        .with_columns(
            pl.col(BARCODE_POSITION).cast(
                pl.Enum([BARCODE_A, BARCODE_B, BARCODE_C, BARCODE_D])
            )
        )
    )
    return summarized_data


def plot_barcode_occurence_heatmap(
    df: pl.DataFrame,
    cumsum_fraction: float,
    sample_name: str,
    library_type: str,
    barcode_pool_size: int,
    indices: str,
) -> None:
    min_value = df.select("# Barcode").min().item()
    max_value = df.select("# Barcode").max().item()
    if barcode_pool_size == 24:
        fig_width = 6
    else:
        fig_width = 12

    if indices == "null":
        plot = (
            gg.ggplot(df)
            + gg.aes(y="row", x="column", fill="# Barcode")
            + gg.geom_tile()
            + gg.facet_wrap(BARCODE_POSITION, nrow=1, scales="free_x")
            + gg.coord_fixed()
            + gg.ggtitle(
                f"Barcode occurence in plates for sample {sample_name}",
                subtitle=f"Min value = {min_value}, top {int(cumsum_fraction * 100)}% cumsum reads used",
            )
            + gg.theme(figure_size=(fig_width, 5))
            + gg.scale_fill_continuous(limits=(0, max_value))
        )
    else:
        plot1 = (
            gg.ggplot(df.filter(pl.col(BARCODE_POSITION) != BARCODE_A))
            + gg.aes(y="row", x="column", fill="# Barcode")
            + gg.geom_tile()
            + gg.facet_wrap(BARCODE_POSITION, nrow=1, scales="free_x")
            + gg.coord_fixed()
            + gg.ggtitle(
                f"Barcode occurence in plates for sample {sample_name}",
                subtitle=f"Min value = {min_value}, top {int(cumsum_fraction * 100)}% cumsum reads used",
            )
            + gg.theme(figure_size=(fig_width * 2, 5))
            + gg.scale_fill_continuous(limits=(0, max_value))
        )

        plot2 = (
            gg.ggplot(df.filter(pl.col(BARCODE_POSITION) == BARCODE_A))
            + gg.aes(y="row", x="column", fill="# Barcode")
            + gg.geom_tile()
            + gg.facet_wrap(BARCODE_POSITION, nrow=1)
            + gg.coord_fixed()
            + gg.theme(figure_size=(fig_width * 1.5, 5))
            + gg.scale_fill_continuous(limits=(0, max_value))
        )

        plot = plot1 | plot2

    plot.save(f"{library_type}_barcode_occurence_heatmap.png")


def plot_fraction_barcodes_heatmap(
    corrected: pl.LazyFrame, ref_df: pl.DataFrame, sample_name: str, sample_out: Path
):
    """
    Plot a heatmap of fraction of reads for each barcode for each ligation step based on ref_df.
    X axis are ligation steps (D,C,B,A), y axis are barcodes (96)
    """
    steps = [BARCODE_D, BARCODE_C, BARCODE_B, BARCODE_A]
    heatmap = []
    for step in steps:
        barcodes_list = ref_df.filter(pl.col(BARCODE_POSITION) == step)[
            BARCODE
        ].to_list()
        counts = (
            corrected.group_by(step)
            .agg(pl.col(READS).sum())
            .rename({step: BARCODE})
            .join(pl.LazyFrame({BARCODE: barcodes_list}), on=BARCODE, how="right")
            .fill_null(0)
            .sort(BARCODE)
        ).collect()
        total = counts[READS].sum()

        fractions = counts[READS] / total
        heatmap.append(fractions.to_numpy())
    heatmap = np.array(heatmap).T  # shape: (96, 4)
    mean_freq = 1 / (ref_df.shape[0] / 4)
    vmin = mean_freq - (0.75 * mean_freq)
    vmax = mean_freq + (0.75 * mean_freq)
    plt.figure(figsize=(2, 6))
    im = plt.imshow(heatmap, aspect="auto", cmap="PiYG", vmin=vmin, vmax=vmax)
    plt.colorbar(im, label="Fraction or reads in barcode")
    plt.xticks(range(len(steps)), steps)
    plt.tick_params(
        axis="y",  # changes apply to the x-axis
        which="both",  # both major and minor ticks are affected
        left=False,  # ticks along the bottom edge are off
        top=False,  # ticks along the top edge are off
        labelbottom=False,
    )
    # plt.yticks(range(heatmap.shape[0]), range(1, heatmap.shape[0]+1))
    plt.xlabel("Ligation step")
    plt.ylabel("Barcode index")
    plt.title(f"Barcode read distribution in {sample_name}")
    plt.tight_layout()
    plt.savefig(sample_out / f"{sample_name}_barcode_heatmap.png", dpi=300)
    plt.close()


def find_inflection_minimum(
    counts: list, sample_name: str, sample_out: Path, smooth_sigma: int = 2
):
    """
    Finds the local minimum (inflection point) between 'true' and 'false' barcodes
    in the log10-transformed count distribution.
    """
    # Log-transform the counts (add 1 to avoid log(0))
    log_counts = np.log10(np.array(counts) + 1)

    # Create histogram of log-counts
    hist, bin_edges = np.histogram(log_counts, bins=100)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Smooth the histogram for easier minima detection
    hist_smooth = gaussian_filter1d(hist, sigma=smooth_sigma)

    # Find local minima
    minima_indices = argrelextrema(hist_smooth, np.less)[0]
    if len(minima_indices) == 0:
        print("No local minima found in the distribution.")
        knee_threshold = 100
        knee_bin = log10(knee_threshold + 1)
    else:
        # Choose the first minimum after the main peak (assume main peak is at highest bin)
        main_peak = np.argmax(hist_smooth)
        minima_after_peak = minima_indices[minima_indices > main_peak]
        if len(minima_after_peak) == 0:
            knee_bin = bin_centers[minima_indices[0]]
        else:
            knee_bin = bin_centers[minima_after_peak[0]]

        # Convert knee_bin (log10 count) back to count threshold
        knee_threshold = 10**knee_bin

    # Plot for visualization
    plt.figure(figsize=(8, 4))
    plt.plot(bin_centers, hist_smooth, label="Smoothed histogram")
    plt.axvline(
        knee_bin,
        color="red",
        linestyle="--",
        label=f"Inflection (log10={knee_bin:.2f})",
    )
    plt.xlabel("log10(UMI/Read Count + 1)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.title(f"Barcode Count Distribution with Inflection Point {sample_name}")
    plt.savefig(sample_out / f"{sample_name}_barcode_inflection.png", dpi=300)
    plt.close()

    return knee_threshold


def plot_barcode_upset_plot(
    raw_bc_corrected: pl.LazyFrame,
    ref_df: pl.DataFrame,
    sample_name: str,
    library_type: str,
    indices: str,
):
    """Plot an Upset plot with barcode positions data.

    Args:
        raw_bc_corrected (pl.LazyFrame): read counts of corrected barcodes
        ref_df (pl.DataFrame): Long list of barcode whitelist
        sample_name (str): sample name
        sample_out (Path): output path for the plot
    """
    most_freq_seq = None
    ids = [BARCODE_D, BARCODE_C, BARCODE_B, BARCODE_A]
    cols = raw_bc_corrected.collect_schema().names()
    if PRIMER in cols:
        most_freq_seq = get_most_freq_df(raw_bc_corrected, key=PRIMER).collect().item()
        ids.append(PRIMER)
        most_freq_seq = "GACTTGAGTGGCTGTCGG"

    if most_freq_seq is not None:
        whitelisted = raw_bc_corrected.with_columns(
            pl.col(BARCODE_D).is_in(
                ref_df.filter(pl.col(BARCODE_POSITION) == BARCODE_D)[BARCODE].to_list()
            ),
            pl.col(BARCODE_C).is_in(
                ref_df.filter(pl.col(BARCODE_POSITION) == BARCODE_C)[BARCODE].to_list()
            ),
            pl.col(BARCODE_B).is_in(
                ref_df.filter(pl.col(BARCODE_POSITION) == BARCODE_B)[BARCODE].to_list()
            ),
            pl.col(BARCODE_A).is_in(
                ref_df.filter(pl.col(BARCODE_POSITION) == BARCODE_A)[BARCODE].to_list()
            ),
            (pl.col(PRIMER) == most_freq_seq),
        ).with_row_index()
    else:
        whitelisted = raw_bc_corrected.with_columns(
            pl.col(BARCODE_D).is_in(
                ref_df.filter(pl.col(BARCODE_POSITION) == BARCODE_D)[BARCODE].to_list()
            ),
            pl.col(BARCODE_C).is_in(
                ref_df.filter(pl.col(BARCODE_POSITION) == BARCODE_C)[BARCODE].to_list()
            ),
            pl.col(BARCODE_B).is_in(
                ref_df.filter(pl.col(BARCODE_POSITION) == BARCODE_B)[BARCODE].to_list()
            ),
            pl.col(BARCODE_A).is_in(
                ref_df.filter(pl.col(BARCODE_POSITION) == BARCODE_A)[BARCODE].to_list()
            ),
        ).with_row_index()

    temp = whitelisted.fill_null(False).group_by(ids).agg(pl.len().alias(READS))
    rcParams["font.size"] = 8
    memberships, read_counts = convert_df_to_upset_data(temp.collect())
    # convert to human readable names, defaults to variable name if not available
    memberships_hrn = convert_membership_names(memberships=memberships)
    hrn_ids = [HUMAN_READABLE_NAMES.get(i, i) for i in ids]
    upset_data = from_memberships(memberships=memberships_hrn, data=read_counts)
    upset = UpSet(upset_data, show_percentages=True, min_subset_size="1%")
    upset.style_subsets(
        present=hrn_ids,
        facecolor="green",
        label="Correct",
    )
    upset.plot()
    plt.show()
    hrn_data_type = HUMAN_READABLE_NAMES.get(library_type, library_type)
    if indices != "null":
        indices_str = "\n" + indices
    else:
        indices_str = ""
    plt.suptitle(
        f"% reads with barcode detected (corrected).\n{sample_name} - {hrn_data_type}{indices_str}"
    )
    plt.savefig(f"{library_type}_barcode_upset_plot.png")


def plot_rank_knee(
    df_summary: pl.DataFrame,
    knee_ncells: int,
    sample_name: str,
    value_type: str,
    min_value: int = 0,
    max_points: int = 2_000_000,
) -> int:
    """
    Plot total UMI counts sorted descending vs rank, with knee position highlighted.
    """
    rcParams["figure.constrained_layout.use"] = True
    umi_at_k = 0

    _, ax = plt.subplots(1, 1, figsize=(6, 4), dpi=120)

    y = df_summary[value_type].to_numpy()
    if min_value > 0:
        y = y[y >= min_value]
    y = np.sort(y)[::-1]
    n = len(y)

    if n == 0:
        ax.set_title(
            f"No barcodes above min {value_type} threshold of {min_value}\n{sample_name}"
        )
        plt.savefig(f"{sample_name}_knee_plot.png")
        return umi_at_k

    # Downsample if very large
    if n > max_points:
        idx = np.linspace(0, n - 1, max_points).astype(int)
        y_plot = y[idx]
        ranks = idx + 1
    else:
        y_plot = y
        ranks = np.arange(1, n + 1)

    ax.plot(ranks, y_plot, lw=1.2, color="#1f77b4")
    if knee_ncells is not None and knee_ncells > 0:
        k = min(knee_ncells, n)
        ax.axvline(k, color="crimson", ls="--", lw=1.2, label=f"knee ≈ {k:,}")
        # annotate UMI at knee
        umi_at_k = y[k - 1] if k - 1 < len(y) else y[-1]
        ax.axhline(umi_at_k, color="gray", ls=":", lw=1.0)
        ax.scatter([k], [umi_at_k], color="crimson", s=30, zorder=3)
        ax.text(
            k,
            umi_at_k,
            f"  {value_type}={int(umi_at_k):,}",
            va="bottom",
            ha="left",
            fontsize=9,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Barcode rank (log)")
    ax.set_ylabel(f"Total {value_type} (log)")
    ax.set_title(f"Ranked {value_type} curve with knee\n{sample_name}")
    ax.legend(frameon=False)
    ax.grid(True, which="both", ls=":", lw=0.5, alpha=0.6)
    plt.savefig(f"knee_plot.png")
    return int(umi_at_k)


def startfig(
    w=4, h=2, rows=1, columns=1, wrs=None, hrs=None, frameon=True, return_first_ax=True
):
    """
    for initiating figures, w and h in centimeters
    example of use:
    a,fig,gs = startfig(w=10,h=2.2,rows=1,columns=3,wr=[4,50,1],hrs=None,frameon=True)
    hrs - height ratios
    wrs - width ratios
    frameon - whether first axes with frame

    returns:
    if return_first_ax=True
    a,fig,gs
    else
    fig,gs
    """

    ratio = 0.393701  # 1 cm in inch
    myfigsize = (w * ratio, h * ratio)
    fig = plt.figure(figsize=(myfigsize))
    gs = gridspec.GridSpec(rows, columns, width_ratios=wrs, height_ratios=hrs)
    if return_first_ax == True:
        a = fig.add_subplot(gs[0, 0], frameon=frameon)
        return a, fig, gs
    else:
        return fig, gs


def plot_histograms(
    df, sample_name: str, umi_threshold: int, data_type: str, nbins: int = 50
):
    """_summary_

    Args:
        data (_type_): Per barcode count df
        sample_name (str): _description_
        umi_threshold (int): Min number of UMIs.
        nbins (int, optional): _description_. Defaults to 50.
    """
    data = df[data_type].to_numpy()
    fig, gs = startfig(18, 14, columns=2, rows=2, hrs=[1.5, 1], return_first_ax=False)
    a1 = fig.add_subplot(gs[0, 0])
    a1.hist(np.log10(data), bins=nbins, color="0.6")
    a1.set_ylabel("# barcodes")
    a1.set_title(f"Barcode\n{data_type} count distribution")

    a2 = fig.add_subplot(gs[0, 1])
    a2.hist(np.log10(data), weights=data, bins=nbins, color="0.4")
    a2.set_ylabel(f"# {data_type}s coming from bin")
    a2.set_title(f"Weighted barcode\n{data_type} depth distribution")

    for a in [a1, a2]:
        a.set_xlabel(f"log10(# {data_type}s)")
        a.axvline(np.log10(umi_threshold), linestyle="--", lw=1, color="r")

    # plot super title
    fig.suptitle(f"{sample_name}")

    # plot text with filtering stats
    a3 = fig.add_subplot(gs[1, 0])

    m = data >= umi_threshold
    lines = [
        "Total number of barcodes: %d" % len(data),
        f"Total number of {data_type}: %d" % data.sum(),
        "-" * 100,
        f"Selected minimum {data_type} number threshold: %d" % umi_threshold,
        "-" * 100,
        f"Percent barcodes with >=%d {data_type}: %.1f%%"
        % (umi_threshold, len(data[m]) / len(data) * 100.0),
        f"Percent {data_type} from barcodes with >=%d {data_type}: %.1f%%"
        % (umi_threshold, data[m].sum() / data.sum() * 100.0),
        "-" * 100,
        f"Number of barcodes with >=%d {data_type}: %d" % (umi_threshold, len(data[m])),
        f"Number of {data_type} from barcodes with >=%d {data_type}: %d"
        % (umi_threshold, data[m].sum()),
        "-" * 100,
    ]

    # Remove all spines, ticks, etc.
    a3.set_axis_off()

    # Print each line as text in the subplot
    for i, line in enumerate(lines):
        a3.text(0, 1 - i * 0.1, line, fontsize=10, va="top")

    gs.tight_layout(fig)
    fig.savefig("mapped_histo.png")
