"""Small HTML blocks (rendered with st.markdown(..., unsafe_allow_html=True)). Typed arguments, no data
access here: pages pass in values read from data/demo."""

from __future__ import annotations

import html as H
import re
from functools import lru_cache
from importlib import resources

import numpy as np

from harvestradar.app.theme import GLASS, T

E = H.escape


@lru_cache(maxsize=16)
def _svg(name: str) -> str:
    s = resources.files("harvestradar.app").joinpath(f"static/brand/{name}.svg").read_text()
    return re.sub(r"\s+", " ", s).strip()


def glyph(kind: str, size: int = 22, color: str = T["frost"]) -> str:
    s = _svg(f"glyph_{kind}")
    s = re.sub(r'width="\d+" height="\d+"', f'width="{size}" height="{size}"', s, count=1)
    return f'<span style="color:{color};display:inline-flex;flex:none">{s}</span>'


def mark(size: int = 30) -> str:
    s = _svg("mark_small")
    return re.sub(r'width="\d+" height="\d+"', f'width="{size}" height="{size}"', s, count=1)


def mark_on_signal(size: int = 40) -> str:
    s = _svg("mark_on_signal")
    return re.sub(r'width="\d+" height="\d+"', f'width="{size}" height="{size}"', s, count=1)


def brand() -> str:
    return f'<div class="hr-topbar"><div class="hr-brand">{mark(30)}<span>Harvest<b>Radar</b></span></div></div>'


def status(week_label: str) -> str:
    return (f'<div class="hr-status"><span class="hr-dot"></span><span>LIVE &middot; WEEK OF {E(week_label.upper())}'
            f' &middot; OFFLINE</span></div>')


def _smooth_path(xs: np.ndarray, ys: np.ndarray) -> str:
    pts = list(zip(xs, ys))
    if len(pts) < 2:
        return ""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, len(pts)):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        cx = (x0 + x1) / 2
        d += f" C{cx:.1f},{y0:.1f} {cx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
    return d


def sparkline(values: list[float], w: int = 120, h: int = 40, color: str = T["signal"], fill: bool = True,
              dot: bool = True, pad: int = 5, ref: float | None = None) -> str:
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)], dtype=float)
    if len(v) < 2:
        return f'<svg width="{w}" height="{h}"></svg>'
    lo, hi = float(v.min()), float(v.max())
    if ref is not None:
        lo, hi = min(lo, ref), max(hi, ref)
    if hi - lo < 1e-9:
        hi = lo + 1
    xs = np.linspace(pad, w - pad, len(v))
    ys = h - pad - (v - lo) / (hi - lo) * (h - 2 * pad)
    d = _smooth_path(xs, ys)
    uid = abs(hash((tuple(np.round(v, 3)), w, h, color))) % 10**8
    area = (f'<path d="{d} L{xs[-1]:.1f},{h} L{xs[0]:.1f},{h} Z" fill="url(#sg{uid})"/>' if fill else "")
    refline = ""
    if ref is not None:
        ry = h - pad - (ref - lo) / (hi - lo) * (h - 2 * pad)
        refline = (f'<line x1="{pad}" x2="{w - pad}" y1="{ry:.1f}" y2="{ry:.1f}" stroke="{T["line_strong"]}" '
                   f'stroke-dasharray="3 4"/>')
    end = (f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="3.6" fill="{color}" '
           f'style="filter:drop-shadow(0 0 5px {color})"/>' if dot else "")
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-hidden="true"><defs>'
            f'<linearGradient id="sg{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{color}" '
            f'stop-opacity=".28"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
            f'{refline}{area}<path d="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
            f'{end}</svg>')


def ticker_card(display: str, glyph_kind: str, value: str, series: list[float], selected: bool,
                glow: bool, spark_w: int = 132) -> str:
    border = "border-color:rgba(255,181,71,.55);box-shadow:0 0 0 1px rgba(255,181,71,.25), 0 20px 60px rgba(0,0,0,.35);" \
        if selected else ""
    g = "hr-glow" if glow else ""
    return (f'<div class="hr-glass" style="height:88px;padding:14px 20px;display:flex;align-items:center;gap:16px;{border}">'
            f'{glyph(glyph_kind, 26, T["frost_2"])}'
            f'<div style="flex:1;min-width:0"><div class="hr-caps" style="white-space:nowrap">{E(display)} &middot; RISK_Z</div>'
            f'<div class="hr-mono {g}" style="font-size:32px;line-height:40px;color:{T["signal"]};font-weight:500">{E(value)}</div></div>'
            f'{sparkline(series, spark_w, 46)}</div>')


def stat_card(label: str, value: str, sub: str = "", color: str = T["frost"], height: int = 164,
              size: int = 34) -> str:
    return (f'<div class="hr-glass" style="height:{height}px;padding:20px 24px">'
            f'<div class="hr-caps">{E(label)}</div>'
            f'<div class="hr-mono" style="font-size:{size}px;line-height:1.25;color:{color};margin-top:12px;font-weight:500">{E(value)}</div>'
            f'<div class="hr-source" style="margin-top:6px">{sub}</div></div>')


def hero_card(display: str, glyph_kind: str, value: str, sub: str, height: int = 164) -> str:
    return (f'<div class="hr-glass" style="height:{height}px;padding:18px 24px;display:flex;align-items:center;gap:22px">'
            f'{glyph(glyph_kind, 52, T["frost_2"])}'
            f'<div><div class="hr-caps">{E(display)} &middot; HARVEST-RISK INDEX</div>'
            f'<div class="hr-mono hr-glow" style="font-size:72px;line-height:1;color:{T["signal"]};font-weight:500;'
            f'margin-top:6px">{E(value)}</div><div class="hr-source" style="margin-top:8px">{sub}</div></div></div>')


def panel(title: str, body: str, source: str = "", height: int | None = None, extra: str = "") -> str:
    h = f"height:{height}px;" if height else ""
    src = f'<div class="hr-source">{source}</div>' if source else ""
    return (f'<div class="hr-glass" style="{h}display:flex;flex-direction:column;{extra}">'
            f'<div class="hr-caps" style="margin-bottom:12px">{title}</div><div style="flex:1">{body}</div>{src}</div>')


def ranking_rows(rows: list[dict], glyph_kind: str) -> str:
    """rows: rank, name, iso, frac (0-1 of the top score), hot (bool)."""
    out = []
    for r in rows:
        end = T["heat"] if r["hot"] else T["signal"]
        out.append(
            f'<div style="display:grid;grid-template-columns:34px 26px 1fr auto;align-items:center;gap:6px 10px;'
            f'margin-bottom:10px">'
            f'<span class="hr-mono" style="font-size:13px;color:{T["muted"]}">{r["rank"]:02d}</span>'
            f'{glyph(glyph_kind, 18, T["frost_2"])}'
            f'<span style="font-size:16px;color:{T["frost"]};white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{E(r["name"])}</span>'
            f'<span class="hr-mono" style="font-size:13px;color:{T["muted"]}">{E(r["iso"])}</span>'
            f'<span></span><span></span>'
            f'<div style="grid-column:3 / span 2;height:4px;border-radius:3px;background:{T["line"]}">'
            f'<div style="width:{max(3, 100 * r["frac"]):.0f}%;height:4px;border-radius:3px;'
            f'background:linear-gradient(90deg,#8A6424,#F5A93A 70%,{end});box-shadow:0 0 8px rgba(255,181,71,.35)"></div></div>'
            f'</div>')
    return "".join(out)


def climate_card(value: str, period: str, series: list[float], source: str) -> str:
    return (f'<div class="hr-glass" style="height:176px;padding:18px 20px">'
            f'<div class="hr-caps">CLIMATE DRIVER &middot; CONTEXT</div>'
            f'<div style="font-family:Space Grotesk,sans-serif;font-weight:700;font-size:22px;margin-top:8px;color:{T["frost"]}">El Niño</div>'
            f'<div style="display:flex;align-items:flex-end;justify-content:space-between;gap:12px">'
            f'<div><span class="hr-mono" style="font-size:30px;color:{T["signal"]}">{E(value)}</span>'
            f'<span class="hr-mono" style="font-size:13px;color:{T["muted"]};margin-left:10px;letter-spacing:.08em">{E(period)}</span></div>'
            f'{sparkline(series, 200, 48)}</div>'
            f'<div class="hr-source" style="margin-top:6px">{source}</div></div>')


def note_ready(passed: int, total: int, label: str) -> str:
    return (f'<div class="hr-glass" style="height:88px;padding:16px 20px;display:flex;align-items:center;gap:16px">'
            f'<span style="flex:none;border-radius:10px;overflow:hidden;display:inline-flex">{mark_on_signal(40)}</span>'
            f'<div><div style="font-size:17px;color:{T["frost"]};font-weight:500">{E(label)}</div>'
            f'<div class="hr-mono" style="font-size:13px;color:{T["muted"]}">{passed}/{total} checks passed</div></div>'
            f'<div style="margin-left:auto" class="hr-mono"><span style="font-size:13px;color:{T["signal"]}">OPEN &rarr;</span></div></div>')


def bar_rows(rows: list[dict], unit: str = "pp", max_abs: float | None = None, label_w: int = 180) -> str:
    """Diverging bars: risk-raising (negative supply) in amber, risk-lowering in blue.
    rows: label, value (signed), raises_risk (bool), note (optional)."""
    if not rows:
        return f'<div style="color:{T["muted"]};font-size:15px">No data.</div>'
    m = max_abs or max(abs(r["value"]) for r in rows) or 1.0
    out = []
    for r in rows:
        frac = min(1.0, abs(r["value"]) / m)
        amber = r["raises_risk"]
        bg = ("linear-gradient(90deg,#8A6424,#F5A93A)" if amber else "#3F74D8")
        glow = "0 0 12px rgba(255,181,71,.45)" if amber else "0 0 10px rgba(63,116,216,.4)"
        bar = (f'<div style="height:12px;width:{max(2, 100 * frac):.1f}%;border-radius:7px;background:{bg};'
               f'box-shadow:{glow};{"margin-left:auto" if not amber else ""}"></div>')
        left = bar if not amber else ""
        right = bar if amber else ""
        note = f'<div class="hr-mono" style="font-size:13px;color:{T["muted"]}">{E(r["note"])}</div>' if r.get("note") else ""
        out.append(
            f'<div style="display:grid;grid-template-columns:{label_w}px 1fr 1fr 84px;align-items:center;gap:10px;'
            f'min-height:44px">'
            f'<div><div style="font-size:16px;color:{T["frost"]};white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{E(r["label"])}</div>{note}</div>'
            f'<div style="display:flex">{left}</div><div style="display:flex;border-left:1px solid {T["line_strong"]}">{right}</div>'
            f'<div class="hr-mono" style="text-align:right;font-size:15px;color:{T["signal"] if amber else T["frost_2"]}">'
            f'{r["value"]:+.2f}{(" " + unit) if unit else ""}</div></div>')
    return "".join(out)


def legend_risk(low: str = "lower risk", high: str = "higher risk", width: int = 36) -> str:
    sw = "".join(f'<i style="width:{width}px;height:8px;border-radius:3px;display:block;background:{c}"></i>' for c in
                 ["#7EB0FF", "#3F74D8", "#26406A", "#1E2833", "#8A6424", "#F5A93A", "#FF5A36"])
    return (f'<div><div style="display:flex;gap:4px">{sw}</div><div class="hr-mono" style="display:flex;'
            f'justify-content:space-between;font-size:13px;color:{T["muted"]};margin-top:5px"><span>{low}</span>'
            f'<span>{high}</span></div></div>')


def chip(text: str, amber: bool = False) -> str:
    return f'<span class="hr-chip{" amber" if amber else ""}">{E(text)}</span>'


def badge(text: str, ok: bool) -> str:
    icon = "&#10003;" if ok else "&#10005;"
    color = T["frost_2"] if ok else T["heat"]
    return (f'<span style="display:inline-flex;align-items:center;gap:7px;padding:6px 12px;border-radius:999px;'
            f'border:1px solid {T["line_strong"]};background:rgba(19,28,39,.7);font-size:15px;color:{color};'
            f'margin:0 8px 8px 0"><span style="color:{T["signal"] if ok else T["heat"]}">{icon}</span>{E(text)}</span>')


def glass_open(extra: str = "") -> str:
    return f'<div style="{GLASS}{extra}">'
