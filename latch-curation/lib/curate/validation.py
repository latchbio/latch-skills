import re

import numpy as np
import scipy.sparse as sp
import anndata as ad


ENSEMBL_REGEX = re.compile(r"ENS[A-Z0-9]{0,5}G\d{11}(?:\.\d+)?$")


def validate_counts_object(adata: ad.AnnData) -> list[tuple[str, str]]:
    validation_log: list[tuple[str, str]] = []

    # latch_sample_id exists
    has_sample_id = "latch_sample_id" in adata.obs
    validation_log.append(("pass" if has_sample_id else "fail", "obs contains latch_sample_id"))

    # var index is Ensembl IDs
    matches = [bool(ENSEMBL_REGEX.match(str(x))) for x in adata.var_names]
    all_ensembl = all(matches)
    if all_ensembl:
        validation_log.append(("pass", "var index contains Ensembl IDs"))
    else:
        ex_index = matches.index(False) if False in matches else None
        validation_log.append(("fail", f"var index not all Ensembl IDs (first fail at index {ex_index})"))

    # gene_symbols exists
    has_symbols = "gene_symbols" in adata.var.columns
    validation_log.append(("pass" if has_symbols else "fail", "var contains gene_symbols"))

    # gene_symbols unique
    if has_symbols:
        symbols_unique = adata.var["gene_symbols"].is_unique
        validation_log.append(("pass" if symbols_unique else "fail", "gene_symbols are unique"))

    # obs index unique
    obs_unique = adata.obs_names.is_unique
    validation_log.append(("pass" if obs_unique else "fail", "obs index is unique"))

    # var index unique
    var_unique = adata.var_names.is_unique
    validation_log.append(("pass" if var_unique else "fail", "var index is unique"))

    # counts non-negative
    X = adata.X
    vals = X.data if sp.issparse(X) else np.asarray(X)
    non_negative = (vals >= 0).all()
    validation_log.append(("pass" if non_negative else "fail", "counts are non-negative"))

    # counts are integers
    are_integers = np.allclose(vals, vals.round())
    validation_log.append(("pass" if are_integers else "fail", "counts are integers"))

    # matrix has non-zero values
    nnz = X.nnz if sp.issparse(X) else (X != 0).sum()
    total_elements = adata.n_obs * adata.n_vars
    sparsity = 1 - (nnz / total_elements) if total_elements > 0 else 1
    validation_log.append(("pass" if nnz > 0 else "fail", f"matrix has non-zero values ({nnz} entries, {sparsity:.1%} sparse)"))

    # author_ columns not all NaN
    for col in adata.obs.columns:
        if col.startswith("author_"):
            series = adata.obs[col]
            not_all_nan = not series.isna().all()
            validation_log.append(("pass" if not_all_nan else "fail", f"{col} not all NaN"))

    return validation_log


def format_validation_report(validation_log: list[tuple[str, str]]) -> str:
    lines = []
    for status, msg in validation_log:
        icon = "✅" if status == "pass" else "❌"
        lines.append(f"{icon} {msg}")
    return "\n".join(lines)


def all_checks_passed(validation_log: list[tuple[str, str]]) -> bool:
    return all(status == "pass" for status, _ in validation_log)
