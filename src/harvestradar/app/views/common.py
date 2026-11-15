"""Shared page pieces: the live ticker and navigation callbacks."""

from __future__ import annotations

import streamlit as st

from harvestradar.app import components as C
from harvestradar.app import data

CROPS = ("maize", "coffee", "cocoa")


def set_crop(key: str) -> None:
    st.session_state.crop = key
    st.session_state.q_country = None


def go(page: str, **kw) -> None:
    st.session_state.nav = page
    st.session_state.page = page
    for k, v in kw.items():
        st.session_state[k] = v


def ticker() -> None:
    """Three glass cards, one per commodity; clicking a card selects it."""
    m = data.meta()["commodities"]
    asof = st.session_state.asof
    cols = st.columns(3)
    for col, key in zip(cols, CROPS):
        c = m[key]
        r = data.latest_risk(key, asof)
        s = data.risk_series(key, 26, asof)
        val = data.fmt_signed(r.get("risk_z")) if r else "n/a"
        with col:
            st.markdown(C.ticker_card(c["display"], c["glyph"], val, s["risk_z"].tolist(),
                                      key == st.session_state.crop, bool(r) and r["risk_z"] >= 2),
                        unsafe_allow_html=True)
            st.button(f"Select {c['label']}", key=f"pick_{key}", on_click=set_crop, args=(key,),
                      use_container_width=True)


def source(text: str) -> str:
    return f'<div class="hr-source">{text}</div>'
