from __future__ import annotations


# Fresh construction-generalization battery.
#
# These examples are NOT copied from the development battery or holdout.
# They target construction classes suggested by the frozen v2 holdout
# failures.
#
# Expected facts are evaluation metadata only.


CONSTRUCTION_BATTERY = (
    (
        "C1-followup-interest",
        "quote_pending_decision",
        (
            (
                "The buyer indicated that another conversation would be useful "
                "after the committee review.",
                {"followup_request"},
            ),
            (
                "The customer would be happy to reconnect once the proposal "
                "has been reconsidered.",
                {"followup_request"},
            ),
            (
                "The purchaser expressed interest in continuing the discussion "
                "next week.",
                {"followup_request"},
            ),
            (
                "The client signaled a preference for a further call after "
                "the pricing review.",
                {"followup_request"},
            ),
        ),
    ),
    (
        "C2-followup-suggestion",
        "quote_pending_decision",
        (
            (
                "The buyer suggested another conversation after the internal "
                "review.",
                {"followup_request"},
            ),
            (
                "The customer proposed speaking again once the figures are "
                "checked.",
                {"followup_request"},
            ),
            (
                "The purchaser recommended a further discussion later in "
                "the week.",
                {"followup_request"},
            ),
            (
                "The client put forward the idea of reconnecting after the "
                "committee meets.",
                {"followup_request"},
            ),
        ),
    ),
    (
        "C3-institutional-approval",
        "quote_pending_decision",
        (
            (
                "The finance office issued authorization for the proposed "
                "purchase.",
                {"budget_approved"},
            ),
            (
                "Funding for the quoted package received formal sign-off "
                "from finance.",
                {"budget_approved"},
            ),
            (
                "The proposed expenditure was sanctioned by the approval "
                "committee.",
                {"budget_approved"},
            ),
            (
                "Finance cleared the requested spend under the approved "
                "allocation.",
                {"budget_approved"},
            ),
        ),
    ),
)


def test_construction_battery_shape() -> None:
    assert len(CONSTRUCTION_BATTERY) == 3

    assert {
        family_id
        for family_id, _primary_state, _variants in CONSTRUCTION_BATTERY
    } == {
        "C1-followup-interest",
        "C2-followup-suggestion",
        "C3-institutional-approval",
    }

    for family_id, primary_state, variants in CONSTRUCTION_BATTERY:
        assert family_id.startswith("C")
        assert isinstance(primary_state, str)
        assert len(variants) == 4

        for text, expected_facts in variants:
            assert text.strip()
            assert expected_facts


def test_construction_battery_has_unique_text() -> None:
    texts = [
        text
        for _family_id, _primary_state, variants in CONSTRUCTION_BATTERY
        for text, _expected_facts in variants
    ]

    assert len(texts) == 12
    assert len(set(texts)) == 12


def test_construction_battery_has_required_construction_classes() -> None:
    observed = {
        family_id
        for family_id, _primary_state, _variants in CONSTRUCTION_BATTERY
    }

    assert observed == {
        "C1-followup-interest",
        "C2-followup-suggestion",
        "C3-institutional-approval",
    }