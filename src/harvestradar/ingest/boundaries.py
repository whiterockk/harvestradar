"""geoBoundaries gbOpen ADM1 (simplified geometry), one file per country. Licence per country, mostly
CC BY 4.0 or public domain; recorded in the manifest."""

from __future__ import annotations

import json
import re

import geopandas as gpd
import pandas as pd

from harvestradar.ingest.manifest import download, record
from harvestradar.paths import RAW

API = "https://www.geoboundaries.org/api/current/gbOpen/{iso}/ADM1/"
GB_DIR = RAW / "geoboundaries"


def media_url(url: str) -> str:
    """geoBoundaries files are stored with Git LFS: github.com/<o>/<r>/raw/<ref>/<path> serves a pointer
    or redirects; media.githubusercontent.com/media/<o>/<r>/<ref>/<path> serves the file itself."""
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/raw/([^/]+)/(.+)", url)
    return f"https://media.githubusercontent.com/media/{m[1]}/{m[2]}/{m[3]}/{m[4]}" if m else url


def fetch_adm1(iso3: str) -> gpd.GeoDataFrame:
    meta_path = GB_DIR / f"{iso3}_ADM1_meta.json"
    geo_path = GB_DIR / f"{iso3}_ADM1_simplified.geojson"
    if not geo_path.exists():
        download(API.format(iso=iso3), meta_path)
        meta = json.loads(meta_path.read_text())
        url = media_url(meta["simplifiedGeometryGeoJSON"])
        download(url, geo_path, timeout=300)
        record(geo_path, f"geoBoundaries gbOpen ADM1 {iso3} ({meta.get('boundarySource', '')})", url,
               meta.get("boundaryLicense", "see geoBoundaries"))
    g = gpd.read_file(geo_path)
    g = g.rename(columns={"shapeName": "adm1_name", "shapeID": "shape_id", "shapeISO": "shape_iso"})
    g["country_iso3"] = iso3
    keep = ["country_iso3", "adm1_name", "shape_id", "shape_iso", "geometry"]
    for k in keep:
        if k not in g:
            g[k] = None
    return g[keep].to_crs(4326)


def fetch_many(isos: list[str]) -> gpd.GeoDataFrame:
    frames = []
    for iso in sorted(set(isos)):
        try:
            frames.append(fetch_adm1(iso))
        except Exception as e:  # noqa: BLE001
            print(f"[boundaries] {iso}: {e}")
    return gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=4326)
