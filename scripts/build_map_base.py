"""Project the graded Blue Marble (equirectangular) to Equal Earth, once, offline. Output is committed.

Writes static/img/equal_earth_radar_night.webp (transparent outside the globe outline) and a JSON file
with the extent in projected kilometres, so that SVG layers can be drawn in the same coordinates.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "src" / "harvestradar" / "app" / "static" / "img"
SRC = IMG / "blue_marble_radar_night.jpg"
EQ = "+proj=eqearth +lon_0=0 +datum=WGS84 +units=m +no_defs"
LAT_MIN, LAT_MAX = -58.0, 84.0
WIDTH = 3600


def main() -> None:
    fwd = Transformer.from_crs("EPSG:4326", EQ, always_xy=True)
    inv = Transformer.from_crs(EQ, "EPSG:4326", always_xy=True)
    xmax, _ = fwd.transform(180.0, 0.0)
    _, ytop = fwd.transform(0.0, LAT_MAX)
    _, ybot = fwd.transform(0.0, LAT_MIN)
    height = int(round(WIDTH * (ytop - ybot) / (2 * xmax)))
    xs = np.linspace(-xmax, xmax, WIDTH)
    ys = np.linspace(ytop, ybot, height)
    X, Y = np.meshgrid(xs, ys)
    lon, lat = inv.transform(X.ravel(), Y.ravel())
    lon, lat = np.asarray(lon), np.asarray(lat)
    # inside the globe outline: re-project and compare (pyproj extrapolates outside)
    bx, by = fwd.transform(np.clip(lon, -180, 180), np.clip(lat, -90, 90))
    inside = np.isfinite(lon) & np.isfinite(lat) & (np.abs(lon) <= 180) & \
        (np.hypot(np.asarray(bx) - X.ravel(), np.asarray(by) - Y.ravel()) < 2000)
    src = np.asarray(Image.open(SRC).convert("RGB"))
    h, w, _ = src.shape
    col = np.clip(((lon + 180) / 360 * w).astype(int), 0, w - 1)
    row = np.clip(((90 - lat) / 180 * h).astype(int), 0, h - 1)
    rgb = src[np.where(inside, row, 0), np.where(inside, col, 0)]
    alpha = np.where(inside, 255, 0).astype(np.uint8)
    out = np.concatenate([rgb.reshape(height, WIDTH, 3), alpha.reshape(height, WIDTH, 1)], axis=2)
    Image.fromarray(out, "RGBA").save(IMG / "equal_earth_radar_night.webp", quality=82, method=6)
    meta = {"projection": EQ, "x_min_km": -xmax / 1000, "x_max_km": xmax / 1000, "y_top_km": ytop / 1000,
            "y_bottom_km": ybot / 1000, "lat_min": LAT_MIN, "lat_max": LAT_MAX, "width_px": WIDTH,
            "height_px": height, "source": "NASA Blue Marble Next Generation (public domain), graded"}
    (IMG / "equal_earth_radar_night.json").write_text(json.dumps(meta, indent=2))
    print(meta)


if __name__ == "__main__":
    main()
