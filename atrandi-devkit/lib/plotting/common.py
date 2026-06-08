from upsetplot import from_memberships, UpSet
import matplotlib.pyplot as plt
from matplotlib import rcParams
import polars as pl
from typing import List
from lib.common_const import READS, label_for, FRACTION


def export_upset_data_csv(
    bool_lf: pl.LazyFrame, sample_name: str, prefix: str, min_fraction: float = 0.01
) -> str:
    out_path = f"{prefix}_upset_data.csv"
    bool_lf.with_columns(
        (pl.col(READS) / pl.sum(READS)).alias(FRACTION), sample_name=pl.lit(sample_name)
    ).sort(FRACTION, descending=True).sink_csv(out_path)
    return out_path


def convert_df_to_upset_data(df: pl.DataFrame) -> tuple[list[list], list]:
    """Convert a boolean dataframe to an upsetplot compatible format

    Args:
        df (pl.DataFrame): boolean df of whitelisted barcodes

    Returns:
        Tuple[list, list]: List of groups, list of read counts
    """
    col_indexes = df.columns
    col_indexes.remove(READS)
    final_list: list[list] = []
    read_counts = []
    for i in df.iter_rows():
        value = i[-1]
        current_list = []
        for index, j in enumerate(i):
            if index > len(col_indexes):
                if i[index] > 0:
                    continue
            if j is True:
                current_list.append(col_indexes[index])

        final_list.append(current_list)
        read_counts.append(value)
    return final_list, read_counts


def convert_membership_names(memberships: list[list]) -> list[list]:
    """Tries to translate variables to human readable names for upset memberships
    Defaults to the variable name if HUMAN_READABLE_NAMES does not have the required entry

    Args:
        memberships (list[list]): variable memberships

    Returns:
        list[list]: Human readable memberships
    """
    new_memberships = []
    for group in memberships:
        new_group = []
        for element in group:
            new_element = label_for(key=element)
            new_group.append(new_element)
        new_memberships.append(new_group)
    return new_memberships


def plot_generic_upset_plot(
    bool_count: pl.DataFrame,
    sample_name: str,
    title: str,
    modularity: str,
    discarded_members: List[str] = [],
    min_pct_show: int = 1,
):
    """Plot an upset plot from a generic boolean counted lazyframe

    Args:
        bool_count (pl.LazyFrame): Columns are flags, rows are true/false, the last column is the read count for he conditions in the row.
        sample_name (str): sample name
        sample_out (Path): subfolder if needed
        title (str): Title of the plot except the sample name
    """
    ids = bool_count.columns
    if READS in ids:
        ids.remove(READS)
    filtered_ids = [i for i in ids if i not in discarded_members]
    rcParams["font.size"] = 8
    memberships, read_counts = convert_df_to_upset_data(bool_count)
    memberships_hrn = convert_membership_names(memberships=memberships)
    hrn_ids = [label_for(i) for i in filtered_ids]
    upset_data = from_memberships(memberships=memberships_hrn, data=read_counts)
    upset = UpSet(upset_data, show_percentages=True, min_subset_size=f"{min_pct_show}%")
    upset.style_subsets(
        present=hrn_ids,
        facecolor="green",
        label="Usable",
    )
    upset.plot()
    plt.suptitle(f"{title}\n{sample_name}")
    plt.show()
    output_path = f"{modularity}_upset_plot.png"
    plt.savefig(output_path, dpi=120)
