"""Weekly note: payload -> local LLM writes text with slots -> software inserts sourced figures ->
three checks -> up to 2 retries -> deterministic template if the model keeps failing.

Output: data/processed/notes.parquet (commodity, week, title, template, markdown, numbers_ok, context_ok,
claims_ok, model, payload, seconds, attempts, failures).
"""

from __future__ import annotations


import json
import time
from importlib import resources

import pandas as pd

from harvestradar.config import Settings
from harvestradar.features.windows import window_open_on
from harvestradar.paths import PROCESSED
from harvestradar.report.checks import check_claims, check_context, check_numbers, fill
from harvestradar.signal.risk_index import country_name

FALLBACK_ID = "deterministic-template"


def fmt_signed(x: float, nd: int = 2, suffix: str = "") -> str:
    return f"{x:+.{nd}f}{suffix}"


def fmt_price(key: str, x: float) -> str:
    return f"{x:,.0f}" if key == "cocoa" else f"{x:,.2f}"


def level_word(z: float) -> str:
    return "elevated" if z >= 1 else ("below normal" if z <= -1 else "near normal")


def _top_regions(key: str, n: int = 3) -> tuple[list[dict], str, list[str]]:
    st = pd.read_parquet(PROCESSED / f"stress_{key}.parquet")
    rg = pd.read_parquet(PROCESSED / f"regions_{key}.parquet")
    last = st.dekad_end.max()
    s = st[st.dekad_end == last].merge(rg[["region_id", "adm1_name", "country_iso3", "weight"]], on="region_id")
    s["score"] = s["stress"].clip(lower=0) * s["weight"]
    top = s.sort_values("score", ascending=False).head(n)
    comp = pd.DataFrame({"heat": top[["tmax_z", "hdd_z"]].max(axis=1), "low rainfall": -top["precip_z"],
                         "dry soils": -top["sm_root_z"]})
    top = top.assign(cause=comp.idxmax(axis=1))
    return ([{"name": r.adm1_name, "country": r.country_iso3, "stress": float(r.stress), "cause": r.cause}
             for r in top.itertuples()],
            pd.Timestamp(last).strftime("%Y-%m-%d"), rg["adm1_name"].tolist())


def next_major_window(cfg: Settings, key: str, week: pd.Timestamp, contributors: list[dict]):
    """Next window to open among countries holding at least `major_share` of world supply."""
    c = cfg.commodities[key]
    major = float(cfg.index["major_share"]) * 100
    big = [ct["country"] for ct in json.loads(json.dumps(contributors)) if ct["share_pct"] >= major] or [c.main_country]
    best = None
    for ctry in big:
        for w in c.windows.get(ctry, []):
            for season in range(week.year - 1, week.year + 3):
                s0, _ = w.dates(season)
                if s0 > week.date() and (best is None or s0 < best[0]):
                    best = (s0, ctry, w.stage)
    if best is None:
        return None
    s0, ctry, stage = best
    return (f"{country_name(ctry)} {stage}", s0.strftime("%B %Y"), f"opens {s0.isoformat()}")


def build_payload(cfg: Settings, key: str, week: pd.Timestamp, risk: pd.DataFrame, prices: pd.DataFrame,
                  oni: pd.DataFrame) -> dict:
    c = cfg.commodities[key]
    r = risk[(risk.commodity == key) & (risk.date <= week)].sort_values("date")
    cur = r.iloc[-1]
    prev = r[r.date <= week - pd.Timedelta(weeks=4)].iloc[-1]
    px = prices[prices.date <= week].iloc[-1]
    px0 = prices[prices.date <= week - pd.Timedelta(weeks=4)].iloc[-1]
    o = oni[oni.available_at <= week].iloc[-1]
    wk = week.strftime("%Y-%m-%d")
    d = lambda ts: pd.Timestamp(ts).strftime("%Y-%m-%d")  # noqa: E731
    slots: dict[str, dict] = {
        "RISK": dict(kind="figure", text=fmt_signed(cur.risk_z), value=round(float(cur.risk_z), 2),
                     label=f"{c.display} harvest-risk index", source="risk_index.parquet", date=wk,
                     detail=f"week of {week.strftime('%d %b %Y')}"),
        "RISK_CHANGE": dict(kind="figure", text=f"{fmt_signed(cur.risk_z - prev.risk_z)} over four weeks",
                            value=round(float(cur.risk_z - prev.risk_z), 2), label="Change over four weeks",
                            source="risk_index.parquet", date=wk, detail=f"vs {d(prev.date)}"),
        "SUPPLY": dict(kind="figure", text=fmt_signed(cur.delta_prod_pct, 1, "%"),
                       value=round(float(cur.delta_prod_pct), 1), label="Expected world supply vs trend",
                       source="model predictions", date=wk,
                       detail=f"p10 / p90 band {cur.delta_prod_lo_pct:+.1f}% to {cur.delta_prod_hi_pct:+.1f}%"),
        "PRICE": dict(kind="figure", text=fmt_price(key, px.close), value=round(float(px.close), 2),
                      label=f"{c.price_name} close", source=f"prices_{key}.parquet", date=d(px.date),
                      detail=f"{c.price_name} close, {c.price_unit}"),
        "PRICE_CHANGE": dict(kind="figure", text=f"{fmt_signed(100 * (px.close / px0.close - 1), 1, '%')} over four weeks",
                             value=round(float(100 * (px.close / px0.close - 1)), 1), label="Price change, four weeks",
                             source=f"prices_{key}.parquet", date=d(px.date), detail=f"vs close of {d(px0.date)}"),
        "ONI": dict(kind="figure", text=fmt_signed(o.oni), value=round(float(o.oni), 2), label="El Niño (ONI)",
                    source="oni.parquet", date=d(o.available_at), detail=f"ONI {o.label}, NOAA CPC"),
        "ONI_PERIOD": dict(kind="label", text=f"ONI {o.label}", label="ONI season", source="oni.parquet",
                           date=d(o.available_at), detail="three-month season"),
    }
    contributors = json.loads(cur.contributors)
    drivers = []
    for i, ct in enumerate(contributors[:3], start=1):
        slots[f"DRIVER{i}"] = dict(kind="name", text=ct["name"], label=f"Contributor {i}",
                                   source="risk_index.parquet (contributors)", date=wk, detail=ct["country"])
        slots[f"DRIVER{i}_CONTRIB"] = dict(kind="figure", text=fmt_signed(ct["contrib_pct"], 2, " pp"),
                                           value=round(ct["contrib_pct"], 2), label=f"{ct['name']}, world supply",
                                           source="risk_index.parquet (contributors)", date=wk,
                                           detail=f"season {ct['season']}, share {ct['share_pct']:.1f}%")
        drivers.append({"slot": f"DRIVER{i}", "effect": "lowers supply" if ct["contrib_pct"] < 0
                        else "raises supply", "window_open": ct["window_open"]})
    regions, dekad, all_regions = _top_regions(key)
    for i, rg in enumerate(regions, start=1):
        slots[f"REGION{i}"] = dict(kind="name", text=rg["name"], label=f"Stressed region {i}",
                                   source=f"stress_{key}.parquet", date=dekad, detail=rg["country"])
        slots[f"REGION{i}_STRESS"] = dict(kind="figure", text=fmt_signed(rg["stress"], 1),
                                          value=round(rg["stress"], 1), label=f"{rg['name']} stress",
                                          source=f"stress_{key}.parquet", date=dekad,
                                          detail=f"dekad ending {dekad}, z vs 2001-2020")
    open_now = [f"{country_name(ctry)} ({w.stage})" for ctry, ws in c.windows.items()
                for w in ws if window_open_on(week.date(), [w])]
    nxt = next_major_window(cfg, key, week, contributors)
    if nxt:
        slots["NEXT_WINDOW"] = dict(kind="name", text=nxt[0], label="Next major critical window",
                                    source="config/commodities.yaml", date=wk, detail=nxt[2])
        slots["NEXT_WINDOW_MONTH"] = dict(kind="label", text=nxt[1], label="Opens in",
                                          source="config/commodities.yaml", date=wk, detail=nxt[2])
    facts = {"risk_z": float(cur.risk_z), "risk_change_4w": float(cur.risk_z - prev.risk_z),
             "delta_prod_pct": float(cur.delta_prod_pct),
             "price_change_4w_pct": float(100 * (px.close / px0.close - 1)), "oni": float(o.oni),
             "level": level_word(float(cur.risk_z)), "drivers": drivers, "windows_open": open_now,
             "oni_label": f"ONI {o.label}", "region_causes": {f"REGION{i}": rg["cause"]
                                                            for i, rg in enumerate(regions, start=1)}}
    names = [country_name(x) for x in c.countries] + [s.split(" (")[0] for s in open_now]
    readings = {}
    for k2, c2 in cfg.commodities.items():
        r2 = risk[(risk.commodity == k2) & (risk.date <= week)].dropna(subset=["risk_z"]).sort_values("date")
        if len(r2):
            readings[k2] = {"display": c2.display, "glyph": c2.glyph, "text": fmt_signed(r2.risk_z.iloc[-1]),
                            "value": round(float(r2.risk_z.iloc[-1]), 2), "source": "risk_index.parquet",
                            "date": r2.date.iloc[-1].strftime("%Y-%m-%d")}
    return {"commodity": key, "label": c.label, "display": c.display, "week": wk, "slots": slots,
            "readings": readings, "model_display": cfg.llm["display_name"],
            "facts": facts, "allowed_names": sorted(set(names)), "all_region_names": all_regions,
            "title": f"{c.label} risk {facts['level']}: {slots['RISK']['text']}"}


EXAMPLE = (
    "Cocoa harvest risk is near normal this week. The index reads {RISK}, a little lower than a month ago "
    "({RISK_CHANGE}), and expected world supply sits at {SUPPLY} against trend.\n\n"
    "Most of the movement comes from {DRIVER1}, at {DRIVER1_CONTRIB} of world supply, while {DRIVER2} adds "
    "{DRIVER2_CONTRIB}. Compared with their own history, the most stressed producing regions in the latest "
    "dekad were {REGION1} ({REGION1_STRESS}) and {REGION2} ({REGION2_STRESS}).\n\n"
    "The next period to watch is {NEXT_WINDOW}, which opens in {NEXT_WINDOW_MONTH}. Futures closed at {PRICE}, "
    "{PRICE_CHANGE} over four weeks. For context, the El Nino reading is {ONI} ({ONI_PERIOD}).")


def fact_sheet(p: dict) -> str:
    f = p["facts"]
    chg = "higher" if f["risk_change_4w"] > 0.05 else ("lower" if f["risk_change_4w"] < -0.05 else "about unchanged")
    sup = "below trend" if f["delta_prod_pct"] < 0 else "above trend"
    prc = "higher" if f["price_change_4w_pct"] > 0.5 else ("lower" if f["price_change_4w_pct"] < -0.5 else "flat")
    parts = [f"The commodity is {p['label']}. The harvest-risk index this week is {{RISK}}; its level is "
             f"{f['level']}. {{RISK_CHANGE}} is the change of the index over four weeks (not a level), so the "
             f"index is {chg} than a month ago. Expected world supply against trend is {{SUPPLY}}, which is {sup}. "
             "There is no information on how supply changed over time."]
    drv = []
    for d in f["drivers"]:
        s = d["slot"]
        drv.append(f"{{{s}}} contributes {{{s}_CONTRIB}} of world supply and {d['effect']}"
                   + (" (its critical window is open)" if d["window_open"] else ""))
    if drv:
        parts.append("The largest contributions to world supply (negative values lower supply and raise the risk, "
                     "positive values add supply and lower the risk): " + "; ".join(drv) + ".")
    if "REGION1" in p["slots"]:
        regs = [f"{{REGION{i}}} ({{REGION{i}_STRESS}}, mainly {f['region_causes'][f'REGION{i}']})"
                for i in range(1, 4) if f"REGION{i}" in p["slots"]]
        parts.append("The most stressed producing regions in the latest dekad, compared with their own history, "
                     "are " + ", ".join(regs) + ".")
    parts.append("Critical windows open now: " + (", ".join(f["windows_open"]) if f["windows_open"] else "none") + ".")
    if "NEXT_WINDOW" in p["slots"]:
        parts.append("The next major critical window to open is {NEXT_WINDOW}, in {NEXT_WINDOW_MONTH}.")
    parts.append(f"The futures price is {{PRICE}}, {{PRICE_CHANGE}} over four weeks ({prc}).")
    parts.append("Climate context only, not a driver of the index: the El Nino reading is {ONI} ({ONI_PERIOD}).")
    return " ".join(parts)


def user_prompt(p: dict) -> str:
    return ("FACT SHEET\n" + fact_sheet(p) + "\n\nEXAMPLE OF THE EXPECTED STYLE (another commodity, other facts; "
            "do not copy its facts):\n" + EXAMPLE + "\n\nNow write the note for " + p["label"] + ". Three short "
            "paragraphs of prose, no title, no list, no digits: copy the {SLOTS} exactly.")


def template_note(p: dict) -> str:
    f = p["facts"]
    chg = "up" if f["risk_change_4w"] > 0.05 else ("down" if f["risk_change_4w"] < -0.05 else "little changed")
    move = (f"{chg} {{RISK_CHANGE}}" if chg != "little changed" else "little changed over four weeks")
    first = (f"{p['label']} harvest risk is {f['level']} this week. The index stands at {{RISK}}, {move}. "
             f"Expected world supply is {{SUPPLY}} against trend.")
    drv = [d["slot"] for d in f["drivers"]]
    second = ""
    if drv:
        second = "The largest contributions to world supply come from " + " and ".join(
            f"{{{s}}} ({{{s}_CONTRIB}})" for s in drv[:2]) + "."
    if "REGION1" in p["slots"]:
        second += (" The most stressed producing regions in the latest dekad are {REGION1}, {REGION2} and {REGION3}."
                   if "REGION3" in p["slots"] else " The most stressed producing region in the latest dekad is {REGION1}.")
    wins = f["windows_open"]
    third = ("Critical windows open now: " + ", ".join(wins) + ". " if wins else
             "No critical window is open for the main producers this week. ")
    if "NEXT_WINDOW" in p["slots"]:
        third += "The next major window is {NEXT_WINDOW}, which opens in {NEXT_WINDOW_MONTH}. "
    third += ("Futures settled at {PRICE}, {PRICE_CHANGE}. "
              "Climate context: the El Niño reading is {ONI} ({ONI_PERIOD}), shown as background only.")
    return "\n\n".join(x.strip() for x in (first, second, third) if x.strip())


PARA_TASKS = [
    ("What the index says", "Write two sentences. First: the harvest-risk level this week with {RISK}, and how the "
     "index moved with {RISK_CHANGE}. Second: expected world supply against trend with {SUPPLY}.",
     "Cocoa harvest risk is near normal this week: the index reads {RISK}, {RISK_CHANGE}. Expected world supply "
     "sits at {SUPPLY} against trend."),
    ("Where the risk comes from", "Write two sentences. First: the countries with the largest contributions to "
     "world supply, each followed by its contribution slot in brackets. Second: the most stressed producing regions "
     "and the main cause given for them.",
     "The largest contributions to world supply come from {DRIVER1} ({DRIVER1_CONTRIB}) and {DRIVER2} "
     "({DRIVER2_CONTRIB}). The most stressed producing regions are {REGION1} and {REGION2}, mainly from heat."),
    ("What to watch", "Write two or three sentences: the critical windows (open now, or the next one), the futures "
     "price with {PRICE} and {PRICE_CHANGE}, and the El Nino reading {ONI} ({ONI_PERIOD}) as background only.",
     "No critical window is open this week; the next one is {NEXT_WINDOW}, in {NEXT_WINDOW_MONTH}. Futures closed "
     "at {PRICE}, {PRICE_CHANGE}. For background, the El Nino reading is {ONI} ({ONI_PERIOD})."),
]


def paragraph_prompt(p: dict, i: int) -> str:
    title, task, example = PARA_TASKS[i]
    return ("FACT SHEET\n" + fact_sheet(p) + f"\n\nTASK: paragraph {i + 1} of 3, '{title}'. {task}\n"
            "Rules: plain prose, no title, no list, no digits, copy each {SLOT} exactly and at most once, never "
            "write + or - in front of a slot, use only facts from the sheet.\n"
            f"EXAMPLE (another commodity, other facts, do not copy its facts): {example}\n\nParagraph:")


def run_checks(template: str, p: dict, min_words: int = 50, max_words: int = 220, require_index: bool = True) -> dict:
    n_ok, n_r = check_numbers(template, p)
    c_ok, c_r = check_context(template, p, min_words=min_words, max_words=max_words, require_index=require_index)
    k_ok, k_r = check_claims(template, p)
    return {"numbers_ok": n_ok, "context_ok": c_ok, "claims_ok": k_ok, "reasons": n_r + c_r + k_r}


def write_note(cfg: Settings, p: dict, deterministic: bool = False) -> dict:
    """Three paragraphs, each written by the model and checked on its own (2 retries); a paragraph that keeps
    failing is replaced by the matching paragraph of the deterministic template. The whole note is checked again."""
    from harvestradar.report import llm

    system = resources.files("harvestradar.report").joinpath("prompts/weekly_note_system.md").read_text()
    fallback = template_note(p).split("\n\n")
    t0 = time.time()
    failures, attempts, paras, from_template = [], 0, [], 0
    model_id = cfg.llm["model_id"]
    for i in range(3):
        text = None
        if not deterministic:
            for attempt in range(1 + int(cfg.llm["retries"])):
                attempts += 1
                try:
                    out = llm.generate(model_id, system, paragraph_prompt(p, i), 160,
                                       seed=int(cfg.seed) + 10 * i + attempt, sample=attempt > 0)
                except Exception as e:  # noqa: BLE001
                    failures.append(f"paragraph {i + 1}: generation error {e}")
                    break
                out = out.strip().strip('"').strip()
                res = run_checks(out, p, min_words=12, max_words=90, require_index=(i == 0))
                if res["numbers_ok"] and res["context_ok"] and res["claims_ok"]:
                    text = out
                    break
                failures.append(f"paragraph {i + 1}, attempt {attempt + 1}: " + "; ".join(res["reasons"][:4]))
        if text is None:
            text = fallback[i] if i < len(fallback) else ""
            from_template += 1
        paras.append(text)
    note = "\n\n".join(x for x in paras if x)
    res = run_checks(note, p)
    if not (res["numbers_ok"] and res["context_ok"] and res["claims_ok"]):
        failures.append("whole note: " + "; ".join(res["reasons"][:4]))
        note, from_template = template_note(p), 3
        res = run_checks(note, p)
    model = FALLBACK_ID if from_template == 3 else model_id
    return {"template": note, "model": model, "seconds": round(time.time() - t0, 1), "attempts": attempts,
            "template_paragraphs": from_template, "failures": failures, **res}


def build_notes(cfg: Settings, weeks: int | None = None, deterministic: bool = False) -> pd.DataFrame:
    risk = pd.read_parquet(PROCESSED / "risk_index.parquet")
    oni = pd.read_parquet(PROCESSED / "oni.parquet")
    n = int(weeks or cfg.llm["weeks"])
    end = pd.Timestamp(cfg.as_of_end)
    wk_list = [end - pd.Timedelta(weeks=i) for i in range(n)]
    rows = []
    for week in wk_list:
        for key in cfg.commodities:
            prices = pd.read_parquet(PROCESSED / f"prices_{key}.parquet")
            p = build_payload(cfg, key, week, risk, prices, oni)
            res = write_note(cfg, p, deterministic=deterministic)
            md = f"# {p['title']}\n\n" + fill(res["template"], p)
            rows.append({"commodity": key, "week": week, "title": p["title"], "template": res["template"],
                         "markdown": md, "numbers_ok": res["numbers_ok"], "context_ok": res["context_ok"],
                         "claims_ok": res["claims_ok"], "model": res["model"],
                         "payload": json.dumps(p, ensure_ascii=False), "seconds": res["seconds"],
                         "attempts": res["attempts"], "template_paragraphs": res["template_paragraphs"],
                         "failures": json.dumps(res["failures"])})
            print(f"[notes] {week.date()} {key}: {res['model']} in {res['seconds']}s, attempts {res['attempts']}, "
                  f"template paragraphs {res['template_paragraphs']}, "
                  f"checks {res['numbers_ok']}/{res['context_ok']}/{res['claims_ok']}"
                  + (f" | {res['failures']}" if res["failures"] else ""))
    df = pd.DataFrame(rows)
    df.to_parquet(PROCESSED / "notes.parquet", index=False)
    return df



