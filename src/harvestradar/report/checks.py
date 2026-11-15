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


def split_figure(text: str) -> tuple[str, str]:
    """'+0.09 over four weeks' -> ('+0.09', ' over four weeks'): the figure goes in the pill, words stay text."""
    m = re.match(r"^\s*([-+]?[\d,]*\.?\d+(?:\s?(?:%|pp))?)(.*)$", text)
    return (m.group(1), m.group(2)) if m else (text, "")


def _num(s: str) -> float:
    return float(s.replace(",", "").replace("+", ""))


def extract_numbers(text: str) -> list[float]:
    return [_num(x) for x in NUM_RE.findall(text)]


def check_numbers(template: str, payload: dict) -> tuple[bool, list[str]]:
    reasons = []
    bare = SLOT_RE.sub(" ", template)
    if re.search(r"\d", bare):
        reasons.append("the model typed a digit")
    if re.search(r"[-+\u2212]\s?\{[A-Z]", template):
        reasons.append("a sign typed in front of a figure that already carries its sign")
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


def check_context(template: str, payload: dict, min_words: int = 50, max_words: int = 220,
                  require_index: bool = True) -> tuple[bool, list[str]]:
    reasons = []
    used = set(slots_in(template))
    unknown = used - set(payload["slots"])
    if unknown:
        reasons.append(f"unknown slots {sorted(unknown)}")
    if require_index and "RISK" not in used:
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
    if "#" in template or re.search(r"^\s*[-*] ", template, re.M) or re.search(r"^\s*\*\*[^*]+\*\*:?\s*$", template, re.M):
        reasons.append("headings or bullets")
    counts = {}
    for sl in slots_in(template):
        if sl in payload["slots"] and payload["slots"][sl]["kind"] == "figure":
            counts[sl] = counts.get(sl, 0) + 1
    reused = [k for k, v in counts.items() if v > 1]
    if reused:
        reasons.append(f"figure used more than once: {reused}")
    low = bare.lower()
    for concept in ("stay tuned", "stability", "coming months", "dynamics", "suggest", "demand", "consumption", "stockpile", "stocks", "inventor", "export", "import", "disease",
                    "pest", "tariff", "currency", "dollar", "speculat", "investor", "balanced market", "sentiment"):
        if concept in low:
            reasons.append(f"concept not in the fact sheet: {concept}")
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
    vals = {k: v.get("value") for k, v in payload["slots"].items() if v["kind"] == "figure"}
    for sent in re.split(r"(?<=[.!?])\s+", template):
        sl = set(slots_in(sent))
        lo_s = SLOT_RE.sub(" ", sent).lower()
        if re.search(r"\b(from|was|previous(ly)?)\s*\{RISK_CHANGE\}", sent):
            reasons.append("the four-week change is read as a previous level")
        if "RISK_CHANGE" in sl and "trend" in lo_s and "supply" not in lo_s:
            reasons.append("the four-week change is not described as a change over time")
        if re.search(r"el ni(n|ñ)o|\boni\b", lo_s) and re.search(
                r"\b(impact\w*|chance\w*|neutral|indicat\w*|suggest\w*|likely|effect\w*|affect\w*|influenc\w*|weak|strong|falls? into)\b", lo_s):
            reasons.append("El Nino reading interpreted beyond the fact sheet")
        if "supply" in lo_s and "price" not in lo_s and "futures" not in lo_s:
            if d < 0 and re.search(r"(higher|above|more|increas\w*|greater)[- ]?(than[- ]?)?(trend|usual|normal)?[- ]?supply|supply[^.]*\b(above|higher|increas\w*|surplus)", lo_s):
                reasons.append("supply said to be higher while the figure is below trend")
            if d > 0 and re.search(r"(lower|below|less|reduc\w*|short\w*)[- ]?(than[- ]?)?(trend|usual|normal)?[- ]?supply|supply[^.]*\b(below|lower|reduc\w*|shortfall|deficit)", lo_s):
                reasons.append("supply said to be lower while the figure is above trend")
            if re.search(r"(month ago|last month|four weeks|past weeks)", lo_s) and "index" not in lo_s:
                reasons.append("unsupported change in supply over time")
        contribs = [vals.get(k) for k in sl if k.startswith("DRIVER") and k.endswith("_CONTRIB")]
        contribs = [c for c in contribs if c is not None]
        if contribs and re.search(r"\b(risk|lower supply|reduc\w*|shortfall|decrease)", lo_s) and any(c > 0 for c in contribs):
            reasons.append("a supply-raising contribution is presented as a risk")
        if contribs and re.search(r"\b(increased supply|higher supply|surplus|adds? to supply)", lo_s) and any(c < 0 for c in contribs):
            reasons.append("a supply-lowering contribution is presented as adding supply")
    for clause in re.split(r"(?<=[.!?;])\s+", template):
        cl = SLOT_RE.sub(" ", clause).lower()
        cv = [vals.get(k) for k in slots_in(clause) if k.startswith("DRIVER") and k.endswith("_CONTRIB")]
        cv = [c for c in cv if c is not None]
        if any(c < 0 for c in cv) and re.search(r"lower(s|ing)? (the )?risk|reduc\w* (the )?risk|contribut\w* positively|"
                                                r"rais(e|es|ing) (world )?supply|add(s|ing)? (to )?supply", cl):
            reasons.append("a supply-lowering contribution is described as lowering the risk")
        if any(c > 0 for c in cv) and re.search(r"rais(e|es|ing) (the )?risk|contribut\w* negatively|"
                                                r"lower(s|ing)? (world )?supply", cl):
            reasons.append("a supply-raising contribution is described as raising the risk")
    if re.search(r"over four weeks,? (over|from|in|compared)|weeks over (the past )?four weeks", low):
        reasons.append("repeated timing phrase")
    causes = f.get("region_causes", {})
    for sent in re.split(r"(?<=[.!?])\s+", template):
        regs = [x for x in slots_in(sent) if re.fullmatch(r"REGION\d", x)]
        said = [c for c in ("heat", "dry soils", "low rainfall") if c in sent.lower()]
        if regs and len(said) == 1 and any(causes.get(r) and causes.get(r) != said[0] for r in regs):
            reasons.append(f"cause '{said[0]}' given for a region whose main cause differs")
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
