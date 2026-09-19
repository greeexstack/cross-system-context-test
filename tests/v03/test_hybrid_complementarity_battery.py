from __future__ import annotations


# Fresh examples designed to test whether the two frozen extractors
# fail on complementary constructions.
#
# These examples are newly authored for this experiment and are not
# copied from the prior development batteries or the holdout.


HYBRID_BATTERY = (
    (
        "B1-followup",
        (
            (
                "The customer is keen to resume talks after the proposal "
                "is reviewed.",
                {"followup_request"},
            ),
            (
                "The buyer favors another discussion once finance signs off.",
                {"followup_request"},
            ),
            (
                "A further conversation was welcomed by the purchaser after "
                "the quotation review.",
                {"followup_request"},
            ),
            (
                "The client asked that negotiations continue next week.",
                {"followup_request"},
            ),
        ),
    ),
    (
        "B2-approval",
        (
            (
                "The purchasing request received authorization from finance.",
                {"budget_approved"},
            ),
            (
                "Finance gave formal clearance to the proposed expenditure.",
                {"budget_approved"},
            ),
            (
                "The quoted amount obtained budget approval.",
                {"budget_approved"},
            ),
            (
                "The spending request was approved by the finance committee.",
                {"budget_approved"},
            ),
        ),
    ),
    (
        "B3-rejection",
        (
            (
                "The buyer found the revised commercial terms unacceptable.",
                {"commercial_terms_rejected"},
            ),
            (
                "The revised conditions failed to satisfy the customer's "
                "requirements.",
                {"commercial_terms_rejected"},
            ),
            (
                "The client declined the amended proposal.",
                {"commercial_terms_rejected"},
            ),
            (
                "The buyer refused the revised arrangement.",
                {"commercial_terms_rejected"},
            ),
        ),
    ),
    (
        "B4-service",
        (
            (
                "The implementation session has ended, and the customer "
                "wants to understand the handoff.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The migration work is complete; guidance was requested "
                "for the subsequent transition.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The rollout is finished, and the client asked what follows.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The deployment workshop concluded, with the customer "
                "seeking information about the next transfer.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
        ),
    ),
)


def test_hybrid_battery_shape() -> None:
    assert len(HYBRID_BATTERY) == 4

    assert {
        family_id
        for family_id, _variants in HYBRID_BATTERY
    } == {
        "B1-followup",
        "B2-approval",
        "B3-rejection",
        "B4-service",
    }

    for family_id, variants in HYBRID_BATTERY:
        assert family_id.startswith("B")
        assert len(variants) == 4

        for text, expected_facts in variants:
            assert text.strip()
            assert expected_facts


def test_hybrid_battery_text_is_unique() -> None:
    texts = [
        text
        for _family_id, variants in HYBRID_BATTERY
        for text, _expected_facts in variants
    ]

    assert len(texts) == 16
    assert len(set(texts)) == 16


def test_hybrid_battery_contains_two_fact_service_cases() -> None:
    service_variants = next(
        variants
        for family_id, variants in HYBRID_BATTERY
        if family_id == "B4-service"
    )

    assert all(
        expected_facts
        == {
            "service_completed",
            "next_step_requested",
        }
        for _text, expected_facts in service_variants
    )