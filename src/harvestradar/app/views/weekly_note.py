"""Weekly note page: inbox of notes, the selected note with figure pills (from its own payload), the three
checks, the data given to the model, and the email export."""

from __future__ import annotations

import html as H
import json

import pandas as pd
import streamlit as st

from harvestradar.app import components as C
from harvestradar.app import data
from harvestradar.app.theme import T
from harvestradar.app.views.common import go
from harvestradar.report.checks import SLOT_RE
from harvestradar.report.email_note import eml_bytes

ORDER = {"maize": 0, "coffee": 1, "cocoa": 2}


def body_html(template: str, payload: dict) -> str:
    paras = []
    for para in [p for p in template.split("\n\n") if p.strip()]:
        out, last = [], 0
        for m in SLOT_RE.finditer(para):
            out.append(H.escape(para[last:m.start()]))
            s = payload["slots"].get(m.group(1))
            if s is None:
                out.append(H.escape(m.group(0)))
            elif s["kind"] == "figure":
                out.append(f'<span class="hr-pill" title="{H.escape(s["source"])} · {H.escape(s["date"])}">'
                           f'{H.escape(s["text"])}</span>')
            else:
                out.append(f'<span style="color:{T["frost"]};font-weight:600">{H.escape(s["text"])}</span>')
            last = m.end()
        out.append(H.escape(para[last:]))
        paras.append(f'<p style="font-size:18px;line-height:1.75;color:{T["frost_2"]};margin:0 0 14px 0">{"".join(out)}</p>')
    return "".join(paras)


def _select(k: str) -> None:
    st.session_state.note_sel = k


def render() -> None:
    n = data.notes()
    if n.empty:
        st.info("notes.parquet is missing from data/demo: run `harvestradar report notes`.")
        return
    n = n[n.week <= st.session_state.asof]
    weeks = sorted(n.week.unique(), reverse=True)
    q = st.session_state.get("q_week")
    if "note_sel" not in st.session_state:
        wk = pd.Timestamp(q) if q else weeks[0]
        st.session_state.note_sel = f"{pd.Timestamp(wk):%Y-%m-%d}|{st.session_state.crop}"
    left, right = st.columns([0.29, 0.71])
    with left:
        st.markdown('<div style="display:flex;justify-content:space-between;align-items:baseline;margin:4px 4px 6px 4px">'
                    '<span style="font-family:Space Grotesk,sans-serif;font-weight:700;font-size:28px">Inbox</span>'
                    '<span class="hr-caps">FRIDAY 07:00</span></div>', unsafe_allow_html=True)
        for wk in weeks:
            rows = n[n.week == wk].sort_values("commodity", key=lambda s: s.map(ORDER))
            for r in rows.itertuples():
                k = f"{pd.Timestamp(wk):%Y-%m-%d}|{r.commodity}"
                active = st.session_state.note_sel == k
                tag = ('<div style="margin-top:6px"><span class="hr-chip" style="padding:3px 8px;font-size:13px">'
                       'DETERMINISTIC-TEMPLATE</span></div>' if r.model == "deterministic-template" else "")
                bg = "background:rgba(255,181,71,.08);border-color:rgba(255,181,71,.6);" if active else ""
                st.markdown(
                    f'<div class="hr-glass" style="height:96px;padding:12px 16px;display:flex;gap:14px;{bg}">'
                    f'<span style="border-radius:10px;overflow:hidden;display:inline-flex;flex:none;height:40px">'
                    f'{C.mark_on_signal(40)}</span><div style="flex:1;min-width:0">'
                    f'<div style="display:flex;justify-content:space-between"><span style="font-weight:600;font-size:16px">'
                    f'HarvestRadar Weekly</span><span class="hr-mono" style="font-size:13px;color:{T["muted"]}">'
                    f'{pd.Timestamp(wk):%d %b}</span></div>'
                    f'<div style="font-size:15px;color:{T["frost_2"]};white-space:nowrap;overflow:hidden;'
                    f'text-overflow:ellipsis">{H.escape(r.title)}</div>{tag}</div></div>', unsafe_allow_html=True)
                st.button(f"Open {r.title}", key=f"pickn_{k}", on_click=_select, args=(k,), use_container_width=True)
    wk_s, key = st.session_state.note_sel.split("|")
    sel = n[(n.week == pd.Timestamp(wk_s)) & (n.commodity == key)]
    if sel.empty:
        sel = n[n.week == weeks[0]].head(1)
    row = sel.iloc[0]
    p = json.loads(row.payload)
    m = data.meta()
    with right:
        with st.container(key="glass_note"):
            st.markdown(
                f'<div style="display:flex;gap:16px;align-items:center;margin-bottom:6px">'
                f'<span style="border-radius:12px;overflow:hidden;display:inline-flex;flex:none">{C.mark_on_signal(52)}</span>'
                f'<div><div style="font-family:Space Grotesk,sans-serif;font-weight:700;font-size:30px;line-height:1.15">'
                f'{H.escape(row.title)}</div><div style="font-size:16px;color:{T["muted"]}">HarvestRadar Weekly &middot; '
                f'week of {pd.Timestamp(p["week"]).day} {pd.Timestamp(p["week"]):%b %Y}</div></div></div>',
                unsafe_allow_html=True)
            cols = st.columns(3)
            for col, (k2, rd) in zip(cols, p.get("readings", {}).items()):
                s = data.risk_series(k2, 26, pd.Timestamp(rd["date"]))
                with col:
                    st.markdown(C.ticker_card(rd["display"], rd["glyph"], rd["text"], s["risk_z"].tolist(), k2 == key,
                                              rd["value"] >= 2, spark_w=96), unsafe_allow_html=True)
            st.markdown(body_html(row.template, p), unsafe_allow_html=True)
            checks = (C.badge("Numbers checked", bool(row.numbers_ok)) + C.badge("Context checked", bool(row.context_ok))
                      + C.badge("Claims checked", bool(row.claims_ok)))
            who = ("Deterministic template, the model failed the checks" if row.model == "deterministic-template"
                   else f"Written by {m['llm']['display_name']}, local")
            st.markdown(f'<div style="display:flex;flex-wrap:wrap;align-items:center">{checks}'
                        f'<span class="hr-mono" style="font-size:13px;color:{T["muted"]};margin-left:6px">{who} '
                        f'&middot; figures inserted by software</span></div>', unsafe_allow_html=True)
            b1, b2, _ = st.columns([0.2, 0.24, 0.56])
            with b1:
                st.button("Open the map", key="open_map", on_click=go, args=("stress",),
                          kwargs={"crop": key}, use_container_width=True)
            with b2:
                content, fname = eml_bytes(row.to_dict())
                st.download_button("Download as email", data=content, file_name=fname, mime="message/rfc822",
                                   key="download_eml", use_container_width=True)
        with st.expander("Data given to the model", expanded=st.session_state.get("q_data") == "1"):
            figs = [(k, s) for k, s in p["slots"].items() if s["kind"] == "figure"]
            cards = "".join(
                f'<div class="hr-glass" style="padding:14px 16px"><div class="hr-mono" style="font-size:24px;'
                f'color:{T["signal"]}">{H.escape(s["text"])}</div><div style="font-size:15px;color:{T["frost_2"]};'
                f'margin-top:4px">{H.escape(s["label"])}</div><div class="hr-source" style="margin-top:6px">source '
                f'&middot; {H.escape(s["source"])}<br>{H.escape(s["date"])} &middot; {H.escape(s.get("detail", ""))}</div></div>'
                for _, s in figs)
            st.markdown(f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">{cards}</div>'
                        f'<div class="hr-source">INSERTED BY SOFTWARE, WITH SOURCE &middot; notes.parquet payload '
                        f'&middot; generated in {row.seconds:.0f} s, {int(row.attempts)} model attempt(s)</div>',
                        unsafe_allow_html=True)
