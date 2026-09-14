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


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _condition(
    text: str,
    *,
    customer_id: str = "C001",
    occurred_at: str | None = "2026-09-12T10:00:00Z",
):
    extractor = LexicalNormalizationSemanticExtractor()

    evidence = extractor.extract(
        evidence_id="TRANSITION",
        content=text,
        source_system="diagnostic",
        record_id="TRANSITION",
        occurred_at=occurred_at,
        customer_id=customer_id,
    ).evidence

    return EvidenceCondition(
        availability="available",
        items=(evidence,),
    )


def _state(result) -> tuple:
    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


CASES = (
    (
        "MR1-relevant",
        PrimaryState("quote_pending_decision"),
        (
            "The customer wants another discussion about the proposal next week.",
        ),
        {
            "interpretation_class": "quote_followup_pending",
            "support_level": "supported_by_secondary_context",
        },
    ),
    (
        "MR2-supporting",
        PrimaryState("quote_pending_decision"),
        (
            "The customer has budget approval for the quoted amount "
            "and says procurement is progressing.",
        ),
        {
            "interpretation_class": "quote_pending_decision",
            "support_level": "secondary_supported",
            "decision_strength": "stronger",
        },
    ),
    (
        "MR3-contradictory",
        PrimaryState("negotiation_open"),
        (
            "The customer rejects the revised commercial terms and "
            "wants the proposal reconsidered.",
        ),
        {
            "interpretation_class": "negotiation_open",
            "support_level": "weakened_by_secondary_context",
            "decision_strength": "weaker",
        },
    ),
    (
        "MR4-irrelevant",
        PrimaryState("quote_pending_decision"),
        (
            "The customer is discussing a different store rollout and "
            "says nothing about this quoted opportunity.",
        ),
        {
            "interpretation_class": "quote_pending_decision",
            "support_level": "primary_only",
            "decision_strength": "moderate",
        },
    ),
)


@pytest.mark.parametrize(
    "case_id,primary,texts,expected_variant",
    CASES,
)
def test_variant_transition_is_measured_against_primary_only(
    case_id: str,
    primary: PrimaryState,
    texts: tuple[str, ...],
    expected_variant: dict[str, str],
) -> None:
    reasoner = _reasoner()

    base_result = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    variant_result = reasoner.evaluate(
        primary,
        _condition(texts[0]),
    )

    base_state = _state(base_result)
    variant_state = _state(variant_result)

    assert base_state == (
        primary.interpretation_class,
        "no_secondary_evidence",
        primary.decision_strength,
        None,
    )

    for field, expected in expected_variant.items():
        assert getattr(variant_result, field) == expected, (
            f"{case_id}: unexpected variant {field}"
        )

    if case_id == "MR4-irrelevant":
        assert variant_state == (
            primary.interpretation_class,
            "primary_only",
            primary.decision_strength,
            None,
        )
    else:
        assert variant_state != base_state, (
            f"{case_id}: expected a material transition from "
            f"primary-only state"
        )


def test_wrong_identity_is_a_preservation_relation() -> None:
    reasoner = _reasoner()

    primary = PrimaryState("quote_pending_decision")

    base_result = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    wrong_identity = reasoner.evaluate(
        primary,
        _condition(
            "The customer wants another discussion about the proposal.",
            customer_id="C999",
        ),
    )

    # Identity quality is not derivable from the customer_id alone, so
    # replace the extracted evidence with an explicitly invalid identity.
    evidence = _condition(
        "The customer wants another discussion about the proposal.",
    ).items[0]

    from dataclasses import replace

    invalid = replace(
        evidence,
        identity=replace(
            evidence.identity,
            quality=evidence.identity.quality.NO_MATCH,
        ),
    )

    wrong_identity = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(invalid,),
        ),
    )

    assert wrong_identity.interpretation_class == base_result.interpretation_class
    assert wrong_identity.decision_strength == base_result.decision_strength
    assert wrong_identity.support_level == "primary_only"


def test_removing_secondary_evidence_returns_to_primary_only() -> None:
    reasoner = _reasoner()

    primary = PrimaryState("quote_pending_decision")

    with_secondary = reasoner.evaluate(
        primary,
        _condition(
            "The customer wants another discussion about the proposal.",
        ),
    )

    without_secondary = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    assert with_secondary.support_level == "supported_by_secondary_context"
    assert without_secondary.interpretation_class == primary.interpretation_class
    assert without_secondary.decision_strength == primary.decision_strength