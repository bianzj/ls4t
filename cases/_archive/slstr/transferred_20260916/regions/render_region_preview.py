"""Render a lightweight preview of the South America processing windows."""

from pathlib import Path
import json

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon


ROOT = Path(__file__).resolve().parent
GEOJSON = ROOT / "south_america_tropical_amazon.geojson"
OUTPUT = ROOT / "south_america_tropical_amazon_preview.png"


def xy(lon, lat):
    """Map lon/lat to the preview canvas coordinates."""
    return 60 + (lon + 90) * 13.8, 700 - (lat + 60) * 8.2


with GEOJSON.open(encoding="utf-8") as fp:
    features = json.load(fp)["features"]

fig, ax = plt.subplots(figsize=(12, 8), dpi=160)
ax.set_facecolor("#eaf3f8")

# Approximate continental outline for orientation only; the GeoJSON windows
# remain the authoritative processing geometry.
south_america = [
    (-81, -5), (-79, 0), (-77, 5), (-73, 11), (-68, 13), (-62, 12),
    (-56, 9), (-51, 5), (-47, 1), (-43, -2), (-38, -7), (-35, -13),
    (-36, -18), (-40, -23), (-42, -28), (-48, -31), (-51, -36),
    (-56, -39), (-61, -43), (-65, -51), (-70, -56), (-73, -50),
    (-71, -42), (-69, -34), (-69, -27), (-73, -22), (-77, -17),
    (-80, -11), (-81, -5),
]
ax.add_patch(Polygon([xy(*p) for p in south_america], closed=True,
                      facecolor="#d8c9a2", edgecolor="#766b55", linewidth=1.2,
                      label="South America (orientation)"))

colors = {"final_output_window": "#d1495b", "amazon_focus": "#168aad"}
for feature in features:
    props = feature["properties"]
    x0, y0 = xy(props["west"], props["north"])
    x1, y1 = xy(props["east"], props["south"])
    width, height = x1 - x0, y1 - y0
    role = props["role"]
    ax.add_patch(Rectangle((x0, y0), width, height, fill=False,
                           edgecolor=colors[role], linewidth=2.5,
                           linestyle="--" if role == "final_output_window" else "-",
                           label=("Final output window" if role == "final_output_window"
                                  else "Amazon focus window")))

    label_x = x0 + 8
    label_y = y0 + 16
    ax.text(label_x, label_y,
            "South America tropical final window" if role == "final_output_window" else "Amazon focus window",
            color=colors[role], fontsize=10, weight="bold",
            bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none", "pad": 2})

for lon in range(-80, -29, 10):
    x, _ = xy(lon, -60)
    ax.plot([x, x], [xy(lon, -60)[1], xy(lon, 20)[1]], color="white", linewidth=0.6)
    ax.text(x, 710, f"{abs(lon)}°W", ha="center", va="bottom", fontsize=8, color="#52616b")
for lat in range(-50, 21, 10):
    _, y = xy(-90, lat)
    ax.plot([xy(-90, lat)[0], xy(-25, lat)[0]], [y, y], color="white", linewidth=0.6)
    ax.text(48, y, f"{abs(lat)}°S" if lat < 0 else f"{lat}°N", ha="right", va="center", fontsize=8, color="#52616b")

ax.set_xlim(40, 900)
ax.set_ylim(730, 20)
ax.axis("off")
ax.set_title("South America Tropical / Amazon Processing Region", fontsize=15, weight="bold", pad=16)
ax.text(60, 28, "WGS84 (EPSG:4326), target grid 0.01°; continent outline is schematic",
        fontsize=9, color="#52616b")
ax.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.9)
fig.savefig(OUTPUT, bbox_inches="tight", facecolor=fig.get_facecolor())
print(OUTPUT)
