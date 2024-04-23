import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from mpf import theme  # noqa: F401
from mpf.config import Config, FootwearSubtype
from mpf.graph import utils


# MARK: _mixed_ids
def _mixed_ids(df: pd.DataFrame, section: str) -> list[int]:
    """Find IDs that have multiple rows."""
    counts = (
        df[df[Config.SECTION] == section]
        .groupby(Config.ID)
        .size()
        .reset_index()
        .rename(columns={0: "Count"})
        .sort_values("Count", ascending=False)
    )
    return sorted(counts[counts["Count"] > 1][Config.ID].values)


# MARK: footwear_type_summary
def footwear_type_summary(
    footwear: pd.DataFrame,
    perc: bool = False,
    **kwargs,
) -> go.Figure:
    """Heatmap showing reported footwear and how it translates to found footwear.

    Separate is treated as found.
    """
    _df = footwear.copy()[[Config.ID, Config.SECTION, Config.TYPE, Config.SUBTYPE]].dropna()
    _df = utils.promote_subtypes(_df, [FootwearSubtype.MINIMAL])
    _df = _df[_df[Config.TYPE] != "nan"]

    _df = utils.fix_footwear_type(_df, include_minimal=True)
    _df = utils.fix_separate_as_found(_df)

    # Identify Mixed
    for section in [Config.REPORTED, Config.FOUND]:
        mask1 = _df[Config.ID].isin(_mixed_ids(_df, section))
        mask2 = _df[Config.SECTION] == section
        _df.loc[mask1 & mask2, Config.TYPE] = Config.MIXED
    _df = _df.drop_duplicates()

    # Found and Reported by ID
    _df = _df.pivot_table(
        index=Config.ID,
        columns=Config.SECTION,
        values=Config.TYPE,
        aggfunc="first",
    ).dropna()

    print(_df[_df.index == 20])
    _df = (
        _df.value_counts()
        .reset_index()
        .pivot_table(index=Config.FOUND, columns=Config.REPORTED, values="count")
        .fillna(0)
    )

    if perc:
        _df = _df.div(_df.sum().sum()).round(4) * 100

    print(_df)

    fig = px.imshow(
        _df.T.values,
        text_auto=True,
        labels={
            "x": "Found Footwear",
            "y": "Reported Footwear",
            "color": Config.PERC if perc else Config.COUNT,
        },
        x=list(_df.columns),
        y=list(_df.index),
    )

    fig.update_xaxes(side="top")
    fig.data[0]["z"][np.where(fig.data[0]["z"] == 0)] = np.nan
    utils.fix_left_margin(fig, _df.index, standoff=15)

    return fig


# MARK: footwear_type_summary_perc
def footwear_type_summary_perc(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    return footwear_type_summary(footwear, perc=True)
