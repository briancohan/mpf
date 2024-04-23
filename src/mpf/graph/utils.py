import numpy as np
import pandas as pd
import plotly.graph_objects as go

from mpf import theme  # noqa: F401
from mpf.config import Config, FootwearSubtype, FootwearType, SizeType


# MARK: fix_facet_labels
def fix_facet_labels(fig: go.Figure) -> None:
    """Remove column name and '=' from labels."""
    for annotation in fig.layout.annotations:
        if "=REPORTED" in annotation.text:
            annotation.text = "Reported Footwear"
        elif "=FOUND" in annotation.text:
            annotation.text = "Found Footwear"
        else:
            annotation.text = annotation.text.split("=")[1]


# MARK: fix_left_margin
def fix_left_margin(fig: go.Figure, data: pd.Series, standoff: int = 0) -> None:
    """Fix the left margin so Y-axis title is legible.

    This is necessary when the Y-axis labels are long.
    """
    standoff = standoff or 8 * max(len(str(item)) for item in data)
    fig.update_layout(margin_l=standoff, yaxis_title_standoff=standoff, yaxis_ticksuffix="  ")


# MARK: fix_left_margin
def fix_bottom_margin(fig: go.Figure, data: pd.Series, standoff: int = 0) -> None:
    """Fix the bottom margin so X-axis title is legible.

    This is necessary when the X-axis labels are long.
    """
    standoff = standoff or 8 * max(len(str(item)) for item in data)
    fig.update_layout(margin_b=standoff)


# MARK: fix_footwear_type
def fix_footwear_type(df: pd.DataFrame, include_minimal: bool = False) -> pd.DataFrame:
    """Adjust footwear code to words."""
    df[Config.TYPE] = df[Config.TYPE].astype(str)
    for ft in FootwearType:
        df.loc[df[Config.TYPE] == ft.value, Config.TYPE] = ft.name.title()

    df.loc[df[Config.TYPE] == "nan", Config.TYPE] = "Unknown"

    if include_minimal:
        mask = df[Config.SUBTYPE] == FootwearSubtype.MINIMAL.value
        df.loc[mask, Config.TYPE] = FootwearSubtype.MINIMAL.name.title()

    return df


# MARK: fix_footwear_size_type
def fix_footwear_size_type(df: pd.DataFrame) -> pd.DataFrame:
    """Adjust footwear code to words."""
    df[Config.SIZE_TYPE] = df[Config.SIZE_TYPE].astype(str)
    for st in SizeType:
        df.loc[df[Config.SIZE_TYPE] == st.value, Config.SIZE_TYPE] = st.name
    df.loc[df[Config.SIZE_TYPE] == "nan", Config.SIZE_TYPE] = "UNKNOWN"

    return df


# MARK: fix_separate_as_found
def fix_separate_as_found(df: pd.DataFrame) -> pd.DataFrame:
    """Treat separate as found."""
    df.loc[df[Config.SECTION] == Config.SEPARATE, Config.SECTION] = Config.FOUND
    return df


# MARK: put_legend_inside_subplot
def put_legend_inside_subplot(fig: go.Figure, x: float, y: float) -> None:
    ref = "paper"
    fig.layout.legend = {
        "x": x,
        "y": y,
        "xanchor": "right" if x > 0.5 else "left",
        "yanchor": "top" if y > 0.5 else "bottom",
        "xref": ref,
        "yref": ref,
    }
    return fig


# MARK: promote_subtypes
def promote_subtypes(df: pd.DataFrame, subtypes: list[FootwearSubtype]) -> pd.DataFrame:
    """Promote subtypes to types."""
    for subtype in list(subtypes):
        df.loc[df[Config.SUBTYPE] == subtype.name.title(), Config.TYPE] = subtype.name.title()

    print(df[df.ID == 20])
    return df


# MARK: proportional_venn
def proportional_venn(
    value1: int,
    value2: int,
    overlap: int,
    label1: str,
    label2: str,
) -> go.Figure:
    """Create a Venn Diagarm with proportional circles.

    This will show the overlap between two groups as well as the unique values.
    Circles are scaled to show the relative sizes of the groups and are positioned
    to show the overlap.
    """

    def diameter_from_area(area: int) -> float:
        return 2 * (100 * area / np.pi) ** 0.5

    d1 = diameter_from_area(value1)
    d2 = diameter_from_area(value2)

    x_shift = diameter_from_area(overlap) / 2
    larger_diameter = max(d1, d2)
    total = value1 + value2 - overlap

    circle_1 = go.layout.Shape(
        type="circle",
        x0=-d1 + x_shift,
        x1=0 + x_shift,
        y0=-d1 / 2,
        y1=d1 / 2,
        fillcolor=Config.BRAND_PRIMARY,
        opacity=0.75,
    )
    circle_2 = go.layout.Shape(
        type="circle",
        x0=0 - x_shift,
        x1=d2 - x_shift,
        y0=-d2 / 2,
        y1=d2 / 2,
        fillcolor=Config.BRAND_SECONDARY,
        opacity=0.75,
    )
    circle_1_outline = go.layout.Shape(
        type="circle",
        x0=-d1 + x_shift,
        x1=0 + x_shift,
        y0=-d1 / 2,
        y1=d1 / 2,
    )
    circle_2_outline = go.layout.Shape(
        type="circle",
        x0=0 - x_shift,
        x1=d2 - x_shift,
        y0=-d2 / 2,
        y1=d2 / 2,
    )

    annotation1 = go.layout.Annotation(
        x=(x_shift * 0.9) - d1,
        y=0,
        text=f"{label1}<br>Only<br>n={value1 - overlap}<br>{(value1 - overlap) * 100 / total:.0f}%",
        showarrow=False,
        font={"size": 16},
        xanchor="right",
    )
    annotation2 = go.layout.Annotation(
        x=d2 - (x_shift * 0.9),
        y=0,
        text=f"{label2}<br>Only<br>n={value2 - overlap}<br>{(value2 - overlap) * 100 / total:.0f}%",
        showarrow=False,
        font={"size": 16},
        xanchor="left",
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
            "range": [-larger_diameter, larger_diameter],
        },
        yaxis={
            "scaleanchor": "x",
            "scaleratio": 1,
            "range": [-larger_diameter / 2, larger_diameter / 2],
        },
        shapes=[circle_1, circle_2, circle_1_outline, circle_2_outline],
        annotations=[annotation1, annotation2, annotation3],
    )

    fig = go.Figure(layout=layout)
    fig.update_layout(
        xaxis={
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "showticklabels": False,
            "range": [-d1, d2],
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
