import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from . import theme  # # noqa: F401
from . import data


def events_by_state(df: pd.DataFrame) -> go.Figure:
    col = "State"
    _df = data.get_value_counts(df, col)

    fig = px.choropleth(
        _df,
        locations=col,
        color="Count",
        locationmode="USA-states",
        scope="usa",
        height=600,
    )

    for row in _df.itertuples():
        fig.add_trace(
            go.Scattergeo(
                locations=[row.State],
                text=[row.Count],
                locationmode="USA-states",
                mode="text",
                textfont=dict(
                    color="black" if row.Count < _df.Count.mean() else "white", size=16
                ),
                showlegend=False,
            )
        )
    return fig


def events_by_category(df: pd.DataFrame) -> go.Figure:
    col = "LPB"
    _df = data.get_value_counts(df, col)
    _df = _df[~(_df[col] == "")].reset_index()

    fig = px.bar(
        _df,
        x="Count",
        y=col,
        orientation="h",
        text="Count",
        category_orders={col: _df.sort_values("Count")[col]},
        labels={
            col: "Lost Person Behavior Category",
            "Count": "Number of Cases",
        },
        height=30 * len(_df),
    )
    standoff = 174
    fig.update_layout(margin_l=standoff, yaxis_title_standoff=standoff)
    fig.update_traces(textposition="outside")
    return fig


def events_by_date(df: pd.DataFrame) -> go.Figure:
    col = "Date"
    _df = data.get_value_counts(df, col)

    fig = px.strip(
        _df,
        x=col,
        height=400,
    )
    return fig
