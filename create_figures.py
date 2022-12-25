from inspect import getmembers, isfunction

from mpf import graph
from mpf.auth import get_credentials
from mpf.config import Config
from mpf.data import get_data

df = get_data(get_credentials())

for name, func in getmembers(graph, isfunction):
    if name.startswith("_"):
        continue
    file = Config.EXPORT_DIR / f"{name}.png"
    func(df).write_image(str(file))
