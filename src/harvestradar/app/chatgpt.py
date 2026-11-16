"""Ask ChatGPT: a link to chatgpt.com with the question and the page's figures already written.

Nothing is sent by the app itself: the viewer clicks the link and ChatGPT opens in a new tab (usable without
an account, within ChatGPT's own limits). Same wording as the web edition (web/app.js, gptPrompt).
"""

from __future__ import annotations

from urllib.parse import quote

from harvestradar.app import data

URL = "https://chatgpt.com/?q="
RULES = ("I am reading HarvestRadar, a research dashboard on weather risk for maize, arabica coffee and cocoa futures. "
         "Use the HarvestRadar figures below as given and say plainly when something is not in them (stocks, positioning, "
         "news). The risk index compares the expected world harvest with normal for the time of year: 0 = normal, above "
         "+2 = rare; it is a supply signal, weakly linked to prices week to week. The climate fair value is the 12-month "
         "average price moved by the price reaction to the expected world supply gap. Give trade ideas as scenarios with "
         "entry logic, invalidation level and risks, not personalised advice. Be brief and concrete; answer in the "
         "language of my question.")


def _fmt(key: str, x: float) -> str:
    return f"{x:,.0f}" if key == "cocoa" else f"{x:,.2f}"


def crop_line(key: str, asof, full: bool) -> str:
    m = data.meta()["commodities"][key]
    r = data.latest_risk(key, asof)
    pi = data.jsonfile("price_impact.json")
    fv = pi.get("fair_value", {}).get(key)
    s = (f"- {m['label']} ({m['price_name']}, {m['price_unit']}): risk index {r['risk_z']:+.2f}; expected world supply "
         f"{r['delta_prod_pct']:+.2f}% vs normal")
    if fv:
        s += (f"; last close {_fmt(key, fv['close'])}; climate fair value {_fmt(key, fv['fair'])} (80% range "
              f"{_fmt(key, fv['fair_lo'])} to {_fmt(key, fv['fair_hi'])}), price {fv['gap_to_fair_pct']:+.1f}% vs fair value; "
              f"price reaction {-fv['slope_pct_per_pct']:.2f}% per 1% of world supply missing"
              + ("" if fv["reliable"] else " (not statistically reliable)"))
    s += "."
    if full:
        s += "\n  Countries behind the reading (points of world supply): " + ", ".join(
            f"{c['name']} {c['contrib_pct']:+.2f}" + (" (critical window open)" if c["window_open"] else "")
            for c in r["contributors"][:4]) + "."
    return s


def chatgpt_url(question: str, key: str, page: str, asof) -> str:
    lines = [crop_line(k, asof, k == key) for k in data.meta()["commodities"]]
    prompt = (f"{RULES}\n\nHarvestRadar data of {asof.day} {asof:%B %Y}:\n" + "\n".join(lines)
              + f"\n\nI am looking at the {page} page, crop: {data.meta()['commodities'][key]['label']}.\n\nMy question: {question}")
    return URL + quote(prompt)
