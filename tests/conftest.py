import json

import pandas as pd
import pytest

from harvestradar.config import load_config


@pytest.fixture(scope="session")
def cfg():
    return load_config()


@pytest.fixture()
def payload():
    """A small, self-consistent note payload (synthetic test data)."""
    slots = {
        "RISK": {"kind": "figure", "text": "+2.10", "value": 2.1, "label": "MAIZE harvest-risk index",
                 "source": "risk_index.parquet", "date": "2026-11-13", "detail": ""},
        "RISK_CHANGE": {"kind": "figure", "text": "+0.40", "value": 0.4, "label": "Change", "source": "risk_index.parquet",
                        "date": "2026-11-13", "detail": ""},
        "SUPPLY": {"kind": "figure", "text": "-1.8%", "value": -1.8, "label": "Supply", "source": "model predictions",
                   "date": "2026-11-13", "detail": ""},
        "PRICE": {"kind": "figure", "text": "445.50", "value": 445.5, "label": "CBOT corn close",
                  "source": "prices_maize.parquet", "date": "2026-11-13", "detail": ""},
        "PRICE_CHANGE": {"kind": "figure", "text": "+3.2%", "value": 3.2, "label": "Price change",
                         "source": "prices_maize.parquet", "date": "2026-11-13", "detail": ""},
        "ONI": {"kind": "figure", "text": "+2.46", "value": 2.46, "label": "El Nino", "source": "oni.parquet",
                "date": "2026-11-10", "detail": ""},
        "ONI_PERIOD": {"kind": "label", "text": "ONI AUG-OCT 2026", "label": "ONI season", "source": "oni.parquet",
                       "date": "2026-11-10", "detail": ""},
        "DRIVER1": {"kind": "name", "text": "United States", "label": "c1", "source": "risk_index.parquet",
                    "date": "2026-11-13", "detail": "USA"},
        "DRIVER1_CONTRIB": {"kind": "figure", "text": "-1.20 pp", "value": -1.2, "label": "US", "source": "risk_index.parquet",
                            "date": "2026-11-13", "detail": ""},
        "DRIVER2": {"kind": "name", "text": "China", "label": "c2", "source": "risk_index.parquet",
                    "date": "2026-11-13", "detail": "CHN"},
        "DRIVER2_CONTRIB": {"kind": "figure", "text": "-0.60 pp", "value": -0.6, "label": "CN", "source": "risk_index.parquet",
                            "date": "2026-11-13", "detail": ""},
        "REGION1": {"kind": "name", "text": "Iowa", "label": "r1", "source": "stress_maize.parquet",
                    "date": "2026-11-10", "detail": "USA"},
        "REGION1_STRESS": {"kind": "figure", "text": "+1.9", "value": 1.9, "label": "Iowa stress",
                           "source": "stress_maize.parquet", "date": "2026-11-10", "detail": ""},
    }
    facts = {"risk_z": 2.1, "risk_change_4w": 0.4, "delta_prod_pct": -1.8, "price_change_4w_pct": 3.2, "oni": 2.46,
             "level": "elevated", "windows_open": [], "oni_label": "ONI AUG-OCT 2026",
             "drivers": [{"slot": "DRIVER1", "effect": "lowers supply", "window_open": False},
                         {"slot": "DRIVER2", "effect": "lowers supply", "window_open": False}],
             "region_causes": {"REGION1": "dry soils"}}
    return {"commodity": "maize", "label": "Maize", "display": "MAIZE", "week": "2026-11-13", "slots": slots,
            "facts": facts, "allowed_names": ["United States", "China", "Brazil"], "all_region_names": ["Iowa", "Illinois"],
            "title": "Maize risk elevated: +2.10",
            "readings": {"maize": {"display": "MAIZE", "glyph": "maize", "text": "+2.10", "value": 2.1,
                                   "source": "risk_index.parquet", "date": "2026-11-13"},
                         "coffee": {"display": "ARABICA", "glyph": "arabica", "text": "+0.95", "value": 0.95,
                                    "source": "risk_index.parquet", "date": "2026-11-13"}}}


@pytest.fixture()
def note_row(payload):
    template = ("Maize harvest risk is elevated this week. The index stands at {RISK}, up {RISK_CHANGE} from four "
                "weeks ago. Expected world supply is {SUPPLY} against trend.\n\n"
                "The largest contributions come from {DRIVER1} ({DRIVER1_CONTRIB}) and {DRIVER2} ({DRIVER2_CONTRIB}). "
                "The most stressed producing region is {REGION1} ({REGION1_STRESS}).\n\n"
                "Futures settled at {PRICE}, {PRICE_CHANGE} over four weeks. Climate context: the El Niño reading "
                "is {ONI} ({ONI_PERIOD}), shown as background only.")
    return {"commodity": "maize", "week": pd.Timestamp("2026-11-13"), "title": payload["title"], "template": template,
            "markdown": "", "numbers_ok": True, "context_ok": True, "claims_ok": True, "model": "Qwen/Qwen2.5-1.5B-Instruct",
            "payload": json.dumps(payload), "seconds": 1.0, "attempts": 1, "failures": "[]"}
