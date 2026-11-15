"""Guard rails for the weekly note.

numbers: the model types no digit; after the software inserts the figures, every number in the note
         exists in the payload (rounding tolerance).
context: only known slots are used, the index slot is present, no country or region outside the
         payload is named, length is within bounds.
claims:  direction words agree with the signs of the figures (level, change, supply, price), El Nino is
         never presented as the driver, no investment advice.
"""

from __future__ import annotations

import re
from functools import lru_cache

SLOT_RE = re.compile(r"\{([A-Z][A-Z0-9_]*)\}")
NUM_RE = re.compile(r"(?<![\w.])[-+]?\d[\d,]*(?:\.\d+)?")


def slots_in(template: str) -> list[str]:
    return SLOT_RE.findall(template)


def fill(template: str, payload: dict) -> str:
    return SLOT_RE.sub(lambda m: payload["slots"][m.group(1)]["text"] if m.group(1) in payload["slots"]
                       else m.group(0), template)


def _num(s: str) -> float:
    return float(s.replace(",", "").replace("+", ""))


def extract_numbers(text: str) -> list[float]:
    return [_num(x) for x in NUM_RE.findall(text)]


def check_numbers(template: str, payload: dict) -> tuple[bool, list[str]]:
    reasons = []
    bare = SLOT_RE.sub(" ", template)
    if re.search(r"\d", bare):
        reasons.append("the model typed a digit")
    allowed = []
    for s in payload["slots"].values():
        allowed += extract_numbers(s["text"])
    for x in extract_numbers(fill(template, payload)):
        if not any(abs(abs(x) - abs(a)) <= 0.006 * max(1.0, abs(a)) for a in allowed):
            reasons.append(f"number {x} not in payload")
    return (not reasons), reasons


@lru_cache(maxsize=1)
def _known_names() -> set[str]:
    import pycountry

    names = set()
    for c in pycountry.countries:
        for attr in ("name", "common_name", "official_name"):
            v = getattr(c, attr, None)
            if v:
                names.add(v)
    names |= {"United States", "US", "USA", "Russia", "Vietnam", "Ivory Coast", "Côte d'Ivoire", "China",
              "Brazil", "Argentina", "Ukraine", "India", "Mexico", "Ghana", "Indonesia", "Colombia",
              "Ethiopia", "Honduras", "Peru", "Nigeria", "Cameroon", "Ecuador", "Europe", "Africa",
              "Asia", "Iowa", "Illinois", "Mato Grosso", "Minas Gerais", "Corn Belt"}
    return names


def check_context(template: str, payload: dict, min_words: int = 50, max_words: int = 220) -> tuple[bool, list[str]]:
    reasons = []
    used = set(slots_in(template))
    unknown = used - set(payload["slots"])
    if unknown:
        reasons.append(f"unknown slots {sorted(unknown)}")
    if "RISK" not in used:
        reasons.append("index slot {RISK} missing")
    allowed = {s["text"] for s in payload["slots"].values() if s["kind"] == "name"}
    allowed |= set(payload.get("allowed_names", []))
    bare = SLOT_RE.sub(" ", template)
    for name in _known_names() | set(payload.get("all_region_names", [])):
        if len(name) < 4:
            continue
        if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", bare) and name not in allowed:
            reasons.append(f"name not in payload: {name}")
    n = len(fill(template, payload).split())
    if not (min_words <= n <= max_words):
        reasons.append(f"length {n} words")
    if "#" in template or re.search(r"^\s*[-*] ", template, re.M):
        reasons.append("headings or bullets")
    return (not reasons), reasons


DOWN = r"\b(eas(e|ed|ing)|fell|fall(en|ing)?|declin\w*|decreas\w*|drop\w*|lower\w*|soften\w*|weaken\w*)\b"
UP = r"\b(rose|ris(en|ing)|increas\w*|climb\w*|jump\w*|higher|rall\w*|surg\w*|strengthen\w*|up)\b"


def _sentences(text: str) -> list[str]:
    return [s.strip().lower() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def check_claims(template: str, payload: dict) -> tuple[bool, list[str]]:
    f = payload["facts"]
    text = fill(template, payload)
    low = text.lower()
    reasons = []
    z = f["risk_z"]
    if z >= 1 and re.search(r"\b(low risk|below normal|near normal|calm|subdued|minimal)\b", low):
        reasons.append("level contradicts an elevated index")
    if -1 < z < 1 and re.search(r"\b(elevated|high risk|severe|alarming|sharp)\b", low):
        reasons.append("level contradicts a near-normal index")
    if z <= -1 and re.search(r"\b(elevated|high risk|severe)\b", low):
        reasons.append("level contradicts a low index")
    d = f["delta_prod_pct"]
    if d < 0 and re.search(r"\b(above trend|surplus|bumper|larger than usual)\b", low):
        reasons.append("supply direction contradicts the figure")
    if d > 0 and re.search(r"\b(below trend|shortfall|deficit)\b", low):
        reasons.append("supply direction contradicts the figure")
    for s in _sentences(text):
        if ("index" in s or "risk" in s) and "price" not in s and "futures" not in s:
            ch = f["risk_change_4w"]
            if ch > 0.05 and re.search(DOWN, s) and "supply" not in s:
                reasons.append(f"index change direction: '{s[:60]}'")
            if ch < -0.05 and re.search(UP, s) and "supply" not in s:
                reasons.append(f"index change direction: '{s[:60]}'")
        if ("price" in s or "futures" in s) and "index" not in s and "risk" not in s:
            pc = f["price_change_4w_pct"]
            if pc > 0.5 and re.search(DOWN, s):
                reasons.append(f"price direction: '{s[:60]}'")
            if pc < -0.5 and re.search(UP, s):
                reasons.append(f"price direction: '{s[:60]}'")
    if re.search(r"el ni(n|ñ)o[^.]*\b(driv\w*|caus\w*|explain\w*|behind|push\w*|fuel\w*)", low) or \
            re.search(r"\b(driv\w*|caus\w*|explain\w*|fuel\w*)\b[^.]*el ni(n|ñ)o", low):
        reasons.append("El Nino presented as a driver")
    wins = f.get("windows_open", [])
    if wins and re.search(r"\bno (critical )?windows? (is |are )?open", low):
        reasons.append("says no window is open while one is")
    if not wins:
        for s in _sentences(text):
            if re.search(r"window[^.]*\b(is|are) (now |currently )?open\b|window[^.]*\bhas opened", s) and \
                    not re.search(r"\bno (critical )?windows?\b|\bnot open\b|\bnone\b", s):
                reasons.append("says a window is open while none is")
    if re.search(r"\bnext (month|week)\b|\bcoming weeks\b", low):
        reasons.append("unsupported timing")
    if re.search(r"el ni(n|ñ)o[^.]*\b(may|could|will|likely to|expected to)\b[^.]*\b(impact|affect|influenc\w*|hurt)", low):
        reasons.append("El Nino presented as an expected cause")
    if re.search(r"\b(buy|sell|hedg\w*|go long|go short|investors should|we recommend|recommend\w*)\b", low):
        reasons.append("investment advice")
    return (not reasons), reasons
