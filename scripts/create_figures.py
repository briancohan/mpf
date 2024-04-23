import warnings
from datetime import datetime
from inspect import getmembers, isfunction

import plotly.io as pio
from mpf import graph
from mpf.auth import get_credentials
from mpf.config import Config
from mpf.data import create_admin_table, create_footwear_table, get_data

warnings.filterwarnings("ignore")
pio.templates.default = "nats"

main_df = get_data(get_credentials())
admin = create_admin_table(main_df)
footwear = create_footwear_table(main_df)

output_dir = Config.PROJECT_DIR / "figures" / datetime.now().strftime("%Y-%m-%d")
output_dir.mkdir(exist_ok=True)

for name, func in getmembers(graph, isfunction):
    if name.startswith("_"):
        continue
    print(name, "...", end="")

    try:
        fig = func(admin=admin, footwear=footwear)
    except Exception:
        print("❌❌ Bad Function Call")
        continue

    if "jsar" in pio.templates.default:
        for annotation in fig.layout.annotations:
            annotation.font.size = Config.JSAR_FONT_SIZE

    try:
        file = output_dir / f"{name}.png"
        fig.write_image(str(file))
        print("✅")
    except Exception:
        print("❌ Could Not Save Image")
