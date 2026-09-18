
from __future__ import annotations


# Fresh development battery for the next extraction hypothesis.
#
# Design goals:
# - independently authored wording
# - different vocabulary from the earlier holdout/development batteries
# - clause-local relationships rather than simple keyword co-occurrence
# - active/passive alternation
# - noun/verb alternation
# - auxiliary/modal constructions
# - implied subjects where natural
# - distractor language from other semantic families
# - positive and negative controls
#
# IMPORTANT:
# These expected facts are test-side evaluation metadata only.
# They are NOT inputs to any extractor or reasoner.


DEVELOPMENT_BATTERY = (
    (
        "D1-followup",
        "quote_pending_decision",
        (
            (
                "The buyer asked for a call after the review committee meets.",
                {
                    "followup_request",
                },
            ),
            (
                "A further conversation was requested once the committee "
                "had completed its review.",
                {
                    "followup_request",
                },
            ),
            (
                "After the committee convenes, please circle back with the "
                "customer about the proposal.",
                {
                    "followup_request",
                },
            ),
            (
                "The client would like the discussion resumed after the "
                "committee's review of the offer.",
                {
                    "followup_request",
                },
            ),
        ),
    ),
    (
        "D2-supporting",
        "quote_pending_decision",
        (
            (
                "Budget authorization has been granted, and procurement "
                "has started its intake.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
            (
                "The proposed spend was cleared; the purchasing team is "
                "now opening the order.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
            (
                "Funding for the bid received sign-off, with the buying "
                "team proceeding.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
            (
                "The amount has been released under the approved budget, "
                "while sourcing has begun.",
                {
                    "budget_approved",
                    "procurement_progressing",
                },
            ),
        ),
    ),
    (
        "D3-contradictory",
        "negotiation_open",
        (
            (
                "The revised commercial terms do not work for the client, "
                "so the arrangement needs to be reopened.",
                {
                    "commercial_terms_rejected",
                },
            ),
            (
                "The customer turned down the amended deal and asked for "
                "a new set of terms.",
                {
                    "commercial_terms_rejected",
                },
            ),
            (
                "The altered conditions were rejected by the buyer; "
                "another proposal is needed.",
                {
                    "commercial_terms_rejected",
                },
            ),
            (
                "The client is unwilling to proceed on the revised "
                "commercial arrangement.",
                {
                    "commercial_terms_rejected",
                },
            ),
        ),
    ),
    (
        "D4-irrelevant",
        "quote_pending_decision",
        (
            (
                "A separate regional launch received its own budget approval; "
                "the current quote was not discussed.",
                {
                    "different_work_item",
                },
            ),
            (
                "The customer reviewed another branch's installation plan, "
                "while this opportunity remained untouched.",
                {
                    "different_work_item",
                },
            ),
            (
                "Purchasing is progressing on an unrelated site, with no "
                "information about the present proposal.",
                {
                    "different_work_item",
                },
            ),
            (
                "The buyer is dealing with a separate deployment and has "
                "not addressed this quotation.",
                {
                    "different_work_item",
                },
            ),
        ),
    ),
    (
        "D5-service-next-step",
        "service_completed_next_step_unrecorded",
        (
            (
                "After the installation session ended, the customer asked "
                "what the handover would look like.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The onboarding workshop has been completed; the client "
                "asked for guidance on the next transition.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The migration exercise is over, and the customer wants "
                "the subsequent transfer explained.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
            (
                "The rollout session concluded, and the client is asking "
                "what happens after the handoff.",
                {
                    "service_completed",
                    "next_step_requested",
                },
            ),
        ),
    ),
)


EXPECTED_FAMILIES = {
    "D1-followup",
    "D2-supporting",
    "D3-contradictory",
    "D4-irrelevant",
    "D5-service-next-step",
}


def test_clause_local_development_battery_shape() -> None:
    assert len(DEVELOPMENT_BATTERY) == 5

    family_ids = {
        family_id
        for family_id, _primary_state, _variants in DEVELOPMENT_BATTERY
    }

    assert family_ids == EXPECTED_FAMILIES

    for family_id, primary_state, variants in DEVELOPMENT_BATTERY:
        assert family_id.startswith("D")
        assert isinstance(primary_state, str)
        assert len(variants) == 4

        for text, expected_facts in variants:
            assert text.strip()
            assert expected_facts


def test_clause_local_development_battery_has_no_duplicate_variants() -> None:
    texts = [
        text
        for _family_id, _primary_state, variants in DEVELOPMENT_BATTERY
        for text, _expected_facts in variants
    ]

    assert len(texts) == 20
    assert len(set(texts)) == 20


def test_clause_local_development_battery_has_fifteen_behavioral_pairs() -> None:
    total_pairs = 0

    for _family_id, _primary_state, variants in DEVELOPMENT_BATTERY:
        baseline = variants[0][0]

        assert baseline

        total_pairs += len(variants) - 1

    assert total_pairs == 15


def test_clause_local_development_battery_covers_required_semantic_families() -> None:
    expected_by_family = {
        "D1-followup": {"followup_request"},
        "D2-supporting": {
            "budget_approved",
            "procurement_progressing",
        },
        "D3-contradictory": {
            "commercial_terms_rejected",
        },
        "D4-irrelevant": {"different_work_item"},
        "D5-service-next-step": {
            "service_completed",
            "next_step_requested",
        },
    }

    observed = {
        family_id: {
            fact
            for _text, expected_facts in variants
            for fact in expected_facts
        }
        for family_id, _primary_state, variants in DEVELOPMENT_BATTERY
    }

    assert observed == expected_by_family


def test_clause_local_development_battery_contains_positive_and_negative_controls() -> None:
    irrelevant = next(
        variants
        for family_id, _primary_state, variants in DEVELOPMENT_BATTERY
        if family_id == "D4-irrelevant"
    )

    assert all(
        "different_work_item" in expected_facts
        for _text, expected_facts in irrelevant
    )

    positive_families = {
        family_id
        for family_id, _primary_state, variants in DEVELOPMENT_BATTERY
        if any(
            fact != "different_work_item"
            for _text, expected_facts in variants
            for fact in expected_facts
        )
    }

    assert positive_families == {
        "D1-followup",
        "D2-supporting",
        "D3-contradictory",
        "D5-service-next-step",
    }