from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
from anndata import AnnData


class KitType(Enum):
    TEN_BY_TEN = "10x10"
    THREE_BY_THREE = "3x3"


@dataclass
class BackgroundRemovalResult:
    adata_filtered: AnnData
    adata_step1: AnnData
    adata_step2: AnnData
    step1_mask: np.ndarray
    step2_mask: np.ndarray
    step3_mask: np.ndarray
    step2_density: pd.DataFrame
    step3_density: pd.DataFrame


def grid_density_filter(
    coords: np.ndarray,
    grid_size: int,
    min_beads: int,
) -> tuple[np.ndarray, pd.Series]:
    x_min, x_max = coords[:, 0].min(), coords[:, 0].max()
    y_min, y_max = coords[:, 1].min(), coords[:, 1].max()

    x_width = (x_max - x_min) / grid_size
    y_width = (y_max - y_min) / grid_size

    x_bins = np.floor((coords[:, 0] - x_min) / x_width).astype(int)
    y_bins = np.floor((coords[:, 1] - y_min) / y_width).astype(int)

    x_bins = np.clip(x_bins, 0, grid_size - 1)
    y_bins = np.clip(y_bins, 0, grid_size - 1)

    cell_ids = list(zip(x_bins, y_bins, strict=False))
    cell_counts = pd.Series(cell_ids).value_counts()

    keep_mask = np.array([cell_counts.get(cid, 0) >= min_beads for cid in cell_ids])
    return keep_mask, cell_counts


def remove_background(
    adata: AnnData,
    kit_type: KitType,
    min_log10_umi: float = 1.4,
    m: int = 40,
    n: int = 100,
    p: int = 5,
    q: int = 10,
) -> BackgroundRemovalResult:
    tile_size = 10000 if kit_type == KitType.TEN_BY_TEN else 3000
    grid_m = int(tile_size / m)
    grid_n = int(tile_size / n)

    adata.obs["log10_nCount_RNA"] = np.log10(adata.obs["total_counts"].values + 1)

    barcodes_all = adata.obs_names.values.copy()

    step1_mask = adata.obs["log10_nCount_RNA"].values >= min_log10_umi
    adata_step1 = adata[step1_mask].copy()

    coords_step1 = adata_step1.obsm["spatial"]
    barcodes_step1 = adata_step1.obs_names.values

    step2_local_mask, step2_counts = grid_density_filter(coords_step1, grid_m, p)

    step2_keep_barcodes = barcodes_step1[step2_local_mask]
    step2_mask = np.isin(barcodes_all, step2_keep_barcodes)

    adata_step2 = adata[step2_mask].copy()

    coords_step2 = coords_step1[step2_local_mask]
    barcodes_step2 = barcodes_step1[step2_local_mask]

    step3_local_mask, step3_counts = grid_density_filter(coords_step2, grid_n, q)

    step3_keep_barcodes = barcodes_step2[step3_local_mask]
    step3_mask = np.isin(barcodes_all, step3_keep_barcodes)

    adata_filtered = adata[step3_mask].copy()

    step2_density = step2_counts.reset_index()
    step2_density.columns = ["cell_id", "count"]

    step3_density = step3_counts.reset_index()
    step3_density.columns = ["cell_id", "count"]

    return BackgroundRemovalResult(
        adata_filtered=adata_filtered,
        adata_step1=adata_step1,
        adata_step2=adata_step2,
        step1_mask=step1_mask,
        step2_mask=step2_mask,
        step3_mask=step3_mask,
        step2_density=step2_density,
        step3_density=step3_density,
    )
