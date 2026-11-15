import re
from pathlib import Path

import pandas as pd
import pytest

from harvestradar.app.theme import RAMP, TOKENS, ramp, ramp_opacity
from harvestradar.paths import DEMO, ROOT

ALLOWED = {v.upper() for v in TOKENS.values()} | {c.upper() for _, c in RAMP} | {"#142030"}


def test_ramp_endpoints_and_opacity():
    assert ramp(-5) == (126, 176, 255) and ramp(0) == (30, 40, 51) and ramp(9) == (255, 90, 54)
    assert ramp_opacity(0) == pytest.approx(0.35) and ramp_opacity(3) == pytest.approx(1.0)


def test_only_design_tokens_are_used():
    """Section 3 of the app guidelines: grep for stray hex colours in the app and the email."""
    files = list((ROOT / "src/harvestradar/app").rglob("*.py")) + list((ROOT / "src/harvestradar/app/static/js").glob("*.js"))
    files += [ROOT / "src/harvestradar/report/email_note.py"]
    stray = {}
    for f in files:
        for h in re.findall(r"#[0-9A-Fa-f]{6}\b", f.read_text()):
            if h.upper() not in ALLOWED:
                stray.setdefault(str(f.relative_to(ROOT)), set()).add(h)
    assert not stray, stray


def test_no_em_dash_on_screen():
    for f in (ROOT / "src/harvestradar/app").rglob("*.py"):
        assert "—" not in f.read_text(), f


CONTRACTS = {
    "risk_index.parquet": ["commodity", "date", "risk_z", "delta_prod_pct", "coverage_share", "major_window_open",
                           "contributors"],
    "predictions.parquet": ["commodity", "country_iso3", "season", "date", "pred_anom", "pred_lo", "pred_hi",
                            "window_open"],
    "shap_latest.parquet": ["commodity", "country_iso3", "season", "as_of", "shap_hdd_z", "shap_oni"],
    "notes.parquet": ["commodity", "week", "markdown", "numbers_ok", "model", "payload", "seconds"],
}


@pytest.mark.skipif(not (DEMO / "meta.json").exists(), reason="no demo snapshot")
@pytest.mark.parametrize("name,cols", CONTRACTS.items())
def test_demo_contracts(name, cols):
    df = pd.read_parquet(DEMO / name)
    assert set(cols) <= set(df.columns)


@pytest.mark.skipif(not (DEMO / "meta.json").exists(), reason="no demo snapshot")
def test_demo_size_under_50mb():
    assert sum(p.stat().st_size for p in Path(DEMO).glob("*")) < 50e6
