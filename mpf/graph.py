from itertools import chain

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import plotly.subplots as sp

from . import (
    data,
    theme,  # # noqa: F401
)
from .config import Config


def _fix_facet_labels(fig: go.Figure) -> None:
    """Remove column name and '=' from labels."""
    for annotation in fig.layout.annotations:
        if "=REPORTED" in annotation.text:
            annotation.text = "Reported Footwear"
        elif "=FOUND" in annotation.text:
            annotation.text = "Found Footwear"
        else:
            annotation.text = annotation.text.split("=")[1]


def _fix_left_margin(fig: go.Figure, data: pd.Series, standoff: int = 0) -> None:
    """Fix the left margin so Y-axis title is legible."""
    standoff = standoff or 8 * max(len(str(item)) for item in data)
    fig.update_layout(margin_l=standoff, yaxis_title_standoff=standoff)


def _proportional_venn(
    value1: int,
    value2: int,
    overlap: int,
    label1: str,
    label2: str,
) -> go.Figure:
    def diameter_from_area(area: int) -> float:
        return 2 * (100 * area / np.pi) ** 0.5

    d1 = diameter_from_area(value1)
    d2 = diameter_from_area(value2)

    x_shift = diameter_from_area(overlap) / 2
    max_d = max(d1, d2)  # - x_shift
    total = value1 + value2 - overlap

    circle1 = go.layout.Shape(
        type="circle",
        x0=-d1 + x_shift,
        x1=0 + x_shift,
        y0=-d1 / 2,
        y1=d1 / 2,
        fillcolor=Config.BRAND_PRIMARY,
        opacity=0.75,
    )
    circle2 = go.layout.Shape(
        type="circle",
        x0=0 - x_shift,
        x1=d2 - x_shift,
        y0=-d2 / 2,
        y1=d2 / 2,
        fillcolor=Config.BRAND_SECONDARY,
        opacity=0.75,
    )
    circle1o = go.layout.Shape(
        type="circle",
        x0=-d1 + x_shift,
        x1=0 + x_shift,
        y0=-d1 / 2,
        y1=d1 / 2,
    )
    circle2o = go.layout.Shape(
        type="circle",
        x0=0 - x_shift,
        x1=d2 - x_shift,
        y0=-d2 / 2,
        y1=d2 / 2,
    )

    annotation1 = go.layout.Annotation(
        x=-d1 / 2 - x_shift,
        y=0,
        text=f"{label1}<br>Only<br>n={value1 - overlap}<br>{(value1 - overlap) * 100 / total:.0f}%",
        showarrow=False,
        font={"size": 16},
        xanchor="left",
    )
    annotation2 = go.layout.Annotation(
        x=d2 / 2 + x_shift,
        y=0,
        text=f"{label2}<br>Only<br>n={value2 - overlap}<br>{(value2 - overlap) * 100 / total:.0f}%",
        showarrow=False,
        font={"size": 16},
        xanchor="right",
    )
    annotation3 = go.layout.Annotation(
        x=0,
        y=0,
        text=f"{label1}<br>&amp;<br>{label2}<br>n={overlap}<br>{overlap * 100 / total:.0f}%",
        showarrow=False,
        font={"size": 16},
    )

    layout = go.Layout(
        width=600,
        height=400,
        xaxis={
            "scaleanchor": "y",
            "scaleratio": 1,
            "range": [-max_d, max_d],
        },
        yaxis={
            "scaleanchor": "x",
            "scaleratio": 1,
            "range": [-max_d / 2, max_d / 2],
        },
        shapes=[circle1, circle2, circle1o, circle2o],
        annotations=[annotation1, annotation2, annotation3],
    )

    fig = go.Figure(layout=layout)
    fig.update_layout(
        xaxis={
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "showticklabels": False,
        },
        yaxis={
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "showticklabels": False,
        },
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
    return fig


########################################
# Non Footwear Related
########################################
def report_types(df: pd.DataFrame) -> go.Figure:
    reported = df["REPORTED"][["Type", "Color", "Brand", "Size"]].count(axis=1).values
    found = df["FOUND"][["Type", "Color", "Brand", "Size"]].count(axis=1).values
    both = reported * found
    both = len(both[np.where(both > 0)])
    reported = len(reported[np.where(reported > 0)])
    found = len(found[np.where(found > 0)])

    return _proportional_venn(reported, found, both, "Reported", "Found")


def events_by_state(df: pd.DataFrame, percent: bool = False) -> go.Figure:
    """Create chlorpleth map showing data origins."""
    col = Config.STATE
    _df = data.get_value_counts(df, col)

    _df = _df.assign(Percent=_df.Count / _df.Count.sum() * 100)
    _df = _df.round(1)

    value_col = "Percent" if percent else Config.COUNT

    # Create Figure
    fig = px.choropleth(
        _df,
        locations=col,
        color=value_col,
        locationmode="USA-states",
        scope="usa",
        height=600,
    )

    font_size = 14
    if "jsar" in pio.templates.default:
        font_size = Config.JSAR_FONT_SIZE

    # Annotate count in each state
    for row in _df.itertuples():
        text = f"{getattr(row, value_col)}%" if percent else f"{getattr(row, value_col)}"
        fig.add_trace(
            go.Scattergeo(
                locations=[row.State],
                text=text,
                locationmode="USA-states",
                mode="text",
                textfont={
                    "color": "black" if row.Count < _df.Count.mean() else "white",
                    "size": font_size,
                },
                showlegend=False,
            ),
        )

    return fig


def events_by_state_perc(df: pd.DataFrame) -> go.Figure:
    """Create chlorpleth map showing data origins."""
    return events_by_state(df, percent=True)


def events_by_category(df: pd.DataFrame) -> go.Figure:
    """Show distribution of cases by LPB category."""
    col = Config.LPB
    _df = data.get_value_counts(df, Config.LPB, False).replace(pd.NA, "unknown")

    child_df = _df[_df.LPB.str.startswith("child")].reset_index(drop=True)
    adult_df = _df[~_df.LPB.str.startswith("child")]
    total_children = child_df["Count"].sum()

    adult_df = pd.concat([adult_df, pd.DataFrame([{"LPB": "child", "Count": total_children}])])
    adult_df = adult_df.sort_values("Count", ascending=False).reset_index(drop=True)

    # Create Figure
    adult_fig = px.bar(
        adult_df,
        x=Config.COUNT,
        y=col,
        orientation="h",
        text=Config.COUNT,
        labels={
            col: "Lost Person Behavior Category",
        },
    )
    child_fig = px.bar(
        child_df,
        x=Config.COUNT,
        y=col,
        orientation="h",
        text=Config.COUNT,
        labels={
            col: "Lost Person Behavior Category",
        },
    )
    fig = sp.make_subplots(rows=1, cols=2, horizontal_spacing=0.15)
    for item in adult_fig.data:
        fig.add_trace(item, row=1, col=1)
    for item in child_fig.data:
        fig.add_trace(item, row=1, col=2)

    _fix_left_margin(fig, df[("", Config.LPB)])
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis_categoryorder="total ascending",
        yaxis2_categoryorder="total ascending",
        xaxis_range=[0, adult_df.Count.max() * 1.1],
        xaxis2_range=[0, child_df.Count.max() * 1.1],
        height=35 * len(adult_df),  # Grow for inclusion of additional categories
    )
    return fig


def events_by_category_unshod(df: pd.DataFrame) -> go.Figure:
    """Show distribution of cases by LPB category."""
    col = Config.LPB
    _df = df[df[(Config.FOUND, Config.TYPE)] == "unshod"][("", col)].value_counts().reset_index()

    _df.columns = [col, Config.COUNT]

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
            # Config.COUNT: "Number of Cases",
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
    fig.layout.xaxis.title = "Year"

    return fig


def data_completeness(df: pd.DataFrame) -> go.Figure:
    _df = data.column_comparison(df, Config.METRICS)
    for metric in Config.METRICS:
        counts = sum(
            [
                ~_df[(Config.REPORTED, metric)].isna(),
                ~_df[(Config.FOUND, metric)].isna(),
            ],
        )
        _df[("BOTH", metric)] = counts == 2
        _df = _df.replace(True, "included").replace(False, np.nan)

    _df = _df.isna().sum().reset_index()

    _df.columns = [Config.REPORT, Config.METRIC, Config.COUNT]
    _df[Config.COUNT] = len(df) - _df[Config.COUNT]

    _df = _df.pivot(index=Config.REPORT, columns=Config.METRIC, values=Config.COUNT)
    _df = _df[Config.METRICS].sort_index(ascending=False)
    # return _df

    fig = px.imshow(
        _df.values,
        x=_df.columns.values,
        y=_df.index.values,
        text_auto=True,
        labels={"x": Config.METRIC, "y": Config.REPORT, "color": Config.COUNT},
    )

    fig.update_xaxes(side="top")
    fig.update_yaxes(title="")

    return fig


def data_completeness_by_type(df: pd.DataFrame, show_minimal: bool = True) -> go.Figure:
    _df = data.column_comparison(df, Config.METRICS)

    if not show_minimal:
        _df = _df.replace("minimal", "shoes")

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
        .pivot(index=Config.TYPE, columns=[Config.REPORT, "variable"], values="value")
    )

    _rdf = _df[Config.REPORTED]
    r_fig = px.imshow(
        _rdf.values,
        x=_rdf.columns,
        y=_rdf.index,
        text_auto=True,
    )
    _fdf = _df[Config.FOUND]
    f_fig = px.imshow(
        _fdf.values,
        x=_fdf.columns,
        y=_fdf.index,
        text_auto=True,
    )

    titles = ["Reported Footwear", "Found Footwear"]
    fig = sp.make_subplots(rows=1, cols=2, subplot_titles=titles)

    for item in r_fig.data:
        fig.add_trace(item, row=1, col=1)
    for item in f_fig.data:
        fig.add_trace(item, row=1, col=2)

    fig.update_annotations(y=1.15)
    fig.update_xaxes(side="top")

    return fig


def data_completeness_by_type_no_minimal(df: pd.DataFrame) -> go.Figure:
    return data_completeness_by_type(df=df, show_minimal=False)


def overall_accuracy(df: pd.DataFrame, size_tolerance: float = 0.5) -> go.Figure:
    # Type Info
    type_df = data.column_comparison_no_na(df, Config.TYPE)

    # Size Info
    size_df = data.column_comparison_no_na(df, Config.SIZE, keep_type=False)
    size_df[Config.REPORTED] = [
        tuple(float(i) for i in value.split("-")) for value in size_df[Config.REPORTED]
    ]
    size_df[Config.FOUND] = size_df[Config.FOUND].astype("float")
    size_df["MATCH"] = [
        row.REPORTED[0] - size_tolerance
        <= row.FOUND  # noqa: W503
        <= row.REPORTED[-1] + size_tolerance  # noqa: W503
        for row in size_df.itertuples()
    ]

    # Color Info
    color_df = data.column_comparison_no_na(df, Config.COLOR, keep_type=False)

    color_df["MATCH"] = [
        row.REPORTED in row.FOUND or row.FOUND in row.REPORTED for row in color_df.itertuples()
    ]

    # Brand Info
    brand_df = data.column_comparison_no_na(df, Config.BRAND, keep_type=False)

    type_correct = int(sum(type_df["MATCH"].values))
    type_incorrect = len(type_df) - type_correct
    size_correct = sum(size_df["MATCH"].values)
    size_incorrect = len(size_df) - size_correct
    color_correct = sum(color_df["MATCH"].values)
    color_incorrect = len(color_df) - color_correct
    brand_correct = sum(brand_df["MATCH"].values)
    brand_incorrect = len(brand_df) - brand_correct

    _df = pd.DataFrame(
        [
            (
                Config.TYPE,
                type_correct,
                type_incorrect,
                round(type_correct * 100 / len(type_df), 0),
                round(type_incorrect * 100 / len(type_df), 0),
            ),
            (
                Config.SIZE,
                size_correct,
                size_incorrect,
                round(size_correct * 100 / len(size_df), 0),
                round(size_incorrect * 100 / len(size_df), 0),
            ),
            (
                Config.COLOR,
                color_correct,
                color_incorrect,
                round(color_correct * 100 / len(color_df), 0),
                round(color_incorrect * 100 / len(color_df), 0),
            ),
            (
                Config.BRAND,
                brand_correct,
                brand_incorrect,
                round(brand_correct * 100 / len(brand_df), 0),
                round(brand_incorrect * 100 / len(brand_df), 0),
            ),
        ],
        columns=["Metric", "Correct", "Incorrect", "% Correct", "% Incorrect"],
    )
    _df = _df.sort_values("Correct")

    opts = {
        "x": "value",
        "y": "Metric",
        "color": "variable",
        "orientation": "h",
        "text_auto": True,
        "category_orders": {"Metric": [Config.TYPE, Config.COLOR, Config.BRAND, Config.SIZE]},
    }
    fig_v = px.bar(_df[["Metric", "Correct", "Incorrect"]].melt(id_vars="Metric"), **opts)
    fig_p = px.bar(_df[["Metric", "% Correct", "% Incorrect"]].melt(id_vars="Metric"), **opts)

    fig = sp.make_subplots(rows=1, cols=2, column_titles=["By Value", "By Percentage"])
    for item in fig_v.data:
        fig.add_trace(item, row=1, col=1)
    for item in fig_p.data:
        fig.add_trace(item, row=1, col=2)

    for trace in fig.data:
        if trace.legendgroup.startswith("%"):
            trace.showlegend = False

    fig.update_layout(barmode="stack")

    return fig


########################################
# Footwear Type
########################################
def footwear_type_summary(df: pd.DataFrame, show_minimal: bool = True) -> go.Figure:
    rows = Config.REPORTED
    cols = Config.FOUND

    _df = data.column_comparison(df, "Type")
    if not show_minimal:
        _df = _df.replace("minimal", "shoes")

    _df = _df.value_counts().reset_index().rename(columns={0: Config.COUNT})
    # TODO Make this less hacky
    _df.loc[len(_df.index)] = ["mix", "mix", 0]

    _df = _df.pivot_table(
        index=rows,
        columns=cols,
        values=Config.COUNT,
    )

    fig = px.imshow(
        _df.values,
        text_auto=True,
        labels={"x": "Found Footwear", "y": "Reported Footwear", "color": Config.COUNT},
        x=list(_df.columns),
        y=list(_df.index),
    )
    fig.update_xaxes(side="top")
    fig.data[0]["z"][np.where(fig.data[0]["z"] == 0)] = np.nan
    _fix_left_margin(fig, _df.index, standoff=15)
    return fig


def footwear_type_summary_no_minimal(df: pd.DataFrame) -> go.Figure:
    return footwear_type_summary(df=df, show_minimal=False)


########################################
# Footwear Size
########################################
def _fix_size_yaxis_labels(fig: go.Figure) -> None:
    annotations = [
        annotation
        for annotation in fig.layout.annotations
        if not any(
            word.lower() in annotation.text.lower() for word in [Config.REPORTED, Config.FOUND]
        )
    ]
    fig.layout.annotations = annotations
    fig.layout.yaxis.title.text = "Found Footwear - Count"
    other_axis = len([i for i in fig.layout if i.startswith("yaxis")]) // 2 + 1
    fig.layout[f"yaxis{other_axis}"].title.text = "Reported Footwear - Count"


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

    legend_names = {"m": "Mens", "w": "Womens", "y": "Youth", "o": "Unknown"}
    for record in fig.data:
        for attr in ["legendgroup", "name", "offsetgroup"]:
            record[attr] = legend_names[record[attr]]
    fig.layout.legend.title = "Sizing Legend"
    _fix_size_yaxis_labels(fig)
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
    legend_names = {"m": "Mens", "w": "Womens", "y": "Youth", "o": "Unknown"}
    for annotation in fig.layout.annotations:
        if annotation.text in legend_names.keys():
            annotation.text = legend_names[annotation.text]
        annotation.text = annotation.text.capitalize()

    fig.layout.legend.title = "Sizing Legend"
    _fix_size_yaxis_labels(fig)
    return fig


def shoe_size_accuracy(df: pd.DataFrame) -> go.Figure:
    _df = data.column_comparison(df, [Config.TYPE, Config.SIZE]).dropna(
        subset=[(Config.REPORTED, Config.SIZE), (Config.FOUND, Config.SIZE)],
    )
    _df.columns = ["report_type", "report_size", "found_type", "found_size"]

    # Convert to ranges and determine min/max size
    _df["report_size"] = [tuple(float(i) for i in value.split("-")) for value in _df["report_size"]]
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
                marker_symbol=Config.FOOTWEAR_MARKER[row.found_type],
            ),
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
        ),
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
        ("Reported Value", Config.BRAND_PRIMARY, "circle"),
        (
            "Found: Boot",
            Config.FOOTWEAR_COLOR["boots"],
            Config.FOOTWEAR_MARKER["boots"],
        ),
        (
            "Found: Shoes",
            Config.FOOTWEAR_COLOR["shoes"],
            Config.FOOTWEAR_MARKER["shoes"],
        ),
        (
            "Found: Minimal",
            Config.FOOTWEAR_COLOR["minimal"],
            Config.FOOTWEAR_MARKER["minimal"],
        ),
        ("Found: Mix", Config.FOOTWEAR_COLOR["mix"], Config.FOOTWEAR_MARKER["mix"]),
    ]
    for text, marker_color, marker_symbol in entries:
        fig.add_trace(
            go.Scatter(
                x=[legend_key_center],
                y=[y],
                showlegend=False,
                marker_color=marker_color,
                marker_symbol=marker_symbol,
            ),
        )
        fig.add_annotation(text=text, x=legend_text_start, y=y, showarrow=False, xanchor="left")
        if "Found" not in text:
            y -= legend_spacing
        y -= legend_spacing

    fig.add_shape(type="rect", x0=5, x1=9, y0=y, y1=13.5 + legend_spacing)

    # Add Match Lines and Error Ranges
    erng = rng[0] - 1, rng[1] + 1
    fig.add_shape(
        type="line",
        line={"color": "black", "dash": "dot"},
        xref="x",
        x0=erng[0],
        x1=erng[1],
        yref="y",
        y0=erng[0],
        y1=erng[1],
    )
    for offset in [0.5, 1.0]:
        fig.add_trace(
            go.Scatter(
                x=[
                    erng[0] - offset,
                    erng[1] - offset,
                    erng[1] + offset,
                    erng[0] + offset,
                ],
                y=[erng[0], erng[1], erng[1], erng[0]],
                fill="toself",
                line={"width": 0},
                marker=None,
                showlegend=False,
                fillcolor="#788d64",
                opacity=0.25,
            ),
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
        title=Config.FOUND.title() + " Shoe Size",
        tick0=rng[0],
        dtick=1,
    )
    fig.update_xaxes(
        title=Config.REPORTED.title() + " Shoe Size",
        range=rng,
        tick0=rng[0],
        dtick=1,
    )

    return fig


########################################
# Footwear Brand
########################################
def brand_distribution_gte1(
    df: pd.DataFrame,
    threshold: int = 1,
    height: int = 35,
    horizontal: bool = True,
) -> go.Figure:
    _df = data.column_comparison(df, [Config.TYPE, Config.BRAND])

    # TODO remove "skechers + appalacian trail"
    _df = _df[["+" not in str(value) for value in _df[Config.REPORTED, Config.BRAND]]]

    _rdf = _df[Config.REPORTED].dropna().value_counts().reset_index()
    _fdf = _df[Config.FOUND].dropna().value_counts().reset_index()
    _rdf[Config.REPORT] = Config.REPORTED
    _fdf[Config.REPORT] = Config.FOUND
    _df = pd.concat([_rdf, _fdf])
    keep = _df.groupby(Config.BRAND).sum(numeric_only=True)
    keep.columns = [Config.COUNT]
    keep = keep[keep[Config.COUNT] > threshold].reset_index()[Config.BRAND].values
    _df = _df[_df[Config.BRAND].isin(keep)]

    _df.rename(columns={0: Config.COUNT}, inplace=True)

    brand_order = (
        _df.groupby(Config.BRAND)
        .sum(numeric_only=True)
        .sort_values(Config.COUNT, ascending=False)
        .index
    )

    if horizontal:
        fig = px.bar(
            _df,
            x=Config.COUNT,
            y=Config.BRAND,
            color=Config.TYPE,
            category_orders={Config.BRAND: brand_order},
            text_auto=True,
            height=height * len(brand_order),
            facet_col=Config.REPORT,
        )
        _fix_left_margin(fig, _df[Config.BRAND])
    else:
        fig = px.bar(
            _df,
            x=Config.BRAND,
            y=Config.COUNT,
            color=Config.TYPE,
            category_orders={Config.BRAND: brand_order},
            text_auto=True,
            height=height,
            facet_row=Config.REPORT,
        )
        if threshold == 1:
            fig.update_layout(margin_b=100)

    _fix_facet_labels(fig)

    return fig


def brand_distribution_gte2(df: pd.DataFrame, threshold: int = 2) -> go.Figure:
    return brand_distribution_gte1(df=df, threshold=threshold, height=50)


def brand_distribution_gte1_vertical(df: pd.DataFrame, threshold: int = 1) -> go.Figure:
    return brand_distribution_gte1(df=df, threshold=threshold, horizontal=False, height=500)


def brand_distribution_gte2_vertical(df: pd.DataFrame, threshold: int = 2) -> go.Figure:
    return brand_distribution_gte1(df=df, threshold=threshold, horizontal=False, height=500)


def brand_accuracy(df: pd.DataFrame) -> go.Figure:
    _df = data.column_comparison_no_na(df, Config.BRAND)

    _df = _df[_df["MATCH"].sum(axis=1) < 2]
    _df.columns = [" - ".join(col) for col in _df.columns]

    fig = go.Figure(
        data=[
            go.Table(
                header={"values": _df.columns},
                cells={"values": _df.T.values},
            ),
        ],
    )
    return fig


########################################
# Footwear Color
########################################
def color_distribution(df: pd.DataFrame) -> go.Figure:
    _df = data.column_comparison(df, [Config.TYPE, Config.COLOR])
    for report_type in (Config.REPORTED, Config.FOUND):
        _df.loc[_df[(report_type, Config.TYPE)] == "minimal", (report_type, Config.TYPE)] = "shoes"
        for sep in "/,":
            _df[(report_type, Config.COLOR)] = [
                color.split(sep)[0] if sep in str(color) else color
                for color in _df[(report_type, Config.COLOR)]
            ]

    _rdf = _df[Config.REPORTED].dropna().value_counts().reset_index()
    _fdf = _df[Config.FOUND].dropna().value_counts().reset_index()
    _rdf[Config.REPORT] = Config.REPORTED
    _fdf[Config.REPORT] = Config.FOUND
    _df = pd.concat([_rdf, _fdf]).dropna()
    _df.rename(columns={0: Config.COUNT}, inplace=True)
    _df = _df[_df[Config.TYPE] != "mix"]

    _df = _df[["&" not in str(value) for value in _df[Config.COLOR]]]
    # return _df

    brand_order = list(
        _df.groupby(Config.COLOR)
        .sum(numeric_only=True)
        .sort_values(Config.COUNT, ascending=False)
        .index,
    )
    brand_order.remove("various")
    brand_order.append("various")

    fig = px.bar(
        _df,
        x=Config.COUNT,
        y=Config.COLOR,
        color=Config.TYPE,
        category_orders={Config.COLOR: brand_order},
        text_auto=True,
        height=40 * len(brand_order),
        facet_col=Config.REPORT,
    )

    _fix_facet_labels(fig)
    _fix_left_margin(fig, _df[Config.COLOR])

    return fig


def color_accuracy(df: pd.DataFrame) -> go.Figure:
    _df = data.column_comparison_no_na(df, Config.COLOR)

    _df = _df[_df["MATCH"].sum(axis=1) < 2]
    _df.columns = [" - ".join(col) for col in _df.columns]

    fig = go.Figure(
        data=[
            go.Table(
                header={"values": _df.columns},
                cells={"values": _df.T.values},
            ),
        ],
    )
    fig.update_layout(height=800)
    return fig
