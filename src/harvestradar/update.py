"""Daily update (run by .github/workflows/daily.yml every working day).

Fetches the new days only: NASA POWER weather since each cell's last complete day, futures closes, ONI.
Then features, weekly predictions with the stored vintage models (a full training only when the vintage of
the year is missing, i.e. once a year), weekly and daily index, events, backtest, price reaction, climate
fair value, the notes of the new days and the offline snapshot in data/demo.
"""

from __future__ import annotations

import datetime as dt
import os
import time

import pandas as pd

from harvestradar.config import Settings
from harvestradar.paths import MODELS_STORE, PROCESSED


def previous_business_day(today: dt.date | None = None) -> dt.date:
    today = today or dt.datetime.now(dt.timezone.utc).date()
    return (pd.Timestamp(today) - pd.offsets.BDay(1)).date()


def run_update(cfg: Settings, end: dt.date | None = None, deterministic_notes: bool = False,
               skip_weather: bool = False) -> dt.date:
    from harvestradar.demo.export import export_demo
    from harvestradar.ingest.enso import fetch_oni
    from harvestradar.ingest.power import update_cells
    from harvestradar.ingest.prices import fetch_prices
    from harvestradar.pipeline import build_daily, build_features, build_index, predict_weekly, train_models
    from harvestradar.report.weekly_note import build_notes

    end = end or previous_business_day()
    os.environ["HARVESTRADAR_AS_OF_END"] = end.isoformat()
    t0 = time.time()

    def step(name, fn, *a, **k):
        s = time.time()
        fn(*a, **k)
        print(f"[update] {name}: {time.time() - s:.0f} s")

    print(f"[update] data as of {end}")
    if not skip_weather:
        cells = pd.read_parquet(PROCESSED / "sample_cells.parquet")
        step("weather", update_cells, cells, end.isoformat(), cfg.weather_start.isoformat())
    step("El Nino", fetch_oni)
    step("prices", fetch_prices, cfg)
    step("features", build_features, cfg)
    if (MODELS_STORE / f"yield_model_{end.year}.joblib").exists():
        step("predictions", predict_weekly, cfg)
    else:
        step("training (new vintage)", train_models, cfg)
    step("weekly index, events, backtest", build_index, cfg, reuse_climatology=True)
    step("daily index, price reaction, fair value", build_daily, cfg)
    step("notes", build_notes, cfg, deterministic=deterministic_notes, new_only=True)
    step("snapshot", export_demo, cfg)
    print(f"[update] done in {(time.time() - t0) / 60:.1f} min")
    return end
