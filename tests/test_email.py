import email
import json
import re

from harvestradar.report.email_note import render_note_email, render_text, write_eml


def test_eml_parses_back_with_html_and_text(note_row, tmp_path):
    html = render_note_email(note_row)
    path = write_eml(html, note_row["title"], "2026-11-13", "maize", render_text(note_row), tmp_path)
    msg = email.message_from_bytes(path.read_bytes())
    types = [p.get_content_type() for p in msg.walk()]
    assert "text/plain" in types and "text/html" in types and "image/png" in types
    assert msg["Subject"] == note_row["title"]
    assert (tmp_path / "2026-11-13_maize.html").exists()


def test_every_figure_in_email_comes_from_payload(note_row):
    p = json.loads(note_row["payload"])
    html = render_note_email(note_row)
    figs = re.findall(r'data-fig="([A-Z0-9_]+)"[^>]*>([^<]+)<', html)
    assert figs
    allowed = {s["text"] for s in p["slots"].values()} | {r["text"] for r in p["readings"].values()}
    for slot, text in figs:
        assert text in allowed, (slot, text)
    # plain text: every number is a payload figure or part of the week label / ONI period
    txt = render_text(note_row)
    nums = re.findall(r"(?<![\w.])[-+]?\d[\d,]*(?:\.\d+)?", txt.split("\n", 2)[2])
    payload_nums = set()
    for s in list(p["slots"].values()) + list(p["readings"].values()):
        payload_nums |= set(re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", s["text"] + " " + s.get("date", "")))
    for n in nums:
        assert n in payload_nums or n.lstrip("+-") in {x.lstrip("+-") for x in payload_nums}, n


def test_email_html_is_offline(note_row):
    html = render_note_email(note_row)
    assert "http://" not in html and "https://" not in html
