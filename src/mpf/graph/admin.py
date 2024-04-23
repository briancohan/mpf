import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp

from mpf import (
    data,
    theme,  # noqa: F401
)
from mpf.config import Config, FootwearType
from mpf.graph import utils


# MARK: reoprt_types
def report_types(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    """Determine number of datapoints by reported or found types.

    Separate and found types are combined into one column.
    Columns are converted to bool and back to int to account for a subject having multiple rows.
    """
    id_cols = [Config.ID, Config.SECTION]
    data_cols = [Config.TYPE, Config.COLOR, Config.BRAND, Config.SIZE_LO]
    _df = footwear.copy()[id_cols + data_cols]

    _df = utils.fix_separate_as_found(_df)
    _df = _df.replace("nan", np.nan)
    _df["Count"] = 4 - _df[data_cols].isna().sum(axis=1)

    _df = _df[id_cols + ["Count"]]

    _df = _df.pivot_table(index=Config.ID, columns=Config.SECTION, values="Count", aggfunc="sum")
    _df = _df.fillna(0).astype(bool)
    _df["BOTH"] = _df[Config.REPORTED] & _df[Config.FOUND]

    counts = _df.sum()
    counts["FOUND ONLY"] = counts[Config.FOUND] - counts["BOTH"]
    counts["REPORTED ONLY"] = counts[Config.REPORTED] - counts["BOTH"]

    return utils.proportional_venn(
        counts[Config.REPORTED],
        counts[Config.FOUND],
        counts["BOTH"],
        "Reported",
        "Found",
    )


# MARK: events_by_state
# TODO: Fix annotation for small states (mid-atlantic)
def events_by_state(
    admin: pd.DataFrame,
    percent: bool = False,
    **kwargs,
) -> go.Figure:
    """Create chlorpleth map showing data origins.

    The total number of domestic and international cases is annotated.
    """
    _df = (
        admin.copy()[Config.STATE]
        .astype(str)
        .value_counts()
        .reset_index()
        .rename(columns={"count": Config.COUNT})
    )
    _df[Config.PERC] = 100 * _df[Config.COUNT] / _df[Config.COUNT].sum()

    # Base Figure
    fig = px.choropleth(
        _df,
        locations=Config.STATE,
        color=Config.COUNT if not percent else Config.PERC,
        locationmode="USA-states",
        scope="usa",
        height=600,
    )

    # Annotate States
    for row in _df.itertuples():
        perc_format = ".1f" if row.Percent < 1 else ".0f"
        text = f"{row.Percent:{perc_format}}" if percent else f"{row.Count}"
        fig.add_trace(
            go.Scattergeo(
                locations=[row.State],
                text=text,
                locationmode="USA-states",
                mode="text",
                textfont={
                    "color": "black" if row.Count < _df.Count.mean() else "white",
                    "size": 14,
                },
                showlegend=False,
            ),
        )

    # # Annotate International
    col = Config.PERC if percent else Config.COUNT
    domestic = _df[_df[Config.STATE] != "nan"][col].sum()
    international = _df[_df[Config.STATE] == "nan"][col].sum()

    text = (
        "Cases: "
        f"{f'{domestic:.1f}%' if percent else domestic} Domestic, "
        f"{f'{international:.1f}%' if percent else international} International"
    )

    fig.add_annotation(
        text=text,
        xref="paper",
        yref="paper",
        x=0.5,
        y=1.05,
        showarrow=False,
        font={"size": 24},
    )

    return fig


# MARK: events_by_state_perc
def events_by_state_perc(admin: pd.DataFrame, **kwargs) -> go.Figure:
    """Create chlorpleth map showing data origins."""
    return events_by_state(admin, percent=True, **kwargs)


# MARK: events_by_category
def events_by_category(admin: pd.DataFrame, **kwargs) -> go.Figure:
    """Show distribution of cases by LPB Category.

    Each case should already be reduced to a single row.
    """
    _df = admin.copy()[Config.LPB].value_counts().reset_index()
    child_df = _df[_df[Config.LPB].str.startswith("Child")].rename(columns={"count": Config.COUNT})
    adult_df = _df[~_df[Config.LPB].str.startswith("Child")].rename(columns={"count": Config.COUNT})

    # Add a row for all children categories as one
    adult_df = pd.concat(
        [adult_df, pd.DataFrame([{"LPB": "Child", Config.COUNT: child_df.Count.sum()}])]
    )
    adult_df = adult_df.sort_values("Count", ascending=False).reset_index(drop=True)

    # Create Figure
    adult_fig = px.bar(
        adult_df,
        x=Config.COUNT,
        y=Config.LPB,
        orientation="h",
        text=Config.COUNT,
    )
    child_fig = px.bar(
        child_df,
        x=Config.COUNT,
        y=Config.LPB,
        orientation="h",
        text=Config.COUNT,
    )
    fig = sp.make_subplots(rows=1, cols=2, horizontal_spacing=0.15)
    for trace in adult_fig.data:
        fig.add_trace(trace, row=1, col=1)
    for trace in child_fig.data:
        fig.add_trace(trace, row=1, col=2)

    utils.fix_left_margin(fig, admin[Config.LPB])
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis_categoryorder="total ascending",
        yaxis2_categoryorder="total ascending",
        xaxis_range=[0, adult_df.Count.max() * 1.1],
        xaxis2_range=[0, child_df.Count.max() * 1.1],
        height=35 * len(adult_df),  # Grow for inclusion of additional categories
    )
    return fig


# MARK: events_by_category_unshod
def events_by_category_unshod(
    admin: pd.DataFrame,
    footwear: pd.DataFrame,
) -> go.Figure:
    """Show distribution of cases by LPB category only showing unshod cases."""
    unshod_ids = footwear.copy()[footwear[Config.TYPE] == FootwearType.UNSHOD.name.title()].index
    _df = (
        admin[admin[Config.ID].isin(unshod_ids)][Config.LPB]
        .value_counts()
        .reset_index()
        .rename(columns={"count": Config.COUNT})
    )
    _df = _df[_df[Config.COUNT] > 0]

    counts = (
        admin.copy()[Config.LPB].value_counts().reset_index().rename(columns={"count": "Total"})
    )
    _df = _df.merge(counts, left_on=Config.LPB, right_on=Config.LPB)
    _df[Config.PERC] = round(100 * _df[Config.COUNT] / _df["Total"], 1)

    order = _df.sort_values(Config.COUNT)[Config.LPB].values.tolist()

    c_fig = px.bar(
        _df,
        x=Config.COUNT,
        y=Config.LPB,
        orientation="h",
        text=Config.COUNT,
        height=30 * len(_df),
    )
    p_fig = px.bar(
        _df,
        x=Config.PERC,
        y=Config.LPB,
        orientation="h",
        text=Config.PERC,
        height=30 * len(_df),
    )
    fig = sp.make_subplots(rows=1, cols=2, horizontal_spacing=0.05, shared_yaxes=True)
    for trace in c_fig.data:
        fig.add_trace(trace, row=1, col=1)
    for trace in p_fig.data:
        fig.add_trace(trace, row=1, col=2)

    utils.fix_left_margin(fig, admin[Config.LPB])
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis={
            "categoryorder": "array",
            "categoryarray": order,
        },
        yaxis2={
            "categoryorder": "array",
            "categoryarray": order,
        },
        xaxis={
            "range": [0, _df[Config.COUNT].max() * 1.1],
            "title": Config.COUNT,
        },
        xaxis2={
            "range": [0, _df[Config.PERC].max() * 1.1],
            "title": Config.PERC,
        },
        height=35 * len(_df),  # Grow for inclusion of additional categories
    )

    return fig


# MARK: events_by_date
def events_by_date(admin: pd.DataFrame, **kwargs) -> go.Figure:
    """Create jitter plot to show Dates use for data."""
    fig = px.strip(
        admin.copy(),
        x=Config.DATE,
        height=400,
        facet_col_spacing=0,
    )
    fig.layout.xaxis.title = "Year"
    fig.update_traces(width=1)
    fig.update_layout(bargap=0)
    return fig


# MARK: _data_completeness_item
def _data_completeness_item(df: pd.DataFrame, column: str) -> dict[str, int]:
    """Calculate data completeness for a single metric.

    returns a dictionary with the number of times a metric was reported, found, or both.
    """
    _df = (
        df.pivot_table(columns=Config.SECTION, index=Config.ID, values=column, aggfunc="count")
        .fillna(0)
        .astype(bool)
    )
    _df["BOTH"] = False
    _df.loc[_df[Config.REPORTED] & _df[Config.FOUND], "BOTH"] = True

    return _df.sum().to_dict()


# MARK: data_completeness
def data_completeness(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    """Create heatmap showing how many data points we have for each metric.

    Metrics: Type, Color, Brand, Size
    This shows how many times a metric was reported, found, or both.
    """
    # Grab the columns we need
    _df = footwear.copy()[
        [
            Config.ID,
            Config.SECTION,
            Config.TYPE,
            Config.BRAND,
            Config.COLOR,
            Config.SIZE_LO,
            Config.SIZE_HI,
        ]
    ]
    # Change column name for display
    _df = _df.rename(columns={Config.SIZE_LO: Config.SIZE})

    # Separate and Found are both found footwear
    _df = utils.fix_separate_as_found(_df)
    # Calculate stats for each column
    data = pd.DataFrame(
        {
            col: _data_completeness_item(_df, col)
            for col in [Config.TYPE, Config.COLOR, Config.BRAND, Config.SIZE]
        }
    )

    # Set ordering for graphic
    data.index = pd.Categorical(
        data.index,
        categories=[Config.REPORTED, Config.FOUND, "BOTH", Config.SIZE],
        ordered=True,
    )
    data = data.sort_index()

    fig = px.imshow(
        data.values,
        x=data.columns.values,
        y=data.index.values,
        text_auto=True,
        labels={"x": "Data Metric", "color": Config.COUNT},
    )

    fig.update_xaxes(side="top")
    fig.update_yaxes(title="")

    return fig


# MARK: data_completeness_by_type
def data_completeness_by_type(footwear: pd.DataFrame, perc: bool = False, **kwargs) -> go.Figure:
    """Create heatmap showing how many data points we have for each metric by type.

    Metrics: Color, Brand, Size (Type is used for rows)
    """
    cols = [Config.TYPE, Config.BRAND, Config.COLOR, Config.SIZE_LO]
    data = {
        Config.REPORTED: footwear.copy()[footwear[Config.SECTION] == Config.REPORTED],
        Config.FOUND: footwear.copy()[footwear[Config.SECTION] != Config.REPORTED],
    }

    for k, v in data.items():
        _df = v[cols].groupby(Config.TYPE, observed=False).count()
        # Exclude Other
        if FootwearType.OTHER.name.title() in _df.index:
            _df = _df.drop(index=FootwearType.OTHER.name.title())
        _df = _df.rename(columns={Config.SIZE_LO: Config.SIZE})
        _df = _df.drop(index="nan", errors="ignore")
        data[k] = _df

    # Determine custom order so most common report is at the top
    type_order = (
        pd.concat([data[Config.REPORTED].sum(axis=1), data[Config.FOUND].sum(axis=1)])
        .reset_index()
        .groupby(Config.TYPE)
        .sum()
        .sort_values(0, ascending=True)
        .index
    )

    for k, v in data.items():
        v.index = pd.Categorical(v.index, categories=type_order, ordered=True)
        data[k] = v

    reported = px.imshow(
        data[Config.REPORTED].sort_index(),
        x=data[Config.REPORTED].sort_index().columns,
        y=data[Config.REPORTED].sort_index().index,
        text_auto=True,
    )
    found = px.imshow(
        data[Config.FOUND].sort_index(),
        x=data[Config.FOUND].sort_index().columns,
        y=data[Config.FOUND].sort_index().index,
        text_auto=True,
    )

    titles = ["Reported Footwear", "Found Footwear"]
    fig = sp.make_subplots(rows=1, cols=2, subplot_titles=titles)
    fig.add_trace(reported.data[0], row=1, col=1)
    fig.add_trace(found.data[0], row=1, col=2)

    fig.update_annotations(y=1.15)
    fig.update_xaxes(side="top")

    return fig


# # MARK: overall_accuracy
def overall_accuracy(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    _df = pd.concat(
        [
            pd.DataFrame(data.correct_brand_summary(footwear=footwear)),
            pd.DataFrame(data.correct_color_summary(footwear=footwear)),
            pd.DataFrame(data.correct_size_summary(footwear=footwear)),
            pd.DataFrame(data.correct_type_summary(footwear=footwear)),
        ]
    )

    _df["Correct Perc"] = 0
    _df["Incorrect Perc"] = 0
    for metric in _df["Metric"].unique():
        mask = _df["Metric"] == metric
        total_records = _df[mask][["Correct", "Incorrect"]].sum().sum()

        _df.loc[mask, "Correct Perc"] = _df.loc[mask, "Correct"] / total_records
        _df.loc[mask, "Incorrect Perc"] = _df.loc[mask, "Incorrect"] / total_records

    for col in ["Correct Perc", "Incorrect Perc"]:
        _df[col] = (_df[col] * 100).round(2)

    df_v = _df.melt(id_vars=["Metric", "Report"], value_vars=["Correct", "Incorrect"])
    df_p = _df.melt(id_vars=["Metric", "Report"], value_vars=["Correct Perc", "Incorrect Perc"])

    opts = {
        "x": "value",
        "y": "Metric",
        "color": "variable",
        "pattern_shape": "Report",
        "pattern_shape_map": {Config.FOUND: "", Config.SEPARATE: "/"},
        "orientation": "h",
        "text_auto": True,
        "category_orders": {"Metric": [Config.TYPE, Config.COLOR, Config.BRAND, Config.SIZE]},
    }
    fig_v = px.bar(df_v, **opts)
    fig_p = px.bar(df_p, **opts)
    fig_v.update_layout(showlegend=False)

    fig = sp.make_subplots(rows=1, cols=2, column_titles=["By Value", "By Percentage"])
    for item in fig_v.data:
        fig.add_trace(item, row=1, col=1)
    for item in fig_p.data:
        fig.add_trace(item, row=1, col=2)

    for trace in fig.data[len(fig.data) // 2 :]:
        trace.showlegend = False

    fig.update_traces(
        marker={
            "pattern": {
                "fillmode": "overlay",
                "fgcolor": "#ddd",
                "size": 12,
            },
        },
    )
    fig.update_layout(
        barmode="stack",
        xaxis2={  # make incorrect separate number visible
            "range": [0, 110],
            "tick0": 0,
            "dtick": 25,
        },
    )

    return fig
