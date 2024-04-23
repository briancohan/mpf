from typing import Callable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from mpf import theme  # noqa: F401
from mpf.config import Config

VIOLIN_OPTS = {
    "func": px.violin,
    "log_x": False,
    "points": "all",
    "box": True,
}
BOX_OPTS = {
    "func": px.box,
    "log_x": True,
    "points": "all",
}


# MARK: _distance
def _distance(
    footwear: pd.DataFrame,
    *,
    threshold: int = 0,
    func: Callable = px.strip,
    log_x: bool = False,
    **kwargs,
) -> go.Figure:
    """Create a graph showing the distances of footwear found separate from the subject."""
    _df = footwear.copy()[[Config.DIST_LO, Config.DIST_LO]]
    distances = _df.dropna(thresh=2).to_numpy().flatten()

    excluded_points = len(distances)
    distances = distances[distances > threshold]
    excluded_points -= len(distances)

    fig = func(
        x=distances,
        log_x=log_x,
        height=300,
        **{k: v for k, v in kwargs.items() if k != "admin"},
    )

    if excluded_points and threshold:
        fig.add_annotation(
            text=f"Excludes {excluded_points} points within {threshold} meters of subject",
            x=0.95,
            y=0.95,
            xref="paper",
            yref="paper",
            showarrow=False,
        )
    fig.layout.xaxis.title = "Distance [m]"

    return fig


# MARK: distances
def distances(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    return _distance(footwear, **kwargs)


# MARK: distances_gt_1
def distances_gt_1(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    return _distance(footwear, threshold=1, **kwargs)


# MARK: distances_log
def distances_log(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    return _distance(footwear, log_x=True, **kwargs)


# MARK: distances_log_gt_1
def distances_log_gt_1(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    return _distance(footwear, threshold=1, log_x=True, **kwargs)


# MARK: distances_violin
def distances_violin(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    return _distance(footwear, **VIOLIN_OPTS, **kwargs)


# MARK: distances_violin_gt_1
def distances_violin_gt_1(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    return _distance(footwear, threshold=1, **VIOLIN_OPTS, **kwargs)


# MARK: distances_box
def distances_box(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    return _distance(footwear, **BOX_OPTS, **kwargs)


# MARK: distances_box_gt_1
def distances_box_gt_1(footwear: pd.DataFrame, **kwargs) -> go.Figure:
    return _distance(footwear, threshold=1, **BOX_OPTS, **kwargs)
