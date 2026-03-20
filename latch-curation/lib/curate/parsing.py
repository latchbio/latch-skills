from pathlib import Path
import json
import re

import pandas as pd
import scipy.sparse as sp
from anndata import AnnData


ENSEMBL_REGEX = re.compile(r"ENS[A-Z0-9]{0,5}G\d{11}(?:\.\d+)?$")

_ensembl_map: dict[str, str] | None = None


def _get_ensembl_map() -> dict[str, str]:
    global _ensembl_map
    if _ensembl_map is None:
        map_path = Path(__file__).parent / "data" / "ensembl_map.json"
        with open(map_path) as f:
            _ensembl_map = json.load(f)
    return _ensembl_map


def is_valid_ensembl(id_: str) -> bool:
    return ENSEMBL_REGEX.fullmatch(id_) is not None


def ensembl_to_symbol(id_: str) -> str | None:
    if not is_valid_ensembl(id_):
        return None
    mapping = _get_ensembl_map()
    reverse_map = {v: k for k, v in mapping.items()}
    return reverse_map.get(id_)


def symbol_to_ensembl(sym: str) -> str | None:
    mapping = _get_ensembl_map()
    return mapping.get(sym.upper())


def convert_and_swap_symbol_index(adata: AnnData) -> AnnData:
    mapping = _get_ensembl_map()
    symbols = pd.Index(adata.var.index)
    ensembl_ids = symbols.to_series().str.upper().map(mapping)
    mask = ~ensembl_ids.isna()

    adata = adata[:, mask].copy()
    adata.var["gene_symbols"] = adata.var.index
    adata.var.index = ensembl_ids[mask]

    unique_mask = ~adata.var_names.duplicated()
    adata = adata[:, unique_mask].copy()

    return adata


def reindex_and_fill_with_zeros(
    adata: AnnData,
    new_features: pd.Index,
) -> AnnData:
    mapping = _get_ensembl_map()
    reverse_map = {v: k for k, v in mapping.items()}

    X_dense = adata.X.todense() if sp.issparse(adata.X) else adata.X
    df = pd.DataFrame(X_dense, index=adata.obs_names, columns=adata.var_names)
    df_reindexed = df.reindex(columns=new_features, fill_value=0)

    new_var = adata.var.reindex(new_features).copy()
    new_var["gene_symbols"] = new_var.index.to_series().map(reverse_map)

    return AnnData(
        X=sp.csr_matrix(df_reindexed.values),
        obs=adata.obs.copy(),
        var=new_var,
    )


def reindex_and_fill_list(adatas: list[AnnData]) -> list[AnnData]:
    union_features = pd.Index([]).union_many([ad.var.index for ad in adatas])

    mapping = _get_ensembl_map()
    reverse_map = {v: k for k, v in mapping.items()}

    symbol_map: dict[str, str] = {}
    for feature in union_features:
        if feature in reverse_map:
            symbol_map[feature] = reverse_map[feature]
        else:
            for ad in adatas:
                if feature in ad.var.index and "gene_symbols" in ad.var.columns:
                    symbol_map[feature] = ad.var.loc[feature, "gene_symbols"]
                    break

    new_adatas = []
    for ad in adatas:
        new_ad = reindex_and_fill_with_zeros(ad, union_features)
        new_adatas.append(new_ad)
    return new_adatas
