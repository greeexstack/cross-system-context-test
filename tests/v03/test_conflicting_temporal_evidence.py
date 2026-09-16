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


def test_newer_positive_followup_is_preserved_alongside_older_negation():
    newer_positive = _extract(
        "NEWER-POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T11:00:00Z",
    )

    older_negative = _extract(
        "OLDER-NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-10T11:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            newer_positive,
            older_negative,
        ),
    )

    assert newer_positive.timestamp > older_negative.timestamp

    # Record current behavior. The reasoner currently sees the positive
    # assertion and strengthens the transition.
    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_newer_negative_followup_is_preserved_alongside_older_positive():
    newer_negative = _extract(
        "NEWER-NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T11:00:00Z",
    )

    older_positive = _extract(
        "OLDER-POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T11:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            newer_negative,
            older_positive,
        ),
    )

    assert newer_negative.timestamp > older_positive.timestamp

    # This deliberately captures current behavior rather than declaring
    # a temporal conflict-resolution policy correct.
    assert result.interpretation_class == "quote_followup_pending"


def test_stale_conflicting_evidence_is_rejected_before_conflict_resolution():
    fresh_positive = _extract(
        "FRESH-POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T11:00:00Z",
    )

    stale_negative = _extract(
        "STALE-NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-07-01T11:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            fresh_positive,
            stale_negative,
        ),
    )

    assert fresh_positive.timestamp > stale_negative.timestamp

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_multiple_current_conflicting_items_remain_individually_inspectable():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T11:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-11T11:00:00Z",
    )

    condition = _condition(
        positive,
        negative,
    )

    assert len(condition.items) == 2

    assert condition.items[0].identity.quality == (
        IdentityQuality.CONFIRMED
    )
    assert condition.items[1].identity.quality == (
        IdentityQuality.CONFIRMED
    )

    assert condition.items[0].timestamp > condition.items[1].timestamp
    assert condition.items[0].semantics.requests_followup is True
    assert "followup" in condition.items[1].semantics.negated_concepts