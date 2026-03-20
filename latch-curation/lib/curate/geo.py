from pathlib import Path
from textwrap import dedent
from tempfile import TemporaryDirectory
import traceback
import re

import requests
from lxml import html
import pandas as pd
from pysradb.sraweb import SRAweb
import GEOparse


_sradb = SRAweb()
_srp_cache: dict[str, pd.DataFrame] = {}


def gsm_to_gse(gsm_id: str) -> str | None:
    """GSM sample ID → parent GSE series ID. Returns None if not found.

    Call this first if user provides a GSM. All other functions expect GSE.
    Example: gsm_to_gse("GSM2177186") → "GSE81903"
    """
    try:
        df = _sradb.gsm_to_gse([gsm_id])
        if df.shape[0] >= 1 and "study_alias" in df.columns:
            return df["study_alias"].iloc[0]
    except Exception:
        pass
    return None


def get_subseries_ids(gse_id: str) -> list[str]:
    with TemporaryDirectory() as tmp:
        gse = GEOparse.get_GEO(geo=gse_id, destdir=tmp)
    rels = gse.metadata.get("relation", [])
    pat = re.compile(r"SuperSeries of: (GSE\d+)", flags=re.IGNORECASE)
    return [m.group(1) for r in rels for m in [pat.match(r)] if m]


def _df_to_str(df: pd.DataFrame | None) -> str:
    if df is None or df.empty:
        return ""
    return df.to_string()


def download_gse_metadata(gse_id: str) -> pd.DataFrame:
    with TemporaryDirectory() as tmp:
        gse = GEOparse.get_GEO(geo=gse_id, destdir=tmp)

    all_keys = set()
    for gsm in gse.gsms.values():
        all_keys.update(gsm.metadata.keys())
    all_keys = sorted(list(all_keys))

    data = []
    for gsm_name, gsm in gse.gsms.items():
        row_dict = {"GSM": gsm_name}
        for key in all_keys:
            if key in gsm.metadata:
                row_dict[key] = "; ".join(gsm.metadata[key])
            else:
                row_dict[key] = ""
        data.append(row_dict)
    return pd.DataFrame(data)


def download_srp_metadata(gse_id: str) -> pd.DataFrame | None:
    try:
        df = _sradb.gse_to_srp([gse_id])
    except Exception:
        return None

    if df.shape[0] != 1 or df.columns[1] != 'study_accession':
        return None

    srp_id = df['study_accession'][0]

    if srp_id in _srp_cache:
        return _srp_cache[srp_id]

    df = _sradb.sra_metadata(srp_id, detailed=True)
    _srp_cache[srp_id] = df.copy()
    return df


def construct_study_metadata(gse_id: str) -> str:
    srp_df = None
    gse_df = None

    try:
        srp_df = download_srp_metadata(gse_id)
    except Exception:
        traceback.print_exc()

    try:
        gse_df = download_gse_metadata(gse_id)
    except Exception:
        traceback.print_exc()

    return dedent(f"""
    <srp_metadata>
    {_df_to_str(srp_df)}
    </srp_metadata>

    <gse_metadata>
    {_df_to_str(gse_df)}
    </gse_metadata>
    """).strip()


def list_gse_supplementary_files(gse_id: str) -> list[str]:
    """Preview available supplementary files for a GSE without downloading.

    Requires GSE ID. For GSM, convert first: gse_id = gsm_to_gse(gsm_id)
    Returns filenames like ["GSE12345_counts.csv.gz", "GSE12345_metadata.xlsx"]
    """
    series_dir = f"{gse_id[:-3]}nnn"
    root = f"https://ftp.ncbi.nlm.nih.gov/geo/series/{series_dir}/{gse_id}/suppl/"

    resp = requests.get(root)
    resp.raise_for_status()
    tree = html.fromstring(resp.content)
    hrefs = tree.xpath("//a/@href")

    return [h for h in hrefs if not h.endswith("/") and "vulnerability" not in h]


def download_gse_supplementary_files(gse_id: str, target_dir: Path) -> list[Path]:
    """Download all supplementary files from NCBI FTP to target_dir.

    Requires GSE ID. For GSM, convert first: gse_id = gsm_to_gse(gsm_id)
    Returns list of local Path objects for downloaded files.
    """
    series_dir = f"{gse_id[:-3]}nnn"
    root = f"https://ftp.ncbi.nlm.nih.gov/geo/series/{series_dir}/{gse_id}/suppl/"

    files = list_gse_supplementary_files(gse_id)
    target_dir = Path(target_dir)
    target_dir.mkdir(exist_ok=True, parents=True)

    downloaded = []
    for fname in files:
        url = root + fname
        dest = target_dir / fname

        print(f"Downloading {fname}...")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        downloaded.append(dest)

    print(f"Downloaded {len(downloaded)} files to {target_dir}")
    return downloaded
