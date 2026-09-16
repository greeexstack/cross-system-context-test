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


def test_same_polarity_duplicate_evidence_does_not_change_result():
    first = _extract(
        "FIRST",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    second = _extract(
        "SECOND",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(first, second),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_conflicting_followup_is_detectable_from_raw_semantics():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    assert positive.semantics.requests_followup is True
    assert "followup" not in positive.semantics.negated_concepts

    assert negative.semantics.requests_followup is None
    assert "followup" in negative.semantics.negated_concepts


def test_conflicting_approval_is_detectable_from_raw_semantics():
    positive = _extract(
        "POSITIVE",
        "The quoted amount has budget approval.",
        "2026-09-10T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not have budget approval for the quoted amount.",
        "2026-09-12T10:00:00Z",
    )

    assert positive.semantics.confirms_approval is True
    assert "approval" not in positive.semantics.negated_concepts

    assert negative.semantics.confirms_approval is None
    assert "approval" in negative.semantics.negated_concepts


def test_conflicting_evidence_does_not_modify_identity_or_provenance():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    assert positive.identity.customer_id == "C001"
    assert negative.identity.customer_id == "C001"

    assert positive.identity.quality == IdentityQuality.CONFIRMED
    assert negative.identity.quality == IdentityQuality.CONFIRMED

    assert positive.timestamp == datetime(
        2026,
        9,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    assert negative.timestamp == datetime(
        2026,
        9,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )


def test_stale_conflict_does_not_reopen_rejected_evidence():
    fresh_negative = _extract(
        "FRESH-NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    stale_positive = _extract(
        "STALE-POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-07-01T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            fresh_negative,
            stale_positive,
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"