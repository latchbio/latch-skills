#!/usr/bin/env python3

import polars as pl
import polars_distance as pld
import numpy as np
from numpy.typing import NDArray

from pathlib import Path

from lib.common_const import COUNTS, BARCODE_A, READS
from typing import Final

# CONSTANTS


def correct_barcodes_pl(
    barcodes_df: pl.DataFrame,
    barcode_subset_df: pl.DataFrame,
    hamming_distance: int,
    barcode_col_name: str,
    whitelist_col_name: str,
) -> dict:
    """Corrects barcodes using a subset based on join_asof from polars.
    Uses both forward and backward strategy to dinf the closest barcode

    Args:
        barcodes_df (pl.DataFrame): All barcodes with their respective counts
        barcode_subset_df (pl.DataFrame): Barcode reference used to correct
        hamming_distance (int): Max hamming distance allowed
        mapped_barcodes (dict): Dict of mapped barcodes

    Returns:
        tuple[pl.DataFrame, int]: The corrected version of the input barcodes_df, number of corrected barcodes
    """
    print("Correcting barcodes")
    corrected_barcodes_pl = pl.DataFrame(
        schema={
            barcode_col_name: pl.String,
            COUNTS: pl.UInt32,
            whitelist_col_name: pl.String,
        }
    )
    current_barcodes = pl.DataFrame(
        schema={
            barcode_col_name: pl.String,
            COUNTS: pl.UInt32,
            whitelist_col_name: pl.String,
        }
    )
    current_barcodes_to_correct = barcodes_df.shape[0]
    last_iteration_barcodes_to_correct = 0
    unknown_barcodes = barcodes_df.filter(
        ~pl.col(barcode_col_name).is_in(barcode_subset_df[whitelist_col_name])
    )
    n_iterations = 0
    while (
        current_barcodes_to_correct > 0
        and current_barcodes_to_correct != last_iteration_barcodes_to_correct
    ):
        methods = ["backward", "forward"]
        for method in methods:
            current_barcodes = (
                (
                    unknown_barcodes.filter(
                        (
                            ~pl.col(barcode_col_name).is_in(
                                corrected_barcodes_pl[barcode_col_name]
                            )
                        )
                    )
                    .sort(barcode_col_name)
                    .join_asof(
                        barcode_subset_df.sort(whitelist_col_name),
                        left_on=barcode_col_name,
                        right_on=whitelist_col_name,
                        strategy=method,  # type: ignore
                    )
                )
                .filter(~pl.col(whitelist_col_name).is_null())
                .with_columns(
                    pld.col(barcode_col_name)
                    .dist_str.hamming(pl.col(whitelist_col_name))
                    .cast(pl.UInt32)
                    .alias("hamming_distance")
                )
                .filter(pl.col("hamming_distance") <= hamming_distance)
                .drop("hamming_distance")
            )
            corrected_barcodes_pl = pl.concat(
                [
                    corrected_barcodes_pl,
                    current_barcodes,
                ]
            )
        current_barcodes_to_correct = current_barcodes.shape[0]
        barcode_subset_df = barcode_subset_df.filter(
            ~pl.col(whitelist_col_name).is_in(corrected_barcodes_pl[whitelist_col_name])
        )
        n_iterations += 1
    print(f"Corrected barcodes in {n_iterations} iterations")
    print(f"Number of uncorrected barcodes: {current_barcodes.shape[0]}")
    mapped_barcodes = dict(
        corrected_barcodes_pl.select(barcode_col_name, whitelist_col_name).iter_rows()  # type: ignore
    )
    print("Barcodes corrected")

    return mapped_barcodes


def get_motif_freq(one_column_df: pl.DataFrame, size: int) -> NDArray | None:
    """Get motif frequency of DNA bases

    Args:
        one_column_df (pl.DataFrame): On column df of the sequence we want the motif from
        size (int): length of the sequence

    Returns:
        NDArray | None: array struct for plotting
    """
    A = []
    C = []
    G = []
    T = []
    name = one_column_df.columns[0]
    splitted = (
        one_column_df.filter(
            pl.col(name).is_not_null(),
            pl.col(name).str.len_chars() == 8,
            ~pl.col(name).str.contains("N"),
        )
        .with_columns(pl.col(name).str.split_exact(by="", n=(size - 1)))
        .unnest(name)
    )
    for name in splitted.columns:
        aggregated = splitted.select(name).group_by(name).agg(pl.len().alias(READS))
        A.append(aggregated.filter(pl.col(name) == "A")[READS].item())
        C.append(aggregated.filter(pl.col(name) == "C")[READS].item())
        G.append(aggregated.filter(pl.col(name) == "G")[READS].item())
        T.append(aggregated.filter(pl.col(name) == "T")[READS].item())
    freq_list = np.array([np.array(A), np.array(C), np.array(G), np.array(T)])
    return freq_list
