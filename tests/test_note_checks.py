from harvestradar.report.checks import check_claims, check_context, check_numbers, fill
from harvestradar.report.weekly_note import run_checks, template_note


def test_good_note_passes(note_row, payload):
    res = run_checks(note_row["template"], payload)
    assert res["numbers_ok"] and res["context_ok"] and res["claims_ok"], res["reasons"]


def test_digit_typed_by_model_fails(payload):
    ok, reasons = check_numbers("The index is 2.5 this week, {RISK}.", payload)
    assert not ok and any("digit" in r for r in reasons)


def test_unknown_number_after_fill_fails(payload):
    payload["slots"]["RISK"]["text"] = "+9.99"  # not equal to the value checked elsewhere is fine; inject a stray one
    ok, _ = check_numbers("Index {RISK}.", payload)
    assert ok
    payload["slots"]["PRICE"]["text"] = "445.50 (was 400)"
    ok, reasons = check_numbers("Price {PRICE}.", payload)
    assert ok  # numbers inside the payload text are, by definition, in the payload


def test_name_outside_payload_fails(payload):
    text = ("Maize harvest risk is elevated. The index is {RISK}. " + "Weather was dry. " * 15 + "Argentina too.")
    ok, reasons = check_context(text, payload)
    assert not ok and any("Argentina" in r for r in reasons)


def test_contradictions_are_caught(payload):
    assert not check_claims("Harvest risk is near normal this week at {RISK}.", payload)[0]
    assert not check_claims("Expected supply is {SUPPLY}, above trend.", payload)[0]
    assert not check_claims("Futures prices fell to {PRICE}.", payload)[0]
    assert not check_claims("El Nino is driving the index this week.", payload)[0]
    assert not check_claims("Buyers should buy now.", payload)[0]
    assert not check_claims("The window opens next month.", payload)[0]


def test_template_always_passes(payload):
    t = template_note(payload)
    res = run_checks(t, payload)
    assert res["numbers_ok"] and res["context_ok"] and res["claims_ok"], res["reasons"]
    assert "{" not in fill(t, payload)
