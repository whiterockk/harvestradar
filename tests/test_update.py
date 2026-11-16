import datetime as dt

import numpy as np
import pandas as pd

from harvestradar.ingest import power
from harvestradar.update import latest_business_day

COLS = ["tmax_c", "tmin_c", "precip_mm", "sm_root", "sm_top"]


def _days(start, end, missing_tail=0):
    d = pd.DataFrame({"date": pd.date_range(start, end)})
    for c in COLS:
        d[c] = 1.0
    if missing_tail:
        d.loc[d.index[-missing_tail:], COLS] = np.nan
    return d


def test_update_cells_appends_new_days_and_drops_unfilled_tail(tmp_path, monkeypatch):
    monkeypatch.setattr(power, "POWER_DIR", tmp_path)
    monkeypatch.setattr(power, "record_group", lambda *a, **k: None)
    _days("2026-01-01", "2026-11-05").to_parquet(tmp_path / "+010.00_+010.000.parquet", index=False)
    calls = []

    def fake(lat, lon, start, end, session):
        calls.append((start, end))
        new = _days(start, end, missing_tail=2)  # NASA has not filled the last two days yet
        new.loc[new.date == pd.Timestamp("2026-11-01"), "tmax_c"] = 9.0  # a revised value
        return new

    monkeypatch.setattr(power, "_fetch_one", fake)
    cells = pd.DataFrame({"cell_id": ["+010.00_+010.000", "+020.00_+020.000"], "lat": [10.0, 20.0], "lon": [10.0, 20.0]})
    n = power.update_cells(cells, "2026-11-13", "1981-01-01", overlap_days=10)
    assert n == 2
    assert ("2026-10-26", "2026-11-13") in calls and ("1981-01-01", "2026-11-13") in calls
    d = pd.read_parquet(tmp_path / "+010.00_+010.000.parquet")
    assert d.date.is_unique and d.date.is_monotonic_increasing
    assert d.date.max() == pd.Timestamp("2026-11-11")  # the unfilled tail is fetched again next run
    assert d.loc[d.date == pd.Timestamp("2026-11-01"), "tmax_c"].item() == 9.0
    assert d.date.min() == pd.Timestamp("2026-01-01")


def test_latest_business_day():
    assert latest_business_day(dt.date(2026, 11, 16)) == dt.date(2026, 11, 16)  # Monday
    assert latest_business_day(dt.date(2026, 11, 15)) == dt.date(2026, 11, 13)  # Sunday -> Friday


def test_prices_keep_only_settled_closes():
    import pandas as pd

    from harvestradar.ingest.prices import settled_until

    assert settled_until(pd.Timestamp("2026-11-16 09:30", tz="UTC")) == pd.Timestamp("2026-11-16")
    assert settled_until(pd.Timestamp("2026-11-16 21:30", tz="UTC")) == pd.Timestamp("2026-11-17")
