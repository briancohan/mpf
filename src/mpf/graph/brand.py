import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from mpf import theme  # noqa: F401
from mpf.config import Config
from mpf.graph import utils


# MARK: _brand_distribution
def _brand_distribution(
    footwear: pd.DataFrame,
    threshold: int = 2,
    horizontal: bool = True,
) -> go.Figure:
    """Show distribution of brands in reported and found footwear."""
    cols = [Config.TYPE, Config.SECTION, Config.BRAND]
    _df = footwear.copy()[cols]

    _df = utils.fix_footwear_type(_df)
    _df = utils.fix_separate_as_found(_df)

    # Prep data
    _df = _df.dropna().groupby(cols, observed=True).size().reset_index(name="Count")
    included = (
        _df[_df["Count"] >= threshold]
        .sort_values(Config.TYPE, ascending=False)
        .sort_values("Count", ascending=True)
    )

    # Get excluded counts
    excluded = _df[_df["Count"] < threshold]
    ex_reported = len(excluded[excluded[Config.SECTION] == Config.REPORTED])
    ex_found = len(excluded[excluded[Config.SECTION] == Config.FOUND])

    # Build graph
    fig = px.bar(
        included,
        x="Count" if horizontal else Config.BRAND,
        y=Config.BRAND if horizontal else "Count",
        color=Config.TYPE,
        text_auto=True,
        facet_col=Config.SECTION,
        height=30 * len(included[Config.BRAND].unique()) if horizontal else 500,
        category_orders={
            Config.SECTION: [Config.REPORTED, Config.FOUND],
            Config.BRAND: (
                included.groupby(Config.BRAND).sum().sort_values("Count", ascending=False).index
            ),
        },
        labels={
            Config.BRAND: "",
        },
    )

    utils.fix_facet_labels(fig)
    # Annotate excluded counts "# brands reported less than # times"
    for ax, num in zip(["x", "x2"], [ex_reported, ex_found]):
        if not num:
            continue
        fig.add_annotation(
            x=0.95 if horizontal else 0.15,
            y=0.05 if horizontal else 0.95,
            xref=f"{ax} domain",
            yref="y domain",
            xanchor="right" if horizontal else "left",
            text=f"{num} brands reported less than {threshold} times",
            showarrow=False,
        )

    fig.update_traces(textangle=0)
    if horizontal:
        utils.fix_left_margin(fig, included[Config.BRAND])
    else:
        utils.fix_bottom_margin(fig, included[Config.BRAND])
    utils.put_legend_inside_subplot(
        fig,
        x=0.99,
        y=0.25 if horizontal else 0.75,
    )

    return fig


# MARK: brand_distribution_gte2_horiz
def brand_distribution_gte2_horiz(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    return _brand_distribution(footwear=footwear, threshold=2, horizontal=True)


# MARK: brand_distribution_gte2_vert
def brand_distribution_gte2_vert(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    return _brand_distribution(footwear=footwear, threshold=2, horizontal=False)


# MARK: brand_accuracy
def brand_accuracy(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    """Create a table of all records where brand did not match"""
    _df = (
        utils.fix_separate_as_found(footwear.copy())
        .pivot_table(
            index=Config.ID,
            columns=Config.SECTION,
            values=Config.BRAND,
            aggfunc="first",
        )
        .dropna()
    )

    _df = _df[_df[Config.FOUND].str.upper() != _df[Config.REPORTED].str.upper()]

    fig = go.Figure(
        data=[
            go.Table(
                header={"values": ["ID", "Reported", "Found"]},
                cells={"values": [_df.index, _df[Config.REPORTED], _df[Config.FOUND]]},
            )
        ]
    )
    return fig
