import plotnine as gg
import polars as pl
import math


def square_subplot_shape(n_features: int) -> tuple[int, int]:
    """
    Return (n_rows, n_cols) that is as square as possible and large
    enough to hold n_features subplots.
    """
    if n_features <= 0:
        return (1, 1)

    # Start with the integer closest to the square root
    cols = math.ceil(math.sqrt(n_features))
    rows = math.ceil(n_features / cols)

    # Sometimes trimming one column makes it more square
    if cols > 1 and (cols - 1) * rows >= n_features:
        cols -= 1

    return rows, cols


def plot_amplicon_anchors(
    positions: pl.DataFrame, sample_name: str, title: str, prefix: str
):
    n_features = positions.select("chrom").unique().shape[0]
    n_row, n_col = square_subplot_shape(n_features)
    plot = (
        gg.ggplot(positions)
        + gg.aes(x="start", y="reads", color="mean_mapq")
        + gg.geom_point(size=0.5)
        + gg.facet_wrap("chrom", ncol=n_col)
        + gg.theme(figure_size=(1.5 + 2 * n_col, 1 + 1.5 * n_row))
        + gg.scale_color_continuous("turbo")
        + gg.ggtitle(f"{title}\n{sample_name}")
        + gg.scale_y_log10()
        + gg.xlab("Alignment start position")
    )
    plot.save(f"{prefix}_alignment_distribution.png")
