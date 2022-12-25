import plotly.graph_objects as go
import plotly.io as pio

from .config import Config

nats = dict(
    layout=dict(
        width=800,
        colorway=[Config.BRAND_PRIMARY],
        plot_bgcolor=Config.BRAND_SECONDARY,
        colorscale=dict(
            sequential=[
                (0, Config.BRAND_SECONDARY),
                (1, Config.BRAND_PRIMARY),
            ]
        ),
    ),
)


pio.templates["nats"] = go.layout.Template(nats)
pio.templates.default = "nats"
