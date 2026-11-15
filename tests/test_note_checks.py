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


def test_semantic_errors_seen_in_real_notes_are_caught(payload):
    # the change read as a previous level
    assert not check_claims("The index stands at {RISK}, up from {RISK_CHANGE} four weeks ago.", payload)[0]
    # supply direction contradicting a negative SUPPLY figure
    assert not check_claims("This points to a higher-than-trend supply situation.", payload)[0]
    assert not check_claims("World supply is {SUPPLY} against trend, down from a month ago.", payload)[0]
    # a positive contribution presented as a risk
    payload["slots"]["DRIVER2_CONTRIB"]["value"] = 0.95
    assert not check_claims("The largest contributors to this risk are {DRIVER1} at {DRIVER1_CONTRIB} and "
                            "{DRIVER2} at {DRIVER2_CONTRIB}.", payload)[0]


def test_reused_figure_and_bold_heading_fail(payload):
    filler = " The weather was watched closely." * 12
    ok, reasons = check_context("**Maize Harvest Risk: Elevated**\n\nIndex {RISK}." + filler, payload)
    assert not ok and any("headings" in r for r in reasons)
    ok, reasons = check_context("Iowa reads {REGION1_STRESS}, mainly due to {REGION1_STRESS}. Index {RISK}." + filler,
                                payload)
    assert not ok and any("more than once" in r for r in reasons)
    ok, reasons = check_context("Index {RISK}. Strong demand and low stocks." + filler, payload)
    assert not ok


def test_more_real_errors_are_caught(payload):
    assert not check_numbers("Contributions: {DRIVER1} (-{DRIVER1_CONTRIB}).", payload)[0]
    assert not check_claims("The index is {RISK_CHANGE} above the trend line.", payload)[0]
    assert not check_claims("The El Nino reading is {ONI}, indicating low chances of impacts.", payload)[0]
    filler = " The weather was watched closely." * 12
    assert not check_context("Index {RISK}. Stay tuned for developments." + filler, payload)[0]


def test_contribution_direction_both_ways(payload):
    bad = ("{DRIVER1} ({DRIVER1_CONTRIB}) and {DRIVER2} ({DRIVER2_CONTRIB}) contribute negatively to world supply, "
           "lowering the risk.")
    assert not check_claims(bad, payload)[0]
