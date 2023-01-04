from inspect import getmembers, isfunction

from mpf import graph
from mpf.auth import get_credentials
from mpf.config import Config
from mpf.data import get_data

df = get_data(get_credentials())

for name, func in getmembers(graph, isfunction):
    if name.startswith("_"):
        continue
    print(name, "...", end="")

    try:
        fig = func(df)
    except:
        print("❌❌")
        continue
    
    try:
        file = Config.PROJECT_DIR / "figures" / f"{name}.png"
        fig.write_image(str(file))
        print("✅")
    except:
        print("❌")


    try:
        file = Config.EXPORT_DIR / f"{name}.png"
        fig.write_image(str(file))
    except OSError:
        pass
