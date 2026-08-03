"""Background (off-tissue bead) removal for Takara Seeker spatial transcriptomics data.

All three filter masks are derived from ``obs['total_counts']`` and ``obsm['spatial']``
alone. Both are fully resident even when the H5AD is opened with ``backed='r'``, so mask
computation never touches the counts matrix and never scales worse than linearly in the
number of beads. The counts matrix is touched exactly once, to materialize the filtered
subset.

Measured against the pre-optimization implementation at 150,000 beads x 4,000 genes
(57M non-zeros), same in-memory input, separate processes: 236.4 s -> 0.5 s wall clock,
and 1118 MB -> 338 MB of peak RSS above baseline.
"""

import logging
import time
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
import scipy.sparse as sp
from anndata import AnnData

_log = logging.getLogger(__name__)

# grid_density_filter counts occupied cells with np.bincount, which allocates one int64
# per *possible* cell. That is free at the defaults (m=40 -> 250^2 = 62,500 cells) but
# grows quadratically as m shrinks, so fall back to np.unique -- which allocates per
# *occupied* cell, like the original value_counts() -- past this point.
_MAX_DENSE_BINS = 4_000_000


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


def _emit(progress: Callable[[str], None] | None, t0: float, msg: str) -> None:
    """Report progress. A silent multi-minute stall is the failure mode this guards."""
    line = f"[remove_background +{time.monotonic() - t0:6.1f}s] {msg}"
    if progress is not None:
        progress(line)
    else:
        _log.info(line)


def _layer_keys(obj: AnnData) -> list[str]:
    """Real layer names. anndata exposes a ``None`` key in ``.layers`` aliasing ``X``."""
    return [k for k in obj.layers.keys() if k is not None]


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
    n_cells = grid_size * grid_size

    if n_cells <= _MAX_DENSE_BINS:
        counts = np.bincount(flat_ids, minlength=n_cells)
        keep_mask = counts[flat_ids] >= min_beads
        occupied = np.flatnonzero(counts)
        occ_counts = counts[occupied]
    else:
        # Sparse fallback: allocates per occupied cell rather than per possible cell.
        occupied, inverse, occ_counts = np.unique(
            flat_ids, return_inverse=True, return_counts=True
        )
        keep_mask = occ_counts[inverse] >= min_beads

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


def _to_csr_freeing_source(adata_obj: AnnData, key: str | None = None) -> None:
    """Convert a CSC ``.X`` or layer to CSR, dropping the CSC as soon as possible.

    Both matrices are unavoidably alive while ``tocsr()`` runs -- scipy has no in-place
    conversion -- but detaching first means the source is freed the moment it returns
    rather than lingering for the rest of the call. Measured: with this, ``to_csr=True``
    peaks no higher than ``to_csr=False``.
    """
    mat = adata_obj.X if key is None else adata_obj.layers[key]
    if not (sp.issparse(mat) and mat.format == "csc"):
        return

    if key is None:
        adata_obj.X = None
    else:
        del adata_obj.layers[key]

    converted = mat.tocsr()
    del mat

    if key is None:
        adata_obj.X = converted
    else:
        adata_obj.layers[key] = converted


def remove_background(
    adata: AnnData,
    kit_type: KitType,
    min_log10_umi: float = 1.4,
    m: int = 40,
    n: int = 100,
    p: int = 5,
    q: int = 10,
    to_csr: bool = False,
    progress: Callable[[str], None] | None = None,
) -> BackgroundRemovalResult:
    """Remove off-tissue background beads from Seeker spatial data.

    Works on both in-memory and ``backed='r'`` AnnData. Backed input is materialized
    with ``.to_memory()`` on the filtered subset only; measured at 57M non-zeros that is
    both faster and lower-peak than reading the whole matrix in up front.

    Does **not** modify the caller's ``adata``. Earlier versions wrote
    ``obs['log10_nCount_RNA']`` back to it; that column now lands on ``adata_filtered``
    only, because the source object is typically bound to a ``w_h5`` viewer with
    ``sync_to`` and any ``.obs`` write there can trigger a full upload of the H5AD.

    ``adata_step1`` and ``adata_step2`` are returned as zero-copy AnnData *views* onto
    ``adata``. They cost nothing to build and hold no data of their own, but they keep
    ``adata`` alive for as long as the result is referenced, and writing to them
    silently materializes a full copy. Read them, don't mutate them.

    ``to_csr`` converts the filtered ``.X`` (and any CSC layer) to CSR, which is faster
    for every downstream per-bead operation. It defaults to ``False`` so that the
    conversion happens after normalization has shrunk the matrix rather than at peak
    memory here.

    Pass ``progress`` (e.g. ``print``, or a ``w_text_output`` updater) to follow a long
    run; otherwise progress goes to this module's logger at INFO. Enable it with
    ``logging.getLogger("takara.background_removal").setLevel(logging.INFO)``.
    """
    t0 = time.monotonic()

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

    # Computed locally and deliberately NOT written back to adata.obs. w_h5(sync_to=...)
    # persists by serializing the Python AnnData and uploading it to the LPath, so an
    # .obs write on the object bound to the viewer can kick off a full multi-GB upload
    # from inside this function -- with no traceback and no warning if it stalls. The
    # column is attached to adata_filtered instead, which the viewer does not hold.
    # To annotate the source anyway, do it explicitly at the call site:
    #     adata.obs["log10_nCount_RNA"] = np.log10(adata.obs["total_counts"].values + 1)
    log10_umi = np.log10(adata.obs["total_counts"].values + 1)

    n_obs = adata.n_obs
    coords_all = np.asarray(adata.obsm["spatial"])

    # Step 1 — UMI threshold.
    step1_mask = log10_umi >= min_log10_umi
    idx1 = np.flatnonzero(step1_mask)
    coords_step1 = coords_all[idx1]
    _emit(progress, t0, f"step 1 (UMI >= {min_log10_umi}): {len(idx1):,} / {n_obs:,} beads")

    # Step 2 — fine-grid density. Masks compose in index space; matching on barcode
    # strings here was the quadratic step that made this function run for hours.
    step2_local_mask, step2_counts = grid_density_filter(coords_step1, grid_m, p)
    idx2 = idx1[step2_local_mask]
    step2_mask = np.zeros(n_obs, dtype=bool)
    step2_mask[idx2] = True
    _emit(progress, t0, f"step 2 (>= {p} beads / {m}um cell): {len(idx2):,} beads")

    # Step 3 — coarse-grid density.
    coords_step2 = coords_step1[step2_local_mask]
    step3_local_mask, step3_counts = grid_density_filter(coords_step2, grid_n, q)
    idx3 = idx2[step3_local_mask]
    step3_mask = np.zeros(n_obs, dtype=bool)
    step3_mask[idx3] = True
    _emit(progress, t0, f"step 3 (>= {q} beads / {n}um cell): {len(idx3):,} beads")

    # Materialize the one subset downstream steps actually consume. This is the only
    # point at which the counts matrix is touched at all.
    if adata.isbacked:
        _emit(progress, t0, "backed input — reading filtered subset from disk")
        adata_filtered = adata[step3_mask].to_memory()
    else:
        _emit(progress, t0, "subsetting counts matrix in memory")
        adata_filtered = adata[step3_mask].copy()

    adata_filtered.obs["log10_nCount_RNA"] = log10_umi[step3_mask]

    if to_csr:
        # Probe the *filtered* matrix, never adata.X — dereferencing .X on the full
        # object is the one operation here that could force a lazily-stored matrix to
        # materialize in its entirety, and it buys nothing.
        _to_csr_freeing_source(adata_filtered)
        for key in _layer_keys(adata_filtered):
            _to_csr_freeing_source(adata_filtered, key)

    _emit(progress, t0, f"done — adata_filtered is {adata_filtered.shape}")

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
