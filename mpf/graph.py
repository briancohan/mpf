from itertools import chain

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp

from . import theme  # # noqa: F401
from . import data
from .config import Config


def _fix_facet_labels(fig: go.Figure) -> None:
    """Remove column name and '=' from labels."""
    for annotation in fig.layout.annotations:
        annotation.text = annotation.text.split("=")[1]


def _fix_left_margin(fig: go.Figure, data: pd.Series) -> None:
    """Fix the left margin so Y-axis title is legible."""
    standoff = 8 * max(len(str(item)) for item in data)
    fig.update_layout(margin_l=standoff, yaxis_title_standoff=standoff)


########################################
# Non Footwear Related
########################################
def events_by_state(df: pd.DataFrame) -> go.Figure:
    """Create chlorpleth map showing data origins."""
    col = Config.STATE
    _df = data.get_value_counts(df, col)

    # Create Figure
    fig = px.choropleth(
        _df,
        locations=col,
        color=Config.COUNT,
        locationmode="USA-states",
        scope="usa",
        height=600,
    )

    # Annotate count in each state
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
    """Show distribution of cases by LPB category."""
    col = Config.LPB
    _df = data.get_value_counts(df, col)
    _df = _df[~(_df[col] == "")].reset_index()

    # Create Figure
    fig = px.bar(
        _df,
        x=Config.COUNT,
        y=col,
        orientation="h",
        text=Config.COUNT,
        category_orders={col: _df.sort_values(Config.COUNT)[col]},
        labels={
            col: "Lost Person Behavior Category",
            Config.COUNT: "Number of Cases",
        },
        height=30 * len(_df),  # Grow for inclusion of additional categories
    )

    _fix_left_margin(fig, df[("", Config.LPB)])
    fig.update_traces(textposition="outside")

    return fig


def events_by_date(df: pd.DataFrame) -> go.Figure:
    """Create jitter plot to show Dates use for data."""
    col = Config.DATE
    _df = data.get_value_counts(df, col)

    fig = px.strip(
        _df,
        x=col,
        height=400,
    )

    return fig


def data_completeness(df: pd.DataFrame) -> go.Figure:
    _df = data.column_comparison(df, Config.METRICS).isna().sum().reset_index()

    _df.columns = [Config.REPORT, Config.METRIC, Config.COUNT]
    _df[Config.COUNT] = len(df) - _df[Config.COUNT]

    _df = _df.pivot(index=Config.REPORT, columns=Config.METRIC, values=Config.COUNT)
    _df = _df[Config.METRICS].sort_index(ascending=False)

    fig = px.imshow(
        _df.values,
        x=_df.columns.values,
        y=_df.index.values,
        text_auto=True,
        labels={"x": Config.METRIC, "y": Config.REPORT, "color": Config.COUNT},
    )

    fig.update_xaxes(side="top")

    return fig


def data_completeness_by_type(df: pd.DataFrame) -> go.Figure:
    # TODO: Add numbers to subplots
    _df = data.column_comparison(df, Config.METRICS)

    _rdf = _df[Config.REPORTED].copy()
    _fdf = _df[Config.FOUND].copy()
    _rdf[Config.REPORT] = Config.REPORTED
    _fdf[Config.REPORT] = Config.FOUND
    _df = pd.concat([_rdf, _fdf])

    _df = (
        _df.melt(id_vars=[Config.REPORT, Config.TYPE])
        .dropna()
        .groupby([Config.REPORT, Config.TYPE, "variable"])
        .count()
        .reset_index()
        .pivot(index=[Config.REPORT, Config.TYPE], columns="variable", values="value")
    )

    titles = [Config.REPORTED, Config.FOUND]
    fig = sp.make_subplots(rows=1, cols=2, subplot_titles=titles)

    for col, report in enumerate(titles, 1):
        cur_df = _df.loc[report, :]
        fig.add_trace(
            go.Heatmap(
                x=cur_df.columns, y=cur_df.index, z=cur_df.values, coloraxis="coloraxis"
            ),
            row=1,
            col=col,
        )

    fig.update_annotations(y=1.15)
    fig.update_xaxes(side="top")

    return fig


########################################
# Footwear Type
########################################
def footwear_type_summary(df: pd.DataFrame) -> go.Figure:
    rows = Config.REPORTED
    cols = Config.FOUND

    _df = (
        data.column_comparison(df, "Type")
        .value_counts()
        .reset_index()
        .rename(columns={0: Config.COUNT})
        .replace("", Config.NA)
        .pivot_table(
            index=rows,
            columns=cols,
            values=Config.COUNT,
        )
        # .fillna(0)
    )

    fig = px.imshow(
        _df.values,
        text_auto=True,
        labels={"x": cols, "y": rows, "color": Config.COUNT},
        x=list(_df.columns),
        y=list(_df.index),
    )
    fig.update_xaxes(side="top")
    return fig


########################################
# Footwear Size
########################################
def shoe_size_distribution_by_type(df: pd.DataFrame) -> go.Figure:
    _df = data.clean_shoe_size_data(df)

    fig = px.histogram(
        _df,
        x=Config.SIZE,
        facet_row="Report",
        facet_col=Config.TYPE,
        height=700,
        width=1500,
        color=Config.SIZE_CAT,
        category_orders={
            Config.SIZE_CAT: ["m", "w", "y", "o"],
        },
        labels={
            Config.SIZE: "Shoe Size",
        },
        text_auto=True,
        nbins=int(_df[Config.SIZE].max()) * 2,
    )

    fig.update_xaxes(
        tick0=4,
        dtick=1,
        showticklabels=True,
    )

    for annotation in fig.layout.annotations:
        annotation.text = annotation.text.split("=")[1].capitalize()

    legend_names = dict(m="Mens", w="Womens", y="Youth", o="Unknown")
    for record in fig.data:
        for attr in ["legendgroup", "name", "offsetgroup"]:
            record[attr] = legend_names[record[attr]]
    fig.layout.legend.title = "Sizing Legend"

    return fig


def shoe_size_distribution_by_category(df: pd.DataFrame) -> go.Figure:
    _df = data.clean_shoe_size_data(df)

    fig = px.histogram(
        _df,
        x=Config.SIZE,
        facet_row="Report",
        facet_col=Config.SIZE_CAT,
        height=700,
        width=1200,
        color=Config.TYPE,
        category_orders={
            Config.SIZE_CAT: ["m", "w", "y", "o"],
        },
        labels={
            Config.SIZE: "Shoe Size",
        },
        text_auto=True,
        nbins=int(_df[Config.SIZE].max()) * 2,
    )

    fig.update_xaxes(
        tick0=4,
        dtick=1,
        showticklabels=True,
    )

    _fix_facet_labels(fig)
    legend_names = dict(m="Mens", w="Womens", y="Youth", o="Unknown")
    for annotation in fig.layout.annotations:
        if annotation.text in legend_names.keys():
            annotation.text = legend_names[annotation.text]
        annotation.text = annotation.text.capitalize()

    fig.layout.legend.title = "Sizing Legend"

    return fig


def shoe_size_accuracy(df: pd.DataFrame) -> go.Figure:
    _df = data.column_comparison(df, [Config.TYPE, Config.SIZE]).dropna(
        subset=[(Config.REPORTED, Config.SIZE), (Config.FOUND, Config.SIZE)]
    )
    _df.columns = ["report_type", "report_size", "found_type", "found_size"]

    # Convert to ranges and determine min/max size
    _df["report_size"] = [
        tuple(float(i) for i in value.split("-")) for value in _df["report_size"]
    ]
    sizes = list(chain.from_iterable(_df["report_size"])) + list(_df["found_size"])
    sizes = [float(size) for size in sizes]
    rng = [min(sizes) - 1, max(sizes) + 1]

    fig = go.Figure()

    for row in _df.itertuples():
        fig.add_trace(
            go.Scatter(
                x=row.report_size,
                y=[row.found_size] * len(row.report_size),
                showlegend=False,
                marker_color=Config.FOOTWEAR_COLOR[row.found_type],
            )
        )

    # Legend
    legend_key_center = 6
    legend_text_start = 7

    fig.add_trace(
        go.Scatter(
            x=[legend_key_center - 0.5, legend_key_center + 0.5],
            y=[13.5, 13.5],
            showlegend=False,
            marker_color=Config.BRAND_PRIMARY,
            line_color=Config.BRAND_PRIMARY,
        )
    )
    fig.add_annotation(
        text="Reported Range",
        x=legend_text_start,
        y=13.5,
        showarrow=False,
        xanchor="left",
    )

    legend_spacing = 0.3
    y = 13.5 - legend_spacing
    entries = [
        ("Reported Value", Config.BRAND_PRIMARY),
        ("Found: Boot", Config.FOOTWEAR_COLOR["boots"]),
        ("Found: Shoes", Config.FOOTWEAR_COLOR["shoes"]),
        ("Found: Minimal", Config.FOOTWEAR_COLOR["minimal"]),
        ("Found: Mix", Config.FOOTWEAR_COLOR["mix"]),
    ]
    for text, marker_color in entries:
        fig.add_trace(
            go.Scatter(
                x=[legend_key_center],
                y=[y],
                showlegend=False,
                marker_color=marker_color,
            )
        )
        fig.add_annotation(
            text=text, x=legend_text_start, y=y, showarrow=False, xanchor="left"
        )
        y -= legend_spacing

    fig.add_shape(type="rect", x0=5, x1=9, y0=y, y1=13.5 + legend_spacing)

    # Add Match Lines and Error Ranges
    fig.add_shape(
        type="line",
        line=dict(color="black", dash="dot"),
        xref="x",
        x0=rng[0],
        x1=rng[1],
        yref="y",
        y0=rng[0],
        y1=rng[1],
    )
    for offset in [0.5, 1.0]:
        fig.add_trace(
            go.Scatter(
                x=[rng[0] - offset, rng[1] - offset, rng[1] + offset, rng[0] + offset],
                y=[rng[0], rng[1], rng[1], rng[0]],
                fill="toself",
                line=dict(width=0),
                marker=None,
                showlegend=False,
                fillcolor="#788d64",
                opacity=0.25,
            )
        )

    # Error Range Annotations
    annotations = [
        ("Found = Reported", 0.50, 0),
        ("Half Shoe Size Error", 0.75, 0.5),
        ("Full Shoe Size Error", 1.00, 1.0),
    ]
    for text, offset, error in annotations:
        fig.add_annotation(
            text=text,
            x=rng[0] + offset + error,
            y=rng[0] + offset,
            ay=rng[0] + offset,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            ax=rng[0] + 3,
            xanchor="left",
            arrowhead=2,
        )

    # Configure Graph
    fig.update_layout(
        height=fig.layout.width or fig.layout.template.layout.width,
    )
    fig.update_yaxes(
        range=rng,
        scaleanchor="x",
        scaleratio=1,
        title=Config.FOUND + " SHOE SIZE",
        tick0=rng[0],
        dtick=1,
    )
    fig.update_xaxes(
        title=Config.REPORTED + " SHOE SIZE",
        range=rng,
        tick0=rng[0],
        dtick=1,
    )

    return fig


########################################
# Footwear Brand
########################################
def brand_distribution(df: pd.DataFrame) -> go.Figure:
    _df = data.column_comparison(df, [Config.TYPE, Config.BRAND])

    _rdf = _df[Config.REPORTED].dropna().value_counts().reset_index()
    _fdf = _df[Config.FOUND].dropna().value_counts().reset_index()
    _rdf[Config.REPORT] = Config.REPORTED
    _fdf[Config.REPORT] = Config.FOUND
    _df = pd.concat([_rdf, _fdf])
    _df.rename(columns={0: Config.COUNT}, inplace=True)

    brand_order = (
        _df.groupby(Config.BRAND)
        .sum(numeric_only=True)
        .sort_values(Config.COUNT, ascending=False)
        .index
    )

    fig = px.bar(
        _df,
        x=Config.COUNT,
        y=Config.BRAND,
        color=Config.TYPE,
        category_orders={Config.BRAND: brand_order},
        text_auto=True,
        height=31 * len(brand_order),
        facet_col=Config.REPORT,
    )

    _fix_left_margin(fig, _df[Config.BRAND])

    return fig


def brand_accuracy(df: pd.DataFrame) -> go.Figure:
    # TODO Is this figure worth keeping?
    _df = data.column_comparison(df, [Config.TYPE, Config.BRAND]).dropna(
        subset=[(Config.REPORTED, Config.BRAND), (Config.FOUND, Config.BRAND)]
    )
    for col in [Config.TYPE, Config.BRAND]:
        _df[("MATCH", col)] = _df[(Config.REPORTED, col)] == _df[(Config.FOUND, col)]

    _df = _df[_df["MATCH"].sum(axis=1) < 2]
    _df.columns = [" - ".join(col) for col in _df.columns]
    _df

    fig = go.Figure(
        data=[
            go.Table(
                header=dict(values=_df.columns),
                cells=dict(values=_df.T.values),
            )
        ]
    )
    return fig
