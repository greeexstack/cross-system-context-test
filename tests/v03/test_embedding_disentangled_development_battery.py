from __future__ import annotations


DISENTANGLED_DEVELOPMENT_BATTERY = (
    (
        "DD1-followup",
        (
            (
                "The account team would like to reconnect with the buyer after the review.",
                {"followup_request"},
            ),
            (
                "The customer requested another conversation about the quotation next week.",
                {"followup_request"},
            ),
            (
                "The purchaser asked that the proposal discussion resume on Monday.",
                {"followup_request"},
            ),
            (
                "The client wants to continue the quotation discussion after internal review.",
                {"followup_request"},
            ),
        ),
    ),
    (
        "DD2-budget",
        (
            (
                "The finance office authorized the requested expenditure.",
                {"budget_approved"},
            ),
            (
                "The proposed spend received financial approval.",
                {"budget_approved"},
            ),
            (
                "Funding authority signed off on the requested amount.",
                {"budget_approved"},
            ),
            (
                "The finance committee approved the planned outlay.",
                {"budget_approved"},
            ),
        ),
    ),
    (
        "DD3-procurement",
        (
            (
                "The purchasing desk has begun processing the request.",
                {"procurement_progressing"},
            ),
            (
                "The procurement team is now working through the order.",
                {"procurement_progressing"},
            ),
            (
                "The sourcing workflow has moved into active processing.",
                {"procurement_progressing"},
            ),
            (
                "The buying operation has started handling the purchase.",
                {"procurement_progressing"},
            ),
        ),
    ),
    (
        "DD4-rejection",
        (
            (
                "The customer rejected the revised commercial arrangement.",
                {"commercial_terms_rejected"},
            ),
            (
                "The purchaser would not accept the amended pricing terms.",
                {"commercial_terms_rejected"},
            ),
            (
                "The client declined the new commercial conditions.",
                {"commercial_terms_rejected"},
            ),
            (
                "The buyer ruled out the revised deal and asked for alternatives.",
                {"commercial_terms_rejected"},
            ),
        ),
    ),
    (
        "DD5-different-work-item",
        (
            (
                "The discussion concerns a different customer deployment, not this quotation.",
                {"different_work_item"},
            ),
            (
                "The team is addressing another site and has not discussed the current proposal.",
                {"different_work_item"},
            ),
            (
                "The update relates to a separate rollout rather than this opportunity.",
                {"different_work_item"},
            ),
            (
                "The buyer is dealing with another installation and gave no update on this quote.",
                {"different_work_item"},
            ),
        ),
    ),
    (
        "DD6-service-completed",
        (
            (
                "The implementation exercise has been completed.",
                {"service_completed"},
            ),
            (
                "The deployment activity is now finished.",
                {"service_completed"},
            ),
            (
                "The migration session has concluded.",
                {"service_completed"},
            ),
            (
                "The onboarding work has been wrapped up.",
                {"service_completed"},
            ),
        ),
    ),
    (
        "DD7-next-step",
        (
            (
                "The customer asked what the next stage will involve.",
                {"next_step_requested"},
            ),
            (
                "The client requested information about what comes next.",
                {"next_step_requested"},
            ),
            (
                "The buyer wants guidance on the subsequent step.",
                {"next_step_requested"},
            ),
            (
                "The customer asked for an explanation of the next phase.",
                {"next_step_requested"},
            ),
        ),
    ),
)


EXPECTED_FACTS = {
    "DD1-followup": {"followup_request"},
    "DD2-budget": {"budget_approved"},
    "DD3-procurement": {"procurement_progressing"},
    "DD4-rejection": {"commercial_terms_rejected"},
    "DD5-different-work-item": {"different_work_item"},
    "DD6-service-completed": {"service_completed"},
    "DD7-next-step": {"next_step_requested"},
}


def test_disentangled_development_battery_shape() -> None:
    assert len(DISENTANGLED_DEVELOPMENT_BATTERY) == 7

    family_ids = {
        family_id
        for family_id, _variants in DISENTANGLED_DEVELOPMENT_BATTERY
    }

    assert family_ids == set(EXPECTED_FACTS)

    texts = [
        text
        for _family_id, variants in DISENTANGLED_DEVELOPMENT_BATTERY
        for text, _expected_facts in variants
    ]

    assert len(texts) == 28
    assert len(set(texts)) == 28


def test_disentangled_development_battery_is_single_fact_only() -> None:
    for family_id, variants in DISENTANGLED_DEVELOPMENT_BATTERY:
        expected = EXPECTED_FACTS[family_id]

        for _text, facts in variants:
            assert facts == expected
            assert len(facts) == 1


def test_each_fact_has_four_independent_positive_examples() -> None:
    for family_id, variants in DISENTANGLED_DEVELOPMENT_BATTERY:
        expected = EXPECTED_FACTS[family_id]

        assert len(variants) == 4

        for _text, facts in variants:
            assert facts == expected


def test_development_facts_are_no_longer_perfectly_cooccurring() -> None:
    fact_sets = [
        facts
        for _family_id, variants in DISENTANGLED_DEVELOPMENT_BATTERY
        for _text, facts in variants
    ]

    singleton_facts = {
        next(iter(facts))
        for facts in fact_sets
    }

    assert singleton_facts == {
        "followup_request",
        "budget_approved",
        "procurement_progressing",
        "commercial_terms_rejected",
        "different_work_item",
        "service_completed",
        "next_step_requested",
    }