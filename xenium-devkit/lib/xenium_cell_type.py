"""
Helpers for Xenium cell-type annotation with CellGuide.

Exposed functions (used from cell_type_annotation.md):

- load_json_lpath(uri)
- load_vocab_index()
- load_cell_type_vocab_config(organism, tissue, panel_name=None)
- lookup_cellguide_celltypes(genes, organism, tissue, db_or_path)
- summarize_clusters(ranked_df, db_path, organism, tissue, min_markers=3, n_core=10)
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Union

from latch.ldata.path import LPath

# Constants – where docs / vocab live

AGENT_ROOT = Path("/opt/latch/plots-faas/runtime/mount/agent_config")
DOCS_DIR = (
    AGENT_ROOT
    / "context"
    / "technology_docs"
    / "xenium"
    / "steps"
    / "cell_type_annotation"
)
VOCAB_INDEX_PATH = DOCS_DIR / "cell_type_vocab_index.json"


# JSON loading helpers
def load_json_lpath(uri: str) -> Any:
    """
    Load JSON either from a Latch URI (latch://...) or a local path.

    Parameters
    ----------
    uri:
        - If startswith "latch://": uses LPath to download and parse JSON.
        - Otherwise: treated as a local filesystem path.

    Returns
    -------
    Parsed JSON object (usually dict).
    """
    # Latch URI
    if uri.startswith("latch://"):
        if LPath is None:
            raise RuntimeError("Latch LPath is not available in this environment.")
        lp = LPath(uri)
        local = Path(f"{lp.node_id()}.json")
        lp.download(local, cache=True)
        with local.open() as f:
            return json.load(f)

    # Local path
    p = Path(uri)
    with p.open() as f:
        return json.load(f)


def load_vocab_index() -> Dict[str, Any]:
    """
    Load the central cell-type vocab index JSON.

    Looks for `cell_type_vocab_index.json` under:
    /opt/latch/plots-faas/runtime/mount/agent_config/context/technology_docs/xenium
    """
    if not VOCAB_INDEX_PATH.exists():
        raise FileNotFoundError(f"Vocab index not found at {VOCAB_INDEX_PATH}")
    with VOCAB_INDEX_PATH.open() as f:
        return json.load(f)


def load_cell_type_vocab_config(
    organism: str, tissue: str, panel_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Look up and load the vocab config JSON for (organism, tissue[, panel_name]).

    Uses the central index `cell_type_vocab_index.json` to find the config file.

    If panel_name is None:
        - returns the first matching config for (organism, tissue).

    Raises
    ------
    ValueError
        If no matching config is found.
    """
    index = load_vocab_index()

    # First try exact triple match, if panel_name is provided.
    if panel_name is not None:
        for cfg in index.get("configs", []):
            if (
                cfg.get("organism") == organism
                and cfg.get("tissue") == tissue
                and cfg.get("panel_name") == panel_name
            ):
                vocab_path = DOCS_DIR / cfg["path"]
                if not vocab_path.exists():
                    raise FileNotFoundError(f"Vocab config not found at {vocab_path}")
                with vocab_path.open() as f:
                    return json.load(f)

    # Fallback: any config matching organism + tissue.
    for cfg in index.get("configs", []):
        if cfg.get("organism") == organism and cfg.get("tissue") == tissue:
            vocab_path = DOCS_DIR / cfg["path"]
            if not vocab_path.exists():
                raise FileNotFoundError(f"Vocab config not found at {vocab_path}")
            with vocab_path.open() as f:
                return json.load(f)

    raise ValueError(
        f"No vocab config found for organism={organism!r}, "
        f"tissue={tissue!r}, panel_name={panel_name!r}"
    )


# CellGuide lookup helpers


def _load_per_gene_db(db_path: str) -> Dict[str, Any]:
    """
    Internal helper to load the per-gene CellGuide marker database.

    `db_path` may be a Latch URI or a local path.
    """
    return load_json_lpath(db_path)


def lookup_cellguide_celltypes(
    genes: Iterable[str],
    organism: str,
    tissue: str,
    db_or_path: Union[str, Mapping[str, Any]],
) -> Dict[str, List[str]]:
    """
    For a list of genes, return CellGuide cell types for the given organism/tissue.

    Parameters
    ----------
    genes:
        Iterable of gene symbols.
    organism:
        Organism name (e.g. "Mus musculus").
    tissue:
        Tissue name (e.g. "brain").
    db_or_path:
        Either:
        - a dict-like marker DB loaded in memory
        - or a path / Latch URI string to the per-gene DB JSON.

    Returns
    -------
    dict
        Mapping gene -> list of candidate cell-type names.
    """
    if isinstance(db_or_path, str):
        db = _load_per_gene_db(db_or_path)
    else:
        db = db_or_path

    results: Dict[str, List[str]] = {}
    for g in genes:
        org_entry = db.get(g, {}).get(organism, {})
        cts = org_entry.get(tissue) or org_entry.get("All Tissues")
        if cts:
            results[g] = cts
    return results


# Cluster summarization


def summarize_clusters(
    ranked_df,
    db_path: str,
    organism: str = "Mus musculus",
    tissue: str = "brain",
    min_markers: int = 3,
    n_core: int = 10,
) -> Dict[Any, Dict[str, Any]]:
    """
    Summarize CellGuide-based annotations for each cluster.

    Parameters
    ----------
    ranked_df:
        Long-form DataFrame from `scanpy.get.rank_genes_groups_df(...)` with
        columns at least: "group", "names", "rank".
    db_path:
        Latch URI or local path to CellGuide per-gene marker DB JSON.
    organism:
        Organism name for CellGuide lookup (default "Mus musculus").
    tissue:
        Tissue name for CellGuide lookup (default "brain").
    min_markers:
        Minimum number of core markers that must support a cell type for it
        to be considered "eligible".
    n_core:
        Number of top-ranked markers per cluster to use as "core markers".

    Returns
    -------
    dict
        Mapping cluster -> summary dict with keys:
        - "core_markers"
        - "most_common_cell_type"
        - "cell_type_counts"
        - "markers_for_most_common_cell_type"
    """
    # Load DB once per call
    db = _load_per_gene_db(db_path)

    def _lookup_cellguide_celltypes_local(genes: Iterable[str]) -> Dict[str, List[str]]:
        results: Dict[str, List[str]] = {}
        for g in genes:
            org_entry = db.get(g, {}).get(organism, {})
            cts = org_entry.get(tissue) or org_entry.get("All Tissues")
            if cts:
                results[g] = cts
        return results

    summary: Dict[Any, Dict[str, Any]] = {}

    # Iterate over clusters that actually have DGE results
    for c in sorted(ranked_df["group"].unique()):
        g = ranked_df[ranked_df["group"] == c]
        if g.empty:
            summary[c] = {
                "core_markers": [],
                "most_common_cell_type": [],
                "cell_type_counts": {},
                "markers_for_most_common_cell_type": [],
            }
            continue

        # Use top n_core markers per cluster
        g = g.sort_values("rank")
        core_markers: List[str] = g["names"].head(n_core).tolist()

        lookup = _lookup_cellguide_celltypes_local(core_markers)

        # If none of the core markers exist in CellGuide
        if not lookup:
            summary[c] = {
                "core_markers": core_markers,
                "most_common_cell_type": [],
                "cell_type_counts": {},
                "markers_for_most_common_cell_type": [],
            }
            continue

        # Count how many core markers support each cell type
        counter: Counter = Counter(ct for v in lookup.values() for ct in v)

        # Only consider cell types supported by at least min_markers core markers
        eligible = {ct: n for ct, n in counter.items() if n >= min_markers}
        if not eligible:
            summary[c] = {
                "core_markers": core_markers,
                "most_common_cell_type": [],
                "cell_type_counts": dict(counter),
                "markers_for_most_common_cell_type": [],
            }
            continue

        max_support = max(eligible.values())
        top_cts = [ct for ct, n in eligible.items() if n == max_support]

        # Markers that support at least one of the top cell types
        top_markers = [
            gene for gene, cts in lookup.items() if any(ct in top_cts for ct in cts)
        ]

        summary[c] = {
            "core_markers": core_markers,
            "most_common_cell_type": top_cts,
            "cell_type_counts": dict(counter),
            "markers_for_most_common_cell_type": top_markers,
        }

    return summary
