"""Weekly note as an email: a self-contained HTML email (inline CSS, table layout, 640 px, dark theme)
plus a plain-text alternative, written as .eml and .html. Offline: nothing is sent.

Every figure is taken from the note's own payload (slots and readings), never recomputed.
"""

from __future__ import annotations

import base64
import datetime as dt
import html as H
import json
import re
from email.message import EmailMessage
from email.utils import format_datetime
from importlib import resources
from pathlib import Path

import pandas as pd

from harvestradar.paths import DEMO, PROCESSED, ROOT
from harvestradar.report.checks import SLOT_RE, fill, split_figure

C = {"night": "#0B0F14", "console": "#131C27", "line": "#1E2935", "line_strong": "#2A3646", "frost": "#EAF0F5",
     "frost_2": "#C7D1DB", "muted": "#8A9AAB", "faint": "#6F7F90", "signal": "#FFB547", "heat": "#FF5A36"}
SANS = "Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
DISPLAY = "'Space Grotesk', Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', Menlo, Consolas, 'Courier New', monospace"
CHECKS = [("numbers_ok", "Numbers checked"), ("context_ok", "Context checked"), ("claims_ok", "Claims checked")]


def _logo_png() -> bytes:
    return resources.files("harvestradar.app").joinpath("static/brand/mark_on_signal_96.png").read_bytes()


def _pill(text: str, slot: str) -> str:
    return (f'<span data-fig="{slot}" style="font-family:{MONO};color:{C["signal"]};background:rgba(255,181,71,0.10);'
            f'border:1px solid rgba(255,181,71,0.55);border-radius:6px;padding:1px 6px;white-space:nowrap;'
            f'font-variant-numeric:tabular-nums;">{H.escape(text)}</span>')


def _body_html(template: str, payload: dict) -> str:
    paras = []
    for para in [p for p in template.split("\n\n") if p.strip()]:
        out, last = [], 0
        for m in SLOT_RE.finditer(para):
            out.append(H.escape(para[last:m.start()]))
            s = payload["slots"].get(m.group(1))
            if s is None:
                out.append(H.escape(m.group(0)))
            elif s["kind"] == "figure":
                pre, fig, rest = split_figure(s["text"])
                out.append(H.escape(pre) + (_pill(fig, m.group(1)) if fig else "") + H.escape(rest))
            else:
                out.append(f'<span style="color:{C["frost"]};font-weight:600;">{H.escape(s["text"])}</span>')
            last = m.end()
        out.append(H.escape(para[last:]))
        paras.append(f'<p style="margin:0 0 14px 0;font-family:{SANS};font-size:16px;line-height:26px;'
                     f'color:{C["frost_2"]};">{"".join(out)}</p>')
    return "".join(paras)


def _week_label(week: str) -> str:
    ts = pd.Timestamp(week)
    return f"{ts.day} {ts.strftime('%b %Y')}"


def render_note_email(note_row: dict | pd.Series, risk_rows: pd.DataFrame | None = None,
                      prices: dict | None = None, logo_src: str = "cid:hr-logo") -> str:
    """note_row: a row of notes.parquet. risk_rows and prices are accepted for API symmetry; the email uses
    the readings frozen in the note payload so that every figure matches the note."""
    row = dict(note_row)
    p = json.loads(row["payload"])
    week = p["week"]
    readings = "".join(
        f'<td width="33%" style="padding:0 5px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{C["console"]};'
        f'border:1px solid {C["line_strong"]};border-radius:12px;"><tr><td style="padding:12px 14px;">'
        f'<div style="font-family:{MONO};font-size:13px;letter-spacing:2px;color:{C["muted"]};">'
        f'{H.escape(r["display"])} &middot; RISK INDEX</div>'
        f'<div data-fig="READING_{k.upper()}" style="font-family:{MONO};font-size:28px;line-height:36px;'
        f'color:{C["signal"]};font-variant-numeric:tabular-nums;">{H.escape(r["text"])}</div>'
        f'</td></tr></table></td>' for k, r in p.get("readings", {}).items())
    checks = "".join(
        f'<span style="display:inline-block;margin:0 8px 6px 0;padding:4px 10px;border:1px solid {C["line_strong"]};'
        f'border-radius:999px;font-family:{SANS};font-size:13px;color:{C["frost_2"]};">'
        f'{"&#10003;" if row.get(k) else "&#10005;"} {label}</span>' for k, label in CHECKS)
    model = row.get("model", "")
    tp = int(row.get("template_paragraphs", 0) or 0)
    who = ("Written from the fixed template" if model == "deterministic-template"
           else f"Written by a small AI model running locally ({H.escape(p.get('model_display', model.split('/')[-1]))})"
           + (f"; {tp} of 3 paragraphs from the fixed template" if tp else ""))
    sources = "".join(
        f'<tr><td style="padding:6px 0;border-top:1px solid {C["line"]};font-family:{MONO};font-size:13px;'
        f'color:{C["signal"]};white-space:nowrap;" data-fig="{k}">{H.escape(s["text"])}</td>'
        f'<td style="padding:6px 10px;border-top:1px solid {C["line"]};font-family:{SANS};font-size:13px;'
        f'color:{C["frost_2"]};">{H.escape(s["label"])}</td>'
        f'<td style="padding:6px 0;border-top:1px solid {C["line"]};font-family:{MONO};font-size:13px;'
        f'color:{C["faint"]};">{H.escape(s["source"])} &middot; {H.escape(s["date"])}</td></tr>'
        for k, s in p["slots"].items() if s["kind"] == "figure")
    title = H.escape(row.get("title") or p["title"])
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><title>{title}</title></head>
<body style="margin:0;padding:0;background:{C["night"]};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{C["night"]};">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:640px;max-width:640px;
background:{C["console"]};border:1px solid {C["line_strong"]};border-radius:18px;">
<tr><td style="padding:24px 28px 8px 28px;">
 <table role="presentation" cellpadding="0" cellspacing="0"><tr>
  <td style="padding-right:14px;"><img src="{logo_src}" width="48" height="48" alt="HarvestRadar" style="display:block;border-radius:11px;"></td>
  <td><div style="font-family:{DISPLAY};font-size:22px;line-height:28px;font-weight:700;color:{C["frost"]};">{title}</div>
  <div style="font-family:{SANS};font-size:14px;color:{C["muted"]};">HarvestRadar Daily &middot; {_week_label(week)}</div></td>
 </tr></table>
</td></tr>
<tr><td style="padding:16px 23px 8px 23px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{readings}</tr></table></td></tr>
<tr><td style="padding:16px 28px 4px 28px;">{_body_html(row["template"], p)}</td></tr>
<tr><td style="padding:0 28px 6px 28px;">{checks}</td></tr>
<tr><td style="padding:0 28px 18px 28px;font-family:{MONO};font-size:13px;color:{C["muted"]};">{who}. Every figure is inserted by the software, with its source.</td></tr>
<tr><td style="padding:0 28px 20px 28px;">
 <div style="font-family:{MONO};font-size:13px;letter-spacing:2px;color:{C["muted"]};padding-bottom:6px;">SOURCES OF EVERY FIGURE</div>
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{sources}</table>
</td></tr>
<tr><td style="padding:14px 28px 22px 28px;border-top:1px solid {C["line"]};font-family:{MONO};font-size:13px;color:{C["faint"]};">
 Research output, not investment advice.<br>Produced offline by HarvestRadar. Nothing was sent by the app.
</td></tr>
</table></td></tr></table></body></html>"""


def render_text(note_row: dict | pd.Series) -> str:
    row = dict(note_row)
    p = json.loads(row["payload"])
    lines = [row.get("title") or p["title"], f"HarvestRadar Daily, {_week_label(p['week'])}", ""]
    lines += [f"{r['display']} risk index {r['text']}" for r in p.get("readings", {}).values()]
    lines += ["", fill(row["template"], p), ""]
    lines += ["Checks: " + ", ".join(f"{label} {'passed' if row.get(k) else 'FAILED'}" for k, label in CHECKS)]
    lines += ["", "Sources:"]
    lines += [f"  {s['text']}  {s['label']}  ({s['source']}, {s['date']})" for s in p["slots"].values()
              if s["kind"] == "figure"]
    lines += ["", "Research output, not investment advice."]
    return "\n".join(lines)


def write_eml(html: str, subject: str, week: str, commodity: str = "note", text: str = "",
              out_dir: Path | None = None, logo_png: bytes | None = None) -> Path:
    out_dir = Path(out_dir or ROOT / "reports" / "notes")
    out_dir.mkdir(parents=True, exist_ok=True)
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "HarvestRadar Daily <daily@harvestradar.invalid>"
    msg["To"] = "undisclosed-recipients:;"
    sent = dt.datetime.fromisoformat(f"{week}T07:00:00+00:00")  # 07:00 on the note's day, deterministic
    msg["Date"] = format_datetime(sent)
    msg["Message-ID"] = f"<{week}.{commodity}@harvestradar.invalid>"
    msg.set_content(text or re.sub(r"<[^>]+>", " ", html))
    msg.add_alternative(html, subtype="html")
    logo = logo_png if logo_png is not None else _logo_png()
    msg.get_payload()[1].add_related(logo, "image", "png", cid="<hr-logo>", filename="harvestradar.png")
    eml = out_dir / f"{week}_{commodity}.eml"
    eml.write_bytes(bytes(msg))
    data_uri = "data:image/png;base64," + base64.b64encode(logo).decode()
    (out_dir / f"{week}_{commodity}.html").write_text(html.replace("cid:hr-logo", data_uri), encoding="utf-8")
    return eml


def eml_bytes(note_row: dict | pd.Series) -> tuple[bytes, str]:
    """For the app download button: (bytes of the .eml, file name)."""
    import tempfile

    row = dict(note_row)
    p = json.loads(row["payload"])
    with tempfile.TemporaryDirectory() as d:
        path = write_eml(render_note_email(row), row.get("title") or p["title"], p["week"], row["commodity"],
                         render_text(row), Path(d))
        return path.read_bytes(), path.name


def load_notes() -> pd.DataFrame:
    for d in (DEMO, PROCESSED):
        if (d / "notes.parquet").exists():
            return pd.read_parquet(d / "notes.parquet")
    raise FileNotFoundError("notes.parquet not found: run `harvestradar report notes` first")


def export_week(week: str = "latest", out_dir: Path | None = None) -> list[Path]:
    notes = load_notes()
    notes["week"] = pd.to_datetime(notes["week"])
    wk = notes["week"].max() if week == "latest" else pd.Timestamp(week)
    sel = notes[notes["week"] == wk]
    if sel.empty:
        raise ValueError(f"no notes for week {week}")
    out = []
    for row in sel.to_dict("records"):
        p = json.loads(row["payload"])
        out.append(write_eml(render_note_email(row), row["title"], p["week"], row["commodity"], render_text(row),
                             out_dir))
    return out
