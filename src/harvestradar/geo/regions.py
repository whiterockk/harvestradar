"""Producing regions (ADM1) and production weights from MapSPAM 2020 (CC BY 4.0).

For each commodity: sum MapSPAM production per ADM1 polygon, sort, keep regions until they cover
`coverage` of world production, weight = prod_r / sum(prod_r). Then sample up to N NASA POWER grid
cells per region on the most productive pixels, each with a weight.
"""

from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from exactextract import exact_extract

from harvestradar.config import Settings
from harvestradar.ingest import boundaries
from harvestradar.ingest.manifest import record
from harvestradar.ingest.power import cell_id, snap
from harvestradar.paths import PROCESSED, RAW

SPAM_DIR = RAW / "spam"


def spam_raster(crop: str):
    hits = sorted(SPAM_DIR.glob(f"*_P_{crop}_A.tif")) or sorted(SPAM_DIR.glob(f"*{crop}*_A.tif"))
    if not hits:
        raise FileNotFoundError(
            f"MapSPAM 2020 production raster for {crop} not found in {SPAM_DIR}. "
            "Download spam2020V2r2_global_production.geotiff.zip from https://doi.org/10.7910/DVN/SWPENT "
            "(guestbook required) and extract the *_P_{crop}_A.tif files there.")
    return hits[0]


def candidate_countries(cfg: Settings, key: str, fao: pd.DataFrame, share: float = 0.995) -> list[str]:
    c = cfg.commodities[key]
    last = fao[(fao.commodity == key)].year.max()
    p = fao[(fao.commodity == key) & (fao.year.between(last - 4, last))]
    p = p.groupby("country_iso3").production_t.mean().sort_values(ascending=False)
    cum = p.cumsum() / p.sum()
    keep = list(cum[cum.shift(fill_value=0) < share].index)
    return sorted(set(keep) | set(c.countries))


def build_regions(cfg: Settings, key: str, fao: pd.DataFrame) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    c = cfg.commodities[key]
    path = spam_raster(c.spam_crop)
    with rasterio.open(path) as src:
        arr = src.read(1, masked=True)
        world_total = float(arr.sum())
    adm = boundaries.fetch_many(candidate_countries(cfg, key, fao))
    adm = adm[adm.geometry.notna() & ~adm.geometry.is_empty].reset_index(drop=True)
    adm["rid"] = np.arange(len(adm))
    sums = exact_extract(str(path), adm, ["sum"], include_cols=["rid"], output="pandas")
    adm = adm.merge(sums, on="rid")
    adm = adm.rename(columns={"sum": "prod_t"}).sort_values("prod_t", ascending=False)
    adm["cum_share"] = adm["prod_t"].cumsum() / world_total
    shares = (adm.groupby("country_iso3")["prod_t"].sum() / world_total).rename("share").reset_index()
    shares["source"] = "MapSPAM 2020"
    shares.to_parquet(PROCESSED / f"country_shares_{key}.parquet", index=False)
    keep = adm[adm["cum_share"].shift(fill_value=0) < c.coverage].copy()
    keep["world_share"] = keep["prod_t"] / world_total
    keep["weight"] = keep["prod_t"] / keep["prod_t"].sum()
    code = keep["shape_iso"].where(keep["shape_iso"].notna() & (keep["shape_iso"].astype(str).str.len() > 0),
                                   keep["shape_id"])
    keep["region_id"] = keep["country_iso3"] + "-" + code.astype(str)
    dup = keep["region_id"].duplicated(keep=False)
    keep.loc[dup, "region_id"] = keep.loc[dup, "country_iso3"] + "-" + keep.loc[dup, "shape_id"].astype(str)
    keep["commodity"] = key
    rp = keep.geometry.representative_point()
    keep["lat"], keep["lon"] = rp.y.round(4), rp.x.round(4)
    keep = keep[["region_id", "commodity", "country_iso3", "adm1_name", "prod_t", "world_share", "weight",
                 "lat", "lon", "geometry"]].reset_index(drop=True)
    cells = sample_cells(path, keep, int(cfg.regions["max_cells_per_region"]))
    return gpd.GeoDataFrame(keep, crs=4326), cells


def sample_cells(path, regions: gpd.GeoDataFrame, n_max: int) -> pd.DataFrame:
    """Up to n_max POWER cells per region, chosen on the most productive pixels."""
    vals = exact_extract(str(path), regions, ["values", "coverage", "center_x", "center_y"],
                         include_cols=["region_id"], output="pandas")
    rows = []
    for r in vals.itertuples():
        v = np.asarray(r.values, dtype=float)
        cov = np.asarray(r.coverage, dtype=float)
        x = np.asarray(r.center_x, dtype=float)
        y = np.asarray(r.center_y, dtype=float)
        ok = np.isfinite(v) & (v > 0)
        if not ok.any():
            continue
        lat, lon = snap(y[ok], x[ok])
        d = pd.DataFrame({"lat": lat, "lon": lon, "p": v[ok] * cov[ok]}).groupby(["lat", "lon"]).p.sum()
        d = d.sort_values(ascending=False).head(n_max)
        for (la, lo), p in d.items():
            rows.append((r.region_id, cell_id(la, lo), la, lo, p))
    cells = pd.DataFrame(rows, columns=["region_id", "cell_id", "lat", "lon", "p"])
    cells["cell_weight"] = cells["p"] / cells.groupby("region_id")["p"].transform("sum")
    return cells.drop(columns="p")


def build_all(cfg: Settings) -> dict[str, gpd.GeoDataFrame]:
    from harvestradar.ingest.yields import load_faostat

    fao_p = PROCESSED / "fao_qcl.parquet"
    fao = pd.read_parquet(fao_p) if fao_p.exists() else load_faostat(cfg)
    out, all_cells = {}, []
    for key in cfg.commodities:
        regions, cells = build_regions(cfg, key, fao)
        regions.to_file(PROCESSED / f"regions_{key}.gpkg", driver="GPKG")
        regions.drop(columns="geometry").to_parquet(PROCESSED / f"regions_{key}.parquet", index=False)
        cells["commodity"] = key
        all_cells.append(cells)
        out[key] = regions
        cov = regions["world_share"].sum()
        print(f"[regions] {key}: {len(regions)} regions, coverage {cov:.3f}, weights sum "
              f"{regions['weight'].sum():.6f}, {cells.cell_id.nunique()} cells")
    cells = pd.concat(all_cells, ignore_index=True)
    cells.to_parquet(PROCESSED / "sample_cells.parquet", index=False)
    for p in sorted(SPAM_DIR.glob("*.tif")):
        record(p, "MapSPAM 2020 V2r2 (IFPRI), global production", "https://doi.org/10.7910/DVN/SWPENT",
               "CC BY 4.0")
    summary = {k: {"regions": int(len(v)), "coverage": round(float(v["world_share"].sum()), 4)}
               for k, v in out.items()}
    summary["cells"] = int(cells.cell_id.nunique())
    (PROCESSED / "regions_summary.json").write_text(json.dumps(summary, indent=2))
    return out
