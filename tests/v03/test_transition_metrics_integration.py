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
from experiment.v03.transition_metrics import (
    TransitionDirection,
    TransitionExpectation,
    directional_correctness,
    observe,
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


def _variant(text: str):
    extractor = LexicalNormalizationSemanticExtractor()

    evidence = extractor.extract(
        evidence_id="METRIC",
        content=text,
        source_system="diagnostic",
        record_id="METRIC",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
    ).evidence

    return EvidenceCondition(
        availability="available",
        items=(evidence,),
    )


CASES = (
    (
        "MR1-relevant",
        PrimaryState("quote_pending_decision"),
        (
            "The customer wants another discussion about the proposal "
            "next week."
        ),
        TransitionDirection.STRENGTHEN,
    ),
    (
        "MR2-supporting",
        PrimaryState("quote_pending_decision"),
        (
            "The customer has budget approval for the quoted amount "
            "and says procurement is progressing."
        ),
        TransitionDirection.STRENGTHEN,
    ),
    (
        "MR3-contradictory",
        PrimaryState("negotiation_open"),
        (
            "The customer rejects the revised commercial terms and "
            "wants the proposal reconsidered."
        ),
        TransitionDirection.WEAKEN,
    ),
    (
        "MR4-irrelevant",
        PrimaryState("quote_pending_decision"),
        (
            "The customer is discussing a different store rollout "
            "and says nothing about this quoted opportunity."
        ),
        TransitionDirection.PRESERVE,
    ),
)


@pytest.mark.parametrize(
    "case_id,primary,text,expected_direction",
    CASES,
)
def test_directional_metric_evaluates_real_v03_transition(
    case_id: str,
    primary: PrimaryState,
    text: str,
    expected_direction: TransitionDirection,
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
        _variant(text),
    )

    observation = observe(
        base_result,
        variant_result,
    )

    assert directional_correctness(
        observation,
        TransitionExpectation(expected_direction),
    ), (
        f"{case_id}: directional metric rejected valid transition\n"
        f"base={observation.base}\n"
        f"variant={observation.variant}\n"
        f"expected={expected_direction.value}"
    )


def test_irrelevant_context_is_not_counted_as_strengthening() -> None:
    reasoner = _reasoner()

    primary = PrimaryState("quote_pending_decision")

    base_result = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    variant_result = reasoner.evaluate(
        primary,
        _variant(
            "The customer is discussing a different store rollout "
            "and says nothing about this quoted opportunity."
        ),
    )

    observation = observe(base_result, variant_result)

    assert not directional_correctness(
        observation,
        TransitionExpectation(TransitionDirection.STRENGTHEN),
    )


def test_contradictory_context_is_not_counted_as_strengthening() -> None:
    reasoner = _reasoner()

    primary = PrimaryState("negotiation_open")

    base_result = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    variant_result = reasoner.evaluate(
        primary,
        _variant(
            "The customer rejects the revised commercial terms "
            "and wants the proposal reconsidered."
        ),
    )

    observation = observe(base_result, variant_result)

    assert not directional_correctness(
        observation,
        TransitionExpectation(TransitionDirection.STRENGTHEN),
    )