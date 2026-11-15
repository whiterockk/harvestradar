"""Write docs/storyboard_facts.md: the real value, from data/demo, behind every fact tag of the storyboard.
The storyboard's own numbers are illustrative; the video must use these."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "data" / "demo"


def main() -> None:
    meta = json.loads((DEMO / "meta.json").read_text())
    ev = json.loads((DEMO / "events.json").read_text())
    me = json.loads((DEMO / "model_eval.json").read_text())
    bt = json.loads((DEMO / "backtest.json").read_text())
    risk = pd.read_parquet(DEMO / "risk_index.parquet")
    risk["date"] = pd.to_datetime(risk["date"])
    today = risk.date.max()
    last = {r.commodity: r for r in risk[risk.date == today].itertuples()}
    oni = pd.read_parquet(DEMO / "oni.parquet")
    o = oni[pd.to_datetime(oni.available_at) <= today].iloc[-1]
    notes = pd.read_parquet(DEMO / "notes.parquet")
    notes["week"] = pd.to_datetime(notes["week"])
    nm = notes[(notes.week == notes.week.max())]
    e12, e21, ecc = ev["us_drought_2012"], ev["brazil_frost_2021"], ev["cocoa_2023_2024"]
    pooled = me["pooled"].get("end", {})
    cm = meta["commodities"]
    maize_contrib = json.loads(last["maize"].contributors)
    pr_c = pd.read_parquet(DEMO / "prices_cocoa.parquet")
    pr_c["date"] = pd.to_datetime(pr_c["date"])

    def close_on(df, d):
        x = df[df.date <= pd.Timestamp(d)].iloc[-1]
        return x.date.strftime("%Y-%m-%d"), float(x.close)

    c0 = close_on(pr_c, "2023-07-03")
    c1 = close_on(pr_c, "2024-12-31")
    rows = [
        ("F1", "2012 price window and peak", f"CBOT corn {e12['price_from']} on {e12['price_from_date']} "
         f"({e12['price_from_kind']}) to {e12['price_to']} on {e12['price_to_date']} ({e12['price_change_pct']:+.1f}%). "
         f"High of the episode {e12.get('price_max')} on {e12.get('price_max_date')}. Say \"by 20 July\", never \"peaked\"."),
        ("F2", "Date the 2012 index first crossed +2", f"{e12['first_above_2'] or 'never'}"
         + (f" ({e12.get('lead_text')})" if e12.get("lead_text") else "")
         + f"; peak {e12['peak_risk_z']:+.2f} on {e12['peak_date']}. The storyboard's 8 June is illustrative."),
        ("F3", "Out of sample", f"The 2012 forecasts come from a model trained on seasons up to "
         f"{e12.get('model_trained_on_seasons_up_to')} (FAOSTAT publishes year Y in December of Y+1). "
         f"Chip text: MODEL TRAINED ON SEASONS UP TO {e12.get('model_trained_on_seasons_up_to')}."),
        ("F4", "Model vs trend only", f"End of season, {me['test_seasons'][0]} to {me['test_seasons'][1]}: "
         f"{pooled.get('rmse_vs_trend_weighted_pct')}% RMSE weighted by world share, "
         f"{pooled.get('rmse_vs_trend_pct')}% with every country counted equally."),
        ("F5", "Share of weeks above +2 since 2001", ", ".join(f"{c['label']} {c['weeks_above_2_pct']}%" for c in cm.values())),
        ("F6", "Crop maps and weather points", f"{sum(c['regions'] for c in cm.values())} regions "
         f"({', '.join(str(c['regions']) + ' ' + c['label'].lower() for c in cm.values())}), each set covering 90% of "
         f"world output (MapSPAM 2020); {meta['cells']:,} NASA POWER grid points, daily since 1981."),
        ("F7", "Maize drivers this week", "; ".join(f"{c['name']} {c['contrib_pct']:+.2f} pp (crop {c['season']}, "
                                                    f"{c['pred_anom_pct']:+.1f}% vs trend)" for c in maize_contrib)),
        ("F8", "Readings today", f"week of {today:%d %b %Y}: " + ", ".join(
            f"{cm[k]['label']} {last[k].risk_z:+.2f} (supply {last[k].delta_prod_pct:+.1f}%)" for k in cm)),
        ("F9", "El Nino wording", f"ONI {o.label}: {o.oni:+.2f} (NOAA CPC, published {pd.Timestamp(o.available_at):%d %b %Y}). "
         "Context only: call it \"Climate driver\" or \"Context\", never \"driving the index\"."),
        ("F10", "Dekad of the stress map", f"latest complete dekad: {cm['maize']['latest_dekad_end']}"),
        ("F11", "Cocoa price definition", f"ICE cocoa front-month continuous (yfinance CC=F), US$ per tonne: "
         f"{c0[1]:,.0f} on {c0[0]} to {c1[1]:,.0f} on {c1[0]} (x{c1[1] / c0[1]:.2f})."),
        ("F12", "Brazil frost 2021", f"{e21['verdict'].upper()}: peak {e21['peak_risk_z']:+.2f} on {e21['peak_date']}"),
        ("F13", "Cocoa 2023-2024", f"{ecc['verdict'].upper()}: peak {ecc['peak_risk_z']:+.2f} on {ecc['peak_date']}"),
        ("F14", "2012", f"{e12['verdict'].upper()}"),
        ("F15", "Trading rule after costs", f"pre-registered rule: best p {bt['best_rule_p']:.2f} "
         f"({bt['best_rule_p_corrected']:.2f} after Bonferroni for 3 crops); best of the 3 x 3 grid "
         f"{bt['best_p_overall']:.3f} ({bt['best_p_overall_corrected']:.2f} corrected for 27 tests): no significant edge"),
        ("F16", "Critical windows (config)", "; ".join(
            f"{c['label']} {c['main_country_name']}: " + ", ".join(f"{w['stage']} {w['start']} to {w['end']}"
                                                                 for w in c['windows'][c['main_country']])
            for c in cm.values())),
        ("F17", "What it means for the price", "; ".join(
            f"{cm[k]['label']}: " + (f"{v['implied_pct']:+.1f}% expected (range {v['low_pct']:+.1f}% to {v['high_pct']:+.1f}%), "
                                    f"{-v['slope_pct_per_pct']:+.1f}% price per 1% of world supply missing, {v['years'][0]}-{v['years'][1]}"
                                    if v["reliable"] else "no reliable link, no estimate")
            for k, v in json.loads((DEMO / "price_impact.json").read_text())["commodities"].items())),
        ("F18", "Daily note labels", "; ".join(f"{r.commodity}: \"{r.title}\" ({r.model}, "
                                               f"{int(r.template_paragraphs)} of 3 paragraphs from the template, "
                                               f"checks {int(r.numbers_ok) + int(r.context_ok) + int(r.claims_ok)}/3)"
                                               for r in nm.itertuples())),
    ]
    out = ["# Storyboard facts, from the data", "",
           f"Generated by `scripts/storyboard_facts.py` from `data/demo` (as of {today:%d %b %Y}). The storyboard v3 "
           "numbers are illustrative; use these in the video.", "", "| Tag | Fact | Value from the data |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    (ROOT / "docs" / "storyboard_facts.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
