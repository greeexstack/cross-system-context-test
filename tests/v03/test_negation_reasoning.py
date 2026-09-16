from __future__ import annotations

from datetime import datetime, timezone

from experiment.v03.evidence import (
    EvidenceCondition,
    EvidenceIdentity,
    EvidenceProvenance,
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)
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
    tzinfo=timezone.utc,
)


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _extract(text: str) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id="NEGATION",
        content=text,
        source_system="test",
        record_id="NEGATION",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    ).evidence


def _condition(text: str) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=(
            _extract(text),
        ),
    )


def test_positive_followup_evidence_strengthens_transition():
    reasoner = _reasoner()

    primary = PrimaryState("quote_pending_decision")

    result = reasoner.evaluate(
        primary,
        _condition(
            "The customer wants another discussion about the proposal."
        ),
    )

    assert result.support_level == "supported_by_secondary_context"
    assert result.decision_strength == "moderate"
    assert result.interpretation_class == "quote_followup_pending"


def test_negated_followup_does_not_strengthen_transition():
    reasoner = _reasoner()

    primary = PrimaryState("quote_pending_decision")

    result = reasoner.evaluate(
        primary,
        _condition(
            "The customer does not want another discussion about the proposal."
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"


def test_positive_completion_and_next_step_are_handled_independently():
    reasoner = _reasoner()

    primary = PrimaryState(
        "service_completed_next_step_unrecorded"
    )

    result = reasoner.evaluate(
        primary,
        _condition(
            "The migration workshop is complete and the customer "
            "asks what comes next."
        ),
    )

    assert result.interpretation_class == (
        "service_completed_next_step_unrecorded"
    )
    assert result.support_level == "supported_by_secondary_context"
    assert result.recommended_focus == "next_step_followup"


def test_negated_completion_does_not_create_completion_evidence():
    reasoner = _reasoner()

    primary = PrimaryState(
        "service_completed_next_step_unrecorded"
    )

    result = reasoner.evaluate(
        primary,
        _condition(
            "The migration workshop is not complete and the customer "
            "asks what comes next."
        ),
    )

    assert result.interpretation_class == (
        "service_completed_next_step_unrecorded"
    )
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"
    assert result.recommended_focus is None


def test_negated_approval_does_not_strengthen_quote_decision():
    reasoner = _reasoner()

    primary = PrimaryState("quote_pending_decision")

    result = reasoner.evaluate(
        primary,
        _condition(
            "The customer does not have budget approval "
            "for the quoted amount."
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"


def test_positive_approval_still_strengthens_quote_decision():
    reasoner = _reasoner()

    primary = PrimaryState("quote_pending_decision")

    result = reasoner.evaluate(
        primary,
        _condition(
            "Funding for the proposed price has been authorized."
        ),
    )

    assert result.support_level == "secondary_supported"
    assert result.decision_strength == "stronger"
    assert result.interpretation_class == "quote_pending_decision"


def test_negated_proposition_does_not_become_positive_support():
    evidence = _extract(
        "The customer does not want another discussion about the proposal."
    )

    assert evidence.semantics.negated_concepts == ("followup",)