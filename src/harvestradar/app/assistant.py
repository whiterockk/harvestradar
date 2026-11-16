"""In-app assistant: the question is answered in the page by the local Qwen model (the one that writes the
daily notes), from the page's figures. Free, no account, nothing leaves the computer once the model is in the
Hugging Face cache. Without the optional LLM dependencies, a link to ask ChatGPT in a new tab is offered
instead. Same instructions and data as the web edition (web/app.js, contextText)."""

from __future__ import annotations

from urllib.parse import quote

from harvestradar.app import data

URL = "https://chatgpt.com/?q="
RULES = ("You are the HarvestRadar assistant, inside a research dashboard on weather risk for maize, arabica coffee and "
         "cocoa futures. Use only the HarvestRadar figures below for numbers, and say plainly when something is not in "
         "them (stocks, positioning, news). The risk index compares the expected world harvest with normal for the time "
         "of year: 0 = normal, above +2 = rare; it moves with the weather and is weakly linked to prices week to week. "
         "Less supply than normal (index above 0) tends to push prices up; more supply pushes them down. "
         "The climate fair value is the 12-month average price moved by the price reaction to the expected world supply "
         "gap. Give trade ideas as scenarios with entry logic, invalidation level and risks, never personalised advice. "
         "Answer in at most 150 words, in the language of the question.")


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


def context(key: str, page: str, asof) -> str:
    lines = [crop_line(k, asof, k == key) for k in data.meta()["commodities"]]
    return (f"{RULES}\n\nHarvestRadar data of {asof.day} {asof:%B %Y}:\n" + "\n".join(lines)
            + f"\n\nThe user is looking at the {page} page, crop: {data.meta()['commodities'][key]['label']}.")


def chatgpt_url(question: str, key: str, page: str, asof) -> str:
    return URL + quote(context(key, page, asof) + f"\n\nMy question: {question}")


def local_model_available() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        return False
    return True


def answer_local(question: str, key: str, page: str, asof) -> str:
    from harvestradar.config import get_config
    from harvestradar.report.llm import generate

    model_id = get_config().llm["model_id"]
    return generate(model_id, context(key, page, asof), question, max_new_tokens=320)
