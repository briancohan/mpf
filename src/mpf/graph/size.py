import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from mpf import theme  # noqa: F401
from mpf.config import Config, FootwearSubtype, FootwearType, SizeType
from mpf.graph import utils


# MARK: _fix_size_yaxis_labels
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


# MARK: _clean_shoe_size_data_for_distribution_plots
def _clean_shoe_size_data_for_distribution_plots(df: pd.DataFrame) -> pd.DataFrame:
    _df = df[[Config.SECTION, Config.TYPE, Config.SIZE_LO, Config.SIZE_HI, Config.SIZE_TYPE]]
    _df = utils.fix_separate_as_found(_df)
    _df = _df.dropna(subset=[Config.SIZE_LO, Config.SIZE_HI])

    for col in [Config.SIZE_LO, Config.SIZE_HI]:
        _df[col] = _df[col].astype(float)
    _df[Config.SIZE] = _df[[Config.SIZE_LO, Config.SIZE_HI]].mean(axis=1)

    _df = _df.replace("nan", np.nan).dropna()

    return _df


# MARK: _shoe_distribution
def _shoe_distribution(
    df: pd.DataFrame,
    facet_row: str,
    facet_col: str,
    color: str,
    col: str = Config.SIZE,
) -> go.Figure:
    """Configurable histogram of shoe sizes by type and section.

    Used by:
    - shoe_size_distribution_by_type
    - shoe_size_distribution_by_category
    """
    fig = px.histogram(
        df.dropna(),
        x=col,
        facet_row=facet_row,
        facet_col=facet_col,
        color=color,
        height=700,
        width=1000,
        text_auto=True,
        labels={
            col: "Shoe Size",
            Config.SIZE_TYPE: "Size Type",
            Config.TYPE: "Footwear Type",
        },
        category_orders={
            Config.TYPE: [ft.name for ft in FootwearType if ft.value in df[Config.TYPE]],
            Config.SIZE_TYPE: [st.name for st in SizeType if st.value in df[Config.SIZE_TYPE]],
        },
    )

    fig.update_xaxes(
        tick0=4,
        dtick=1,
        showticklabels=True,
    )

    for annotation in fig.layout.annotations:
        annotation.text = annotation.text.split("=")[1].capitalize()
    _fix_size_yaxis_labels(fig)

    utils.put_legend_inside_subplot(fig, x=0.97, y=0.98)
    return fig


# MARK: shoe_size_distribution_by_type
def shoe_size_distribution_by_type(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    """Histogram of shoe sizes by type and section.

    Uses the average size if a range was reported.
    """
    _df = _clean_shoe_size_data_for_distribution_plots(footwear.copy())

    fig = _shoe_distribution(
        _df,
        facet_row=Config.SECTION,
        facet_col=Config.TYPE,
        color=Config.SIZE_TYPE,
        col=Config.SIZE,
    )
    fig.update_traces(textangle=0)

    return fig


# MARK: shoe_size_distribution_by_category
def shoe_size_distribution_by_category(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    """Histogram of shoe sizes by type and section.

    Uses the average size if a range was reported.
    """
    _df = _clean_shoe_size_data_for_distribution_plots(footwear.copy())
    _df = _df[_df[Config.TYPE] != "nan"]

    fig = _shoe_distribution(
        _df,
        facet_row=Config.SECTION,
        facet_col=Config.SIZE_TYPE,
        color=Config.TYPE,
        col=Config.SIZE,
    )
    fig.update_traces(textangle=0)

    return fig


# MARK: shoe_size_accuracy
def shoe_size_accuracy(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    cols = [
        Config.ID,
        Config.SECTION,
        Config.TYPE,
        Config.SUBTYPE,
        Config.SIZE_LO,
        Config.SIZE_HI,
    ]
    _df = footwear.copy()[cols]
    _df = utils.promote_subtypes(_df, [FootwearSubtype.MINIMAL, FootwearSubtype.MIXED])

    _df = utils.fix_footwear_type(_df)
    _df = utils.fix_separate_as_found(_df)

    ########################################``
    # MARK: > Data Manipulation
    ########################################
    _df = _df.dropna()

    _df[Config.SIZE] = pd.concat([_df[Config.SIZE_LO], _df[Config.SIZE_HI]], axis=1).values.tolist()
    _df = (
        _df.sort_values(  # Ensure we get the FOUND footwear type
            by=Config.SECTION,
            ascending=True,
        )
        .pivot_table(
            index=[Config.ID, Config.TYPE],
            columns=[Config.SECTION],
            values=Config.SIZE,
            aggfunc="first",
        )
        .dropna()
        .reset_index()
    )
    min_size = min(map(min, _df[Config.FOUND])) - 1
    max_size = max(map(max, _df[Config.FOUND])) + 1

    ########################################
    # MARK: > Base Figure
    ########################################
    fig = go.Figure()
    for row in _df.itertuples():
        fig.add_trace(
            go.Scatter(
                x=row.REPORTED,
                y=row.FOUND,
                showlegend=False,
                marker_color=Config.FOOTWEAR_COLOR[row.Type.lower()],
                marker_symbol=Config.FOOTWEAR_MARKER[row.Type.lower()],
            )
        )

    ########################################
    # MARK: > Error Bars & Error Bar Annotations
    ########################################
    # MARK: > Diagonal Dashed Line
    fig.add_shape(
        type="line",
        line={"color": "black", "dash": "dot"},
        xref="x",
        x0=min_size,
        x1=max_size,
        yref="y",
        y0=min_size,
        y1=max_size,
    )
    # Green Diagonal Error Bars
    color = "#788d64"
    opacity = 0.25

    for offset in [0.5, 1.0]:
        fig.add_trace(
            go.Scatter(
                x=[
                    min_size - offset,
                    max_size - offset,
                    max_size + offset,
                    min_size + offset,
                ],
                y=[min_size, max_size, max_size, min_size],
                fill="toself",
                line={"width": 0},
                # marker=None,
                marker={"size": 0, "color": color, "opacity": opacity},
                showlegend=False,
                fillcolor=color,
                opacity=opacity,
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
            x=min_size + offset + error,
            y=min_size + offset,
            ay=min_size + offset,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            ax=min_size + 3,
            xanchor="left",
            arrowhead=2,
        )
    ########################################
    # MARK: > Legend & Legend Annotations
    ########################################
    legend_key_center = min_size + 1
    legend_text_start = legend_key_center + 1
    legend_spacing = 0.3
    y = max_size - 1.5 - legend_spacing

    # Reported Range. This is different because it has a line and isn't just a point.
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

    # Data Marker and Text Description
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
        # (
        #     "Found: Mixed",
        #     Config.FOOTWEAR_COLOR["mixed"],
        #     Config.FOOTWEAR_MARKER["mixed"],
        # ),
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

    # Black Box Around Legend
    fig.add_shape(type="rect", x0=5, x1=9, y0=y, y1=13.5 + legend_spacing)

    ########################################
    # MARK: > Layout
    ########################################
    fig.update_layout(
        # height=fig.layout.width or fig.layout.template.layout.width,
        height=800,
        width=800,
        xaxis={
            "range": [min_size, max_size],
            "dtick": 1,
            "tick0": min_size,
            # 'scaleratio':1,
            "title": Config.REPORTED.title() + " Shoe Size",
        },
        yaxis={
            "range": [min_size, max_size],
            "dtick": 1,
            "tick0": min_size,
            "scaleratio": 1,
            "scaleanchor": "x",
            "title": Config.FOUND.title() + " Shoe Size",
        },
    )
    return fig
