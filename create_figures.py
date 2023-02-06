from inspect import getmembers, isfunction

import plotly.io as pio

from mpf import graph
from mpf.auth import get_credentials
from mpf.config import Config
from mpf.data import get_data

# pio.templates.default = "nats+jsar"

df = get_data(get_credentials())

for name, func in getmembers(graph, isfunction):
    if name.startswith("_"):
        continue
    print(name, "...", end="")

    try:
        fig = func(df)
    except Exception:
        print("❌❌")
        continue

    if "jsar" in pio.templates.default:
        for annotation in fig.layout.annotations:
            annotation.font.size = Config.JSAR_FONT_SIZE

    try:
        file = Config.PROJECT_DIR / "figures" / f"{name}.png"
        fig.write_image(str(file))
        print("✅")
    except Exception:
        print("❌")
