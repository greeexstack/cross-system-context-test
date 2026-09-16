from __future__ import annotations

from datetime import datetime, timezone

from experiment.v03.evidence import (
    EvidenceCondition,
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


def _extract(
    evidence_id: str,
    text: str,
    occurred_at: str,
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system="test",
        record_id=evidence_id,
        occurred_at=occurred_at,
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    ).evidence


def _condition(
    *items: SemanticEvidence,
) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=items,
    )


def test_three_way_followup_conflict_is_handled_by_current_policy():
    positive_1 = _extract(
        "POSITIVE-1",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    positive_2 = _extract(
        "POSITIVE-2",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            positive_1,
            negative,
            positive_2,
        ),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_three_way_reverse_followup_conflict_is_order_independent():
    negative_1 = _extract(
        "NEGATIVE-1",
        "The customer does not want another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    negative_2 = _extract(
        "NEGATIVE-2",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            negative_1,
            positive,
            negative_2,
        ),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_three_way_approval_conflict_uses_current_positive_precedence():
    positive_1 = _extract(
        "POSITIVE-1",
        "The quoted amount has budget approval.",
        "2026-09-10T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not have budget approval for the quoted amount.",
        "2026-09-11T10:00:00Z",
    )

    positive_2 = _extract(
        "POSITIVE-2",
        "Funding for the proposed price has been authorized.",
        "2026-09-12T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            positive_1,
            negative,
            positive_2,
        ),
    )

    assert result.support_level == "secondary_supported"
    assert result.decision_strength == "stronger"


def test_three_way_rejection_conflict_preserves_rejection_precedence():
    accepted_1 = _extract(
        "ACCEPTED-1",
        "The customer accepted the revised commercial terms.",
        "2026-09-10T10:00:00Z",
    )

    rejected = _extract(
        "REJECTED",
        "The customer rejected the revised commercial terms.",
        "2026-09-11T10:00:00Z",
    )

    accepted_2 = _extract(
        "ACCEPTED-2",
        "The customer accepted the revised commercial terms.",
        "2026-09-12T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("negotiation_open"),
        _condition(
            accepted_1,
            rejected,
            accepted_2,
        ),
    )

    assert result.support_level == "weakened_by_secondary_context"
    assert result.decision_strength == "weaker"


def test_three_way_conflict_preserves_individual_evidence_semantics():
    items = (
        _extract(
            "POSITIVE",
            "The customer wants another discussion about the proposal.",
            "2026-09-10T10:00:00Z",
        ),
        _extract(
            "NEGATIVE",
            "The customer does not want another discussion about the proposal.",
            "2026-09-11T10:00:00Z",
        ),
        _extract(
            "POSITIVE-2",
            "The customer wants another discussion about the proposal.",
            "2026-09-12T10:00:00Z",
        ),
    )

    condition = _condition(*items)

    assert len(condition.items) == 3

    assert condition.items[0].semantics.requests_followup is True
    assert condition.items[1].semantics.requests_followup is None
    assert "followup" in condition.items[1].semantics.negated_concepts
    assert condition.items[2].semantics.requests_followup is True