import plotly.graph_objects as go
import plotly.io as pio

from .config import Config

nats = dict(
    layout=dict(
        width=800,
        colorway=[Config.BRAND_PRIMARY, "#f26157", "#3a5683", "#8e3b46"],
        plot_bgcolor="#ededed",
        colorscale=dict(
            sequential=[
                (0, Config.BRAND_SECONDARY),
                (1, Config.BRAND_PRIMARY),
            ]
        ),
        font_family=Config.FONT,
    ),
    data=dict(
        scatter=[
            dict(
                marker=dict(
                    size=10,
                ),
            )
        ]
    ),
)

jsar = dict(
    layout=dict(
        font_size=Config.JSAR_FONT_SIZE,
        title_font_size=Config.JSAR_FONT_SIZE,
        legend_font_size=Config.JSAR_FONT_SIZE,
        legend_title_font_size=Config.JSAR_FONT_SIZE,
        legend_grouptitlefont_size=Config.JSAR_FONT_SIZE,
        xaxis_title_font_size=Config.JSAR_FONT_SIZE,
        yaxis_title_font_size=Config.JSAR_FONT_SIZE,
    )
)

pio.templates["nats"] = go.layout.Template(nats)
pio.templates["jsar"] = go.layout.Template(jsar)
pio.templates.default = "nats"
