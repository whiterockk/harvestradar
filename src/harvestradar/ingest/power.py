"""NASA POWER daily point data (MERRA-2 based, 0.5 x 0.625 degree native grid), 1981 to present.

No key, public NASA data. One request per grid cell for the full history.
Variables: T2M_MAX, T2M_MIN (deg C), PRECTOTCORR (mm/day), GWETROOT, GWETTOP (soil wetness, 0-1).
"""

from __future__ import annotations

import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import requests

from harvestradar.ingest.manifest import USER_AGENT, record_group
from harvestradar.paths import RAW

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMS = ["T2M_MAX", "T2M_MIN", "PRECTOTCORR", "GWETROOT", "GWETTOP"]
RENAME = {"T2M_MAX": "tmax_c", "T2M_MIN": "tmin_c", "PRECTOTCORR": "precip_mm",
          "GWETROOT": "sm_root", "GWETTOP": "sm_top"}
POWER_DIR = RAW / "power"
LAT_STEP, LON_STEP = 0.5, 0.625


def snap(lat: np.ndarray, lon: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Centre of the MERRA-2 cell containing each point."""
    return np.round(np.asarray(lat) / LAT_STEP) * LAT_STEP, np.round(np.asarray(lon) / LON_STEP) * LON_STEP


def cell_id(lat: float, lon: float) -> str:
    return f"{lat:+07.2f}_{lon:+08.3f}"


def _fetch_one(lat: float, lon: float, start: str, end: str, session: requests.Session) -> pd.DataFrame:
    params = dict(parameters=",".join(PARAMS), community="AG", latitude=lat, longitude=lon,
                  start=start.replace("-", ""), end=end.replace("-", ""), format="CSV", header="false")
    last = None
    for attempt in range(5):
        try:
            r = session.get(URL, params=params, timeout=120, headers={"User-Agent": USER_AGENT})
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            r.raise_for_status()
            df = pd.read_csv(io.StringIO(r.text))
            df["date"] = pd.to_datetime(df["YEAR"].astype(str), format="%Y") + pd.to_timedelta(df["DOY"] - 1, "D")
            df = df.drop(columns=["YEAR", "DOY"]).rename(columns=RENAME)
            df = df.replace(-999.0, np.nan)
            return df
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"POWER failed for {lat},{lon}: {last}")


def fetch_cells(cells: pd.DataFrame, start: str, end: str, workers: int = 4, refresh: bool = False) -> int:
    """cells: DataFrame with cell_id, lat, lon. Each cell is written to data/raw/power/<cell_id>.parquet."""
    POWER_DIR.mkdir(parents=True, exist_ok=True)
    todo = []
    for row in cells.itertuples():
        p = POWER_DIR / f"{row.cell_id}.parquet"
        if refresh or not p.exists():
            todo.append(row)
    done = 0
    with requests.Session() as s, ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(_fetch_one, r.lat, r.lon, start, end, s): r for r in todo}
        for f in as_completed(futs):
            r = futs[f]
            try:
                df = f.result()
            except Exception as e:  # noqa: BLE001
                print(f"[power] {r.cell_id}: {e}")
                continue
            df.to_parquet(POWER_DIR / f"{r.cell_id}.parquet", index=False)
            done += 1
            if done % 100 == 0:
                print(f"[power] {done}/{len(todo)} cells")
    n = len(list(POWER_DIR.glob("*.parquet")))
    record_group("data/raw/power", "NASA POWER daily point API (MERRA-2)", URL,
                 "NASA open data, free of charge", n, note=f"{start} to {end}, parameters {','.join(PARAMS)}")
    return done


def update_cells(cells: pd.DataFrame, end: str, first: str, overlap_days: int = 10, workers: int = 4) -> int:
    """Append the days since each cell's last complete day (minus an overlap) up to `end`. Cells never fetched
    get their full history from `first`. Trailing days that NASA has not filled yet (all missing) are dropped,
    so the next run asks for them again."""
    POWER_DIR.mkdir(parents=True, exist_ok=True)
    end_ts = pd.Timestamp(end)
    jobs = []
    for row in cells.drop_duplicates("cell_id").itertuples():
        p = POWER_DIR / f"{row.cell_id}.parquet"
        if p.exists():
            last = pd.read_parquet(p, columns=["date", "tmax_c"]).dropna().date.max()
            start = min(last - pd.Timedelta(days=overlap_days), end_ts)
        else:
            start = pd.Timestamp(first)
        if start <= end_ts:
            jobs.append((row, start))
    done = failed = 0
    with requests.Session() as s, ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(_fetch_one, r.lat, r.lon, st.strftime("%Y-%m-%d"), end_ts.strftime("%Y-%m-%d"), s): (r, st)
                for r, st in jobs}
        for f in as_completed(futs):
            r, st = futs[f]
            try:
                new = f.result()
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"[power] {r.cell_id}: {e}")
                continue
            p = POWER_DIR / f"{r.cell_id}.parquet"
            old = pd.read_parquet(p) if p.exists() else new.iloc[0:0]
            d = pd.concat([old[old.date < st], new], ignore_index=True).sort_values("date").reset_index(drop=True)
            vals = [c for c in RENAME.values() if c in d.columns]
            filled = d[vals].notna().any(axis=1)
            if filled.any():
                d = d.loc[: filled[filled].index[-1]]
            d.to_parquet(p, index=False)
            done += 1
            if done % 250 == 0:
                print(f"[power] {done}/{len(jobs)} cells updated")
    print(f"[power] {done} cells updated to {end}, {failed} failed")
    record_group("data/raw/power", "NASA POWER daily point API (MERRA-2)", URL,
                 "NASA open data, free of charge", len(list(POWER_DIR.glob("*.parquet"))),
                 note=f"incremental update to {end}, parameters {','.join(PARAMS)}")
    if failed > 0.05 * max(1, len(jobs)):
        raise RuntimeError(f"NASA POWER: {failed} of {len(jobs)} cells failed")
    return done


def load_cells(cell_ids: list[str]) -> pd.DataFrame:
    frames = []
    for cid in cell_ids:
        p = POWER_DIR / f"{cid}.parquet"
        if p.exists():
            d = pd.read_parquet(p)
            d["cell_id"] = cid
            frames.append(d)
    return pd.concat(frames, ignore_index=True)
