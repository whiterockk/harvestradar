"""Grade NASA Blue Marble once, offline, for the Radar Night map base. Output is committed.

Source: NASA Visible Earth "Blue Marble Next Generation" (public domain), as shipped in the
three-globe npm package (example/img/earth-blue-marble.jpg, 4096 x 2048, equirectangular).

Grade: desaturate to about 45 %, brightness about 0.5, cool tint (R x0.86, G x0.95, B x1.08),
compress highlights above 0.30 so ice and deserts never outshine the data.
Also writes a darker variant for the episode replay (zoomed views).
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_URL = "https://cdn.jsdelivr.net/npm/three-globe@2.31.0/example/img/earth-blue-marble.jpg"
SRC = ROOT / "data" / "raw" / "img" / "earth-blue-marble.jpg"
OUT = ROOT / "src" / "harvestradar" / "app" / "static" / "img"


def grade(rgb: np.ndarray, saturation: float = 0.45, brightness: float = 0.5,
          knee: float = 0.30, slope: float = 0.35) -> np.ndarray:
    x = rgb.astype(np.float32) / 255.0
    lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    x = lum + (x - lum) * saturation
    x = x * brightness
    x = x * np.array([0.86, 0.95, 1.08], dtype=np.float32)
    x = np.where(x > knee, knee + (x - knee) * slope, x)
    return (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)


def main() -> None:
    if not SRC.exists():
        SRC.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(SRC_URL, SRC)
    im = np.asarray(Image.open(SRC).convert("RGB"))
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(grade(im)).save(OUT / "blue_marble_radar_night.jpg", quality=86, optimize=True,
                                    progressive=True)
    Image.fromarray(grade(im, brightness=0.42)).resize((2048, 1024), Image.LANCZOS).save(
        OUT / "blue_marble_radar_night_2k.jpg", quality=84, optimize=True)
    print("written", sorted(p.name for p in OUT.glob("blue_marble*")), file=sys.stderr)


if __name__ == "__main__":
    main()
