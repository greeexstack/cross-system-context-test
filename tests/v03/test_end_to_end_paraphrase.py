from __future__ import annotations

from datetime import datetime, timezone

import pytest

from experiment.v03.evidence import EvidenceCondition
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)


EVALUATION_AT = datetime(
    2026,
    9,
    13,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


PARAPHRASE_CASES = (
    (
        "F01",
        PrimaryState("quote_pending_decision"),
        (
            "The customer is assessing the proposal and would like "
            "another discussion next week.",
            "The proposal is being considered by the customer, who "
            "requested another conversation next week.",
            "The customer is evaluating the offer and wants to arrange "
            "a further discussion in the coming week.",
        ),
    ),
    (
        "F02",
        PrimaryState("quote_pending_decision"),
        (
            "The customer has budget approval for the quoted amount "
            "and says procurement is progressing.",
            "Budget has been authorized for the proposed amount, and "
            "the purchasing process is moving forward.",
            "The customer confirmed financial approval for the quote "
            "and indicated that procurement has begun advancing it.",
        ),
    ),
    (
        "F03",
        PrimaryState("negotiation_open"),
        (
            "The customer says the revised commercial terms are "
            "unacceptable and wants the proposal reconsidered.",
            "The customer rejected the revised commercial terms and "
            "wants the proposal reconsidered.",
            "The customer is not prepared to accept the revised terms "
            "and asked that the offer be reviewed again.",
        ),
    ),
    (
        "F04",
        PrimaryState("quote_pending_decision"),
        (
            "The customer is discussing a different store rollout "
            "and says nothing about this quoted opportunity.",
            "The conversation concerns another store rollout and "
            "contains no information about this proposal.",
            "The customer raised a separate rollout initiative without "
            "providing any update on the quoted opportunity.",
        ),
    ),
    (
        "F10",
        PrimaryState("service_completed_next_step_unrecorded"),
        (
            "The customer confirms the migration workshop is finished "
            "and asks what happens in the following handoff.",
            "The migration session is complete, and the customer wants "
            "to know the next stage of the handoff.",
            "The customer says the workshop is finished and is asking "
            "what should happen in the subsequent transition.",
        ),
    ),
)


def _evaluate(
    primary: PrimaryState,
    text: str,
):
    extractor = LexicalNormalizationSemanticExtractor()

    extracted = extractor.extract(
        evidence_id="PARAPHRASE",
        content=text,
        source_system="diagnostic",
        record_id="PARAPHRASE",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
    )

    condition = EvidenceCondition(
        availability="available",
        items=(extracted.evidence,),
    )

    reasoner = V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )

    return reasoner.evaluate(primary, condition)


def _observable_state(result) -> tuple:
    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


@pytest.mark.parametrize(
    "case_id,primary,texts",
    PARAPHRASE_CASES,
)
def test_end_to_end_behavior_is_invariant_across_paraphrases(
    case_id: str,
    primary: PrimaryState,
    texts: tuple[str, ...],
) -> None:
    results = [
        _evaluate(primary, text)
        for text in texts
    ]

    states = [
        _observable_state(result)
        for result in results
    ]

    assert all(state == states[0] for state in states), (
        f"{case_id}: end-to-end observable behavior changed "
        f"across semantically equivalent wording\n"
        f"states={states}"
    )


def test_paraphrase_experiment_preserves_fixed_input_metadata() -> None:
    extractor = LexicalNormalizationSemanticExtractor()

    texts = PARAPHRASE_CASES[0][2]

    extracted = [
        extractor.extract(
            evidence_id="PARAPHRASE",
            content=text,
            source_system="diagnostic",
            record_id="PARAPHRASE",
            occurred_at="2026-09-12T10:00:00Z",
            customer_id="C001",
        ).evidence
        for text in texts
    ]

    assert all(
        item.provenance.source_system == "diagnostic"
        for item in extracted
    )

    assert all(
        item.provenance.record_id == "PARAPHRASE"
        for item in extracted
    )

    assert all(
        item.identity.customer_id == "C001"
        for item in extracted
    )

    assert len(
        {
            item.timestamp
            for item in extracted
        }
    ) == 1