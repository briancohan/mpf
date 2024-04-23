import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from mpf import (
    data,
    theme,  # noqa: F401
)
from mpf.config import Config
from mpf.graph import utils


# MARK: color_distribution
def color_distribution(footwear: pd.DataFrame, threshold: int = 2, **kwargs) -> go.Figure:
    cols = [Config.SECTION, Config.TYPE, Config.COLOR]
    _df = footwear.copy()[cols]
    _df = _df[_df[Config.COLOR] != "nan"]

    _df = utils.fix_separate_as_found(_df)
    _df = utils.fix_footwear_type(_df)

    _df[Config.COLOR] = _df[Config.COLOR].str.replace("/", "&")
    _df = _df.groupby(cols, observed=True).size().reset_index(name="Count")

    _df = _df[~_df[Config.COLOR].str.contains("&")]

    included = _df[_df["Count"] >= threshold]
    excluded = _df[_df["Count"] < threshold]
    ex_reported = len(excluded[excluded[Config.SECTION] == Config.REPORTED])
    ex_found = len(excluded[excluded[Config.SECTION] == Config.FOUND])

    fig = px.bar(
        included,
        x="Count",
        y=Config.COLOR,
        color=Config.TYPE,
        facet_col=Config.SECTION,
        text_auto=True,
        height=30 * len(included[Config.COLOR].unique()),
        category_orders={
            Config.COLOR: (
                included.groupby(Config.COLOR).sum().sort_values("Count", ascending=False).index
            ),
            Config.SECTION: [Config.REPORTED, Config.FOUND],
        },
    )
    utils.fix_facet_labels(fig)
    for ax, num in zip(["x", "x2"], [ex_reported, ex_found]):
        fig.add_annotation(
            x=0.95,
            y=0.05,
            xref=f"{ax} domain",
            yref="y domain",
            xanchor="right",
            text=f"{num} Colors reported less than {threshold} times",
            showarrow=False,
        )

    fig.update_traces(textangle=0)
    utils.fix_left_margin(fig, included[Config.COLOR])
    utils.put_legend_inside_subplot(fig, 0.98, 0.20)
    fig.layout.yaxis.title = ""

    return fig


# MARK: color_accuracy
def color_accuracy(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    _df = footwear.copy()[[Config.ID, Config.SECTION, Config.COLOR]]
    _df = utils.fix_separate_as_found(_df)

    _df = (
        _df[_df[Config.COLOR] != "nan"]
        .pivot_table(
            index=Config.ID,
            columns=Config.SECTION,
            values=Config.COLOR,
            aggfunc="first",
        )
        .dropna()
    )

    _df["Match"] = [
        data.correct_color(reported=reported, found=found)
        for reported, found in zip(_df[Config.REPORTED], _df[Config.FOUND])
    ]

    _df = _df[~_df.Match].reset_index()[[Config.ID, Config.REPORTED, Config.FOUND]]

    fig = go.Figure(
        data=[
            go.Table(
                header={"values": _df.columns},
                cells={"values": _df.T.values},
            ),
        ],
    )
    fig.update_layout()

    return fig
