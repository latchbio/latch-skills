"""Background (off-tissue bead) removal for Takara Seeker spatial transcriptomics data.

All three filter masks are derived from ``obs['total_counts']`` and ``obsm['spatial']``
alone. ``.X`` is touched exactly once, at the very end, to materialize the filtered
object. Nothing here scales worse than linearly in the number of beads.
"""

import warnings
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
import scipy.sparse as sp
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


def _grid_bin_ids(coords: np.ndarray, grid_size: int) -> np.ndarray:
    """Flat linear bin id (``x_bin * grid_size + y_bin``) for each bead.

    The binning arithmetic is unchanged from the original per-bead implementation;
    only the representation is flattened so the counts can be taken with
    ``np.bincount`` instead of a Python-level dict lookup per bead.
    """
    x_min, x_max = coords[:, 0].min(), coords[:, 0].max()
    y_min, y_max = coords[:, 1].min(), coords[:, 1].max()

    x_width = (x_max - x_min) / grid_size
    y_width = (y_max - y_min) / grid_size

    # A degenerate (zero-width) bounding box would divide by zero and leave the
    # subsequent astype(int) undefined. Every bead shares one coordinate, so they
    # all belong in bin 0 — say so explicitly rather than relying on the clip below
    # to launder a NaN.
    if x_width == 0:
        x_width = 1.0
    if y_width == 0:
        y_width = 1.0

    x_bins = np.floor((coords[:, 0] - x_min) / x_width).astype(int)
    y_bins = np.floor((coords[:, 1] - y_min) / y_width).astype(int)

    x_bins = np.clip(x_bins, 0, grid_size - 1)
    y_bins = np.clip(y_bins, 0, grid_size - 1)

    return x_bins.astype(np.int64) * grid_size + y_bins.astype(np.int64)


def grid_density_filter(
    coords: np.ndarray,
    grid_size: int,
    min_beads: int,
) -> tuple[np.ndarray, pd.Series]:
    """Keep beads whose ``grid_size`` x ``grid_size`` cell holds >= ``min_beads`` beads.

    Returns ``(keep_mask, cell_counts)``, where ``cell_counts`` is a Series of per-cell
    bead counts indexed by ``(x_bin, y_bin)`` tuples, sorted by count descending. Only
    occupied cells appear, matching ``value_counts()``.
    """
    if len(coords) == 0:
        return np.zeros(0, dtype=bool), pd.Series(
            np.zeros(0, dtype=np.int64),
            index=pd.Index([], dtype=object, tupleize_cols=False),
            name="count",
        )

    flat_ids = _grid_bin_ids(coords, grid_size)
    counts = np.bincount(flat_ids, minlength=grid_size * grid_size)

    keep_mask = counts[flat_ids] >= min_beads

    occupied = np.flatnonzero(counts)
    occ_counts = counts[occupied]

    # Count descending, ties broken by cell id ascending so the ordering is
    # reproducible run to run (value_counts used a non-stable sort).
    order = np.lexsort((occupied, -occ_counts))
    occupied = occupied[order]
    occ_counts = occ_counts[order]

    cell_ids = list(
        zip(
            (occupied // grid_size).tolist(),
            (occupied % grid_size).tolist(),
            strict=True,
        )
    )
    # tupleize_cols=False keeps this a flat object Index of tuples. Without it pandas
    # promotes a list of tuples to a MultiIndex, and reset_index() downstream would
    # then produce three columns instead of two.
    cell_counts = pd.Series(
        occ_counts,
        index=pd.Index(cell_ids, tupleize_cols=False),
        name="count",
    )
    return keep_mask, cell_counts


def _to_csr(mat):
    """Return ``mat`` as CSR if it is a CSC sparse matrix, else unchanged."""
    if sp.issparse(mat) and mat.format == "csc":
        return mat.tocsr()
    return mat


def remove_background(
    adata: AnnData,
    kit_type: KitType,
    min_log10_umi: float = 1.4,
    m: int = 40,
    n: int = 100,
    p: int = 5,
    q: int = 10,
    to_csr: bool = True,
) -> BackgroundRemovalResult:
    """Remove off-tissue background beads from Seeker spatial data.

    ``adata_step1`` and ``adata_step2`` are returned as zero-copy AnnData *views* onto
    ``adata``. They cost nothing to build and hold no data of their own, but they keep
    ``adata`` alive for as long as the result is referenced, and writing to them
    silently materializes a full copy. Read them, don't mutate them.

    Set ``to_csr=False`` to leave ``adata_filtered.X`` in whatever format it arrived in.
    """
    tile_size = 10000 if kit_type == KitType.TEN_BY_TEN else 3000
    grid_m = int(tile_size / m)
    grid_n = int(tile_size / n)

    if "total_counts" not in adata.obs:
        raise KeyError(
            "adata.obs['total_counts'] is required by remove_background(); compute it "
            "with sc.pp.calculate_qc_metrics or set it before calling."
        )
    if "spatial" not in adata.obsm:
        raise KeyError("adata.obsm['spatial'] is required by remove_background().")

    if not adata.obs_names.is_unique:
        warnings.warn(
            "adata.obs_names are not unique. Masks are composed positionally, so beads "
            "sharing a barcode are filtered independently. Earlier versions matched by "
            "barcode value and kept every bead sharing a retained barcode, including "
            "ones that had failed the UMI filter. Call adata.obs_names_make_unique() "
            "to silence this.",
            RuntimeWarning,
            stacklevel=2,
        )

    # Side effect preserved: the caller's adata gains this column.
    adata.obs["log10_nCount_RNA"] = np.log10(adata.obs["total_counts"].values + 1)

    n_obs = adata.n_obs
    coords_all = np.asarray(adata.obsm["spatial"])

    # Step 1 — UMI threshold.
    step1_mask = adata.obs["log10_nCount_RNA"].values >= min_log10_umi
    idx1 = np.flatnonzero(step1_mask)
    coords_step1 = coords_all[idx1]

    # Step 2 — fine-grid density. Masks compose in index space; matching on barcode
    # strings here was the quadratic step that made this function run for hours.
    step2_local_mask, step2_counts = grid_density_filter(coords_step1, grid_m, p)
    idx2 = idx1[step2_local_mask]
    step2_mask = np.zeros(n_obs, dtype=bool)
    step2_mask[idx2] = True

    # Step 3 — coarse-grid density.
    coords_step2 = coords_step1[step2_local_mask]
    step3_local_mask, step3_counts = grid_density_filter(coords_step2, grid_n, q)
    idx3 = idx2[step3_local_mask]
    step3_mask = np.zeros(n_obs, dtype=bool)
    step3_mask[idx3] = True

    # Materialize the one subset downstream steps actually consume.
    if adata.isbacked:
        warnings.warn(
            "adata was opened in backed mode. AnnData.copy() is not supported on backed "
            "objects, so the filtered subset is materialized with .to_memory(); if .X is "
            "stored as CSC this reads the entire matrix from disk. Prefer loading with "
            "ad.read_h5ad(path) with no backed= argument.",
            RuntimeWarning,
            stacklevel=2,
        )
        adata_filtered = adata[step3_mask].to_memory()
    else:
        if sp.issparse(adata.X) and adata.X.format == "csc" and to_csr:
            warnings.warn(
                "adata.X is stored as CSC. Bead-wise subsetting and every downstream "
                "per-bead operation are several times slower on CSC than on CSR, so "
                "adata_filtered.X is being returned as CSR. Pass to_csr=False to keep "
                "the input format.",
                RuntimeWarning,
                stacklevel=2,
            )
        adata_filtered = adata[step3_mask].copy()

    if to_csr:
        if adata_filtered.X is not None:
            adata_filtered.X = _to_csr(adata_filtered.X)
        for key in list(adata_filtered.layers.keys()):
            adata_filtered.layers[key] = _to_csr(adata_filtered.layers[key])

    step2_density = step2_counts.reset_index()
    step2_density.columns = ["cell_id", "count"]

    step3_density = step3_counts.reset_index()
    step3_density.columns = ["cell_id", "count"]

    return BackgroundRemovalResult(
        adata_filtered=adata_filtered,
        # Zero-copy views: free to build, hold no data of their own.
        adata_step1=adata[step1_mask],
        adata_step2=adata[step2_mask],
        step1_mask=step1_mask,
        step2_mask=step2_mask,
        step3_mask=step3_mask,
        step2_density=step2_density,
        step3_density=step3_density,
    )
