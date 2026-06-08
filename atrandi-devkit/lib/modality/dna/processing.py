import polars as pl
import pysam
from pysam.libcalignmentfile import IteratorColumnRegion
from typing import Final
from lib.common_const import READS, BARCODE, READ_NAME

CHROM: Final[str] = "chrom"
REF: Final[str] = "REF"
ALT: Final[str] = "ALT"
POS: Final[str] = "POS"
QUAL: Final[str] = "QUAL"
VAR_FEATURE: Final[str] = "var_feature"
FEATURE: Final[str] = "feature"
SNP_FEATURE: Final[str] = "snp_feature"
BASES: Final[str] = "bases"
DP: Final[str] = "DP"
READ_BASE: Final[str] = "read_base"
REF_BASE: Final[str] = "ref_base"
VARIANT_STATUS: Final[str] = "variant_status"
VARIANT_NAME: Final[str] = "variant_name"


def pileup_truncated(bam, contig, start, stop, max_depth, min_base_quality):
    """
    Obtain Pysam columns only at selected region
    """
    _, rtid, rstart, rstop = bam.parse_region(contig, start, stop)
    yield from IteratorColumnRegion(
        bam,
        tid=rtid,
        start=rstart,
        stop=rstop,
        truncate=True,
        max_depth=max_depth,
        min_base_quality=min_base_quality,
    )


# TODO: get to actually only pileup on one position
# TODO: do a pileup by cell
def get_pileup_results(
    feature: str,
    start: int,
    stop: int,
    samfile_handle: pysam.AlignmentFile,
    reffa_handle: pysam.FastaFile,
    max_depth: int,
    min_coverage: int = 20,
) -> pl.DataFrame | None:
    # Iterate over pileup

    results: list = []
    for pileupcolumn in pileup_truncated(
        samfile_handle,
        feature,
        start=start,
        stop=stop,
        max_depth=max_depth,
        min_base_quality=13,  # TODO: Study min_base_quality
    ):
        n = 0
        n += 1
        pos = pileupcolumn.reference_pos  # 0-based
        if pos != start:
            continue
        chrom = pileupcolumn.reference_name
        # Get reference base (1-base to 1-base inclusive fetch)
        ref_base = reffa_handle.fetch(chrom, pos, pos + 1)  # returns a string of 1 base

        # print(f"Reference base: {ref_base}")
        # print(f"\nCoverage at {chrom}:{pos+1} = {pileupcolumn.n}")
        if pileupcolumn.nsegments < min_coverage:
            continue
        for pileupread in pileupcolumn.pileups:
            if not pileupread.is_del and not pileupread.is_refskip:
                read_base = pileupread.alignment.query_sequence[
                    pileupread.query_position
                ]

                results.append(
                    [pileupread.alignment.query_name, pos, ref_base, read_base]
                )
        if len(results) == 0:
            df = None
        df = pl.DataFrame(
            results, [READ_NAME, "pos", REF_BASE, READ_BASE], orient="row"
        ).with_columns(pl.lit(feature).alias(FEATURE))
        return df


def get_all_pileups(
    selected_features: pl.DataFrame,
    samfile_handle: pysam.AlignmentFile,
    ref_handle: pysam.FastaFile,
) -> pl.DataFrame:
    all_results: list = []
    for feature, start in selected_features.rows():
        max_depth = samfile_handle.mapped
        results = get_pileup_results(
            feature,
            start,
            stop=start + 1,
            samfile_handle=samfile_handle,
            reffa_handle=ref_handle,
            max_depth=max_depth,
        )
        if results is None:
            continue
        if results.shape[0] == 0:
            continue
        all_results.append(results)
    return pl.concat(all_results)


def format_raw_snps(raw_barcoded_snps: pl.LazyFrame) -> pl.LazyFrame:
    """Group and count SNPs based on barcode, position, base.
    Create the formatting for the feature.

    Args:
        raw_barcoded_snps (pl.DataFrame): raw snps, each row is an event
        barcode_indexed (bool, optional): Is the sample . Defaults to False.

    Returns:
        pl.DataFrame: _description_
    """

    df = (
        raw_barcoded_snps.group_by(BARCODE, POS, READ_BASE, REF_BASE, FEATURE)
        .agg(pl.len().alias(READS))
        .with_columns(pl.sum(READS).over(BARCODE, POS, FEATURE).alias("total_reads"))
    )
    raw_snp = (
        df.with_columns(
            bases=pl.concat_str(pl.col(REF_BASE), pl.col(READ_BASE), separator=">")
        )
        .with_columns(pl.format("{}_{}_{}", FEATURE, POS, READ_BASE).alias(SNP_FEATURE))
        .drop(READ_BASE)
    )
    return raw_snp


def filter_snps(
    raw_snp: pl.LazyFrame,
    min_total_reads: int,
    min_fraction_homo: float,
) -> pl.LazyFrame:
    all_filtered_snps = (
        raw_snp.filter((pl.col("total_reads") > min_total_reads))
        .with_columns(
            fraction_reads=(pl.sum(READS) / pl.sum("total_reads")).over(
                BARCODE, POS, FEATURE, BASES, REF_BASE
            ),
            reads=(pl.sum(READS)).over(BARCODE, POS, FEATURE, BASES, REF_BASE),
        )
        .with_columns(
            high_fraction=(pl.col("fraction_reads") >= min_fraction_homo)
        )  # .over(BARCODE, BASES, POS))
        .sort("fraction_reads", descending=True)
        .with_columns(
            variant_status=pl.when(pl.col("high_fraction"))
            .then(pl.lit("homo"))
            .otherwise(pl.lit("hete"))
        )
        .sort(VARIANT_STATUS)
        .with_columns(
            pl.col(POS).cast(pl.String),
            variant_name=pl.when(pl.col(VARIANT_STATUS) == "homo")
            .then(pl.concat_str(pl.col(VARIANT_STATUS), pl.col(BASES)))
            .otherwise(pl.col(VARIANT_STATUS)),
        )
        .select(BARCODE, POS, FEATURE, VARIANT_NAME, REF_BASE)
        .unique()
        .with_columns(pl.len().over(BARCODE, POS, FEATURE, REF_BASE))
    )
    return all_filtered_snps
