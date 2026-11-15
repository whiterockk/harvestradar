import datetime as dt

import numpy as np
import pandas as pd

from harvestradar.features.windows import active_season, in_critical_window, season_switch, window_open_on


def test_config_validates(cfg):
    assert set(cfg.commodities) == {"maize", "coffee", "cocoa"}
    for c in cfg.commodities.values():
        assert 0 < c.coverage <= 1
        assert c.main_country in c.windows
        assert c.target in {"yield", "production"}


def test_window_crossing_year_end(cfg):
    w = cfg.commodities["cocoa"].windows["CIV"]
    dates = pd.to_datetime(["2023-12-15", "2024-01-20", "2024-02-28", "2024-03-05", "2023-06-01"])
    got = in_critical_window(dates, w, 2023)
    assert got.tolist() == [True, True, True, False, True]


def test_year_offset(cfg):
    # arabica Brazil: the flowering of September Y-1 belongs to the season (harvest) Y
    s, e = cfg.commodities["coffee"].season_span("BRA", 2022)
    assert s == dt.date(2021, 6, 1) and e == dt.date(2021, 11, 30)


def test_active_season_and_switch(cfg):
    c = cfg.commodities["maize"]
    assert active_season(c, "USA", dt.date(2026, 11, 13), 120) == 2026
    assert active_season(c, "USA", dt.date(2026, 12, 20), 120) == 2027
    assert season_switch(c, "USA", 2026, 120) == dt.date(2026, 12, 13)
    assert window_open_on(dt.date(2026, 7, 10), c.windows["USA"])
    assert not window_open_on(dt.date(2026, 11, 13), c.windows["USA"])
    _ = np
