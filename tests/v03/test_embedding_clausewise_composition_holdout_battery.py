from __future__ import annotations


CLAUSEWISE_COMPOSITION_HOLDOUT = (
    (
        "CH1-budget-procurement",
        (
            (
                "Finance approved the requested expenditure; procurement then opened the order.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
            (
                "After the spending request received financial approval, procurement began processing the order.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
            (
                "The proposed funding was cleared, while the purchasing team moved into processing.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
            (
                "With the expenditure authorized, the sourcing workflow began handling the purchase.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
        ),
    ),
    (
        "CH2-service-next-step",
        (
            (
                "The implementation finished; the customer then asked about the next stage.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "After the deployment concluded, the customer asked what would happen next.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The migration work is complete, and the client requested guidance on the subsequent transition.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "With the onboarding exercise completed, the customer requested information about the ensuing handoff.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
        ),
    ),
    (
        "CH3-rejection-followup",
        (
            (
                "The revised commercial terms were rejected; the buyer requested another discussion.",
                {
                    "commercial_terms_rejected",
                    "followup_request",
                },
            ),
            (
                "Although the customer rejected the amended arrangement, the customer asked to revisit the proposal.",
                {
                    "commercial_terms_rejected",
                    "followup_request",
                },
            ),
            (
                "The buyer declined the updated conditions, and requested that negotiations continue later.",
                {
                    "commercial_terms_rejected",
                    "followup_request",
                },
            ),
            (
                "After rejecting the revised deal, the client asked for a further conversation.",
                {
                    "commercial_terms_rejected",
                    "followup_request",
                },
            ),
        ),
    ),
    (
        "CH4-budget-next-step",
        (
            (
                "The proposed expenditure was approved, and the customer asked about the next phase.",
                {
                    "budget_approved",
                    "next_step_requested",
                },
            ),
            (
                "Once the funding request was cleared, the customer requested guidance on what comes next.",
                {
                    "budget_approved",
                    "next_step_requested",
                },
            ),
            (
                "Financial authorization was granted; the client then asked about the subsequent step.",
                {
                    "budget_approved",
                    "next_step_requested",
                },
            ),
            (
                "With funding approved, the buyer wanted to know what should happen after this point.",
                {
                    "budget_approved",
                    "next_step_requested",
                },
            ),
        ),
    ),
    (
        "CH5-procurement-followup",
        (
            (
                "Procurement began processing the order; the buyer also requested another conversation.",
                {
                    "procurement_progressing",
                    "followup_request",
                },
            ),
            (
                "After purchasing started work on the request, the customer asked to discuss the proposal again.",
                {
                    "procurement_progressing",
                    "followup_request",
                },
            ),
            (
                "The sourcing workflow moved into processing, while the client requested a further discussion.",
                {
                    "procurement_progressing",
                    "followup_request",
                },
            ),
            (
                "With the purchase request under active handling, the buyer wanted the proposal conversation resumed.",
                {
                    "procurement_progressing",
                    "followup_request",
                },
            ),
        ),
    ),
)


def test_clausewise_composition_holdout_shape() -> None:
    assert len(CLAUSEWISE_COMPOSITION_HOLDOUT) == 5

    texts = [
        text
        for _family_id, variants in CLAUSEWISE_COMPOSITION_HOLDOUT
        for text, _expected_facts in variants
    ]

    assert len(texts) == 20
    assert len(set(texts)) == 20

    for family_id, variants in CLAUSEWISE_COMPOSITION_HOLDOUT:
        assert family_id.startswith("CH")
        assert len(variants) == 4

        for text, expected_facts in variants:
            assert text.strip()
            assert expected_facts


def test_clausewise_composition_holdout_contains_varied_constructions() -> None:
    texts = [
        text
        for _family_id, variants in CLAUSEWISE_COMPOSITION_HOLDOUT
        for text, _expected_facts in variants
    ]

    assert any(";" in text for text in texts)
    assert any(", and " in text for text in texts)
    assert any(", while " in text for text in texts)
    assert any(text.startswith("After ") for text in texts)
    assert any(text.startswith("Although ") for text in texts)
    assert any(text.startswith("With ") for text in texts)
    assert any(text.startswith("Once ") for text in texts)