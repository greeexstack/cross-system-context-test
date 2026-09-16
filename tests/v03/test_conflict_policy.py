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


def test_current_policy_uses_any_positive_followup():
    older_positive = _extract(
        "OLDER-POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    newer_negative = _extract(
        "NEWER-NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            older_positive,
            newer_negative,
        ),
    )

    assert result.interpretation_class == "quote_followup_pending"


def test_reverse_order_does_not_change_current_followup_result():
    newer_negative = _extract(
        "NEWER-NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    older_positive = _extract(
        "OLDER-POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            newer_negative,
            older_positive,
        ),
    )

    assert result.interpretation_class == "quote_followup_pending"


def test_current_policy_uses_any_approval():
    older_approval = _extract(
        "OLDER-APPROVAL",
        "The quoted amount has budget approval.",
        "2026-09-10T10:00:00Z",
    )

    newer_denial = _extract(
        "NEWER-DENIAL",
        "The customer does not have budget approval for the quoted amount.",
        "2026-09-12T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            older_approval,
            newer_denial,
        ),
    )

    assert result.support_level == "secondary_supported"
    assert result.decision_strength == "stronger"


def test_current_policy_preserves_rejection_precedence():
    accepted = _extract(
        "ACCEPTED",
        "The customer accepted the revised commercial terms.",
        "2026-09-12T10:00:00Z",
    )

    rejected = _extract(
        "REJECTED",
        "The customer rejected the revised commercial terms.",
        "2026-09-10T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("negotiation_open"),
        _condition(
            accepted,
            rejected,
        ),
    )

    assert result.support_level == "weakened_by_secondary_context"
    assert result.decision_strength == "weaker"


def test_reversing_rejection_and_acceptance_timestamps_keeps_current_precedence():
    rejected = _extract(
        "REJECTED",
        "The customer rejected the revised commercial terms.",
        "2026-09-12T10:00:00Z",
    )

    accepted = _extract(
        "ACCEPTED",
        "The customer accepted the revised commercial terms.",
        "2026-09-10T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("negotiation_open"),
        _condition(
            accepted,
            rejected,
        ),
    )

    assert result.support_level == "weakened_by_secondary_context"
    assert result.decision_strength == "weaker"