from __future__ import annotations

from datetime import datetime, timezone

import pytest

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
    text: str,
    *,
    customer_id: str | None = "C001",
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    occurred_at: str | None = "2026-09-12T10:00:00Z",
):
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id="SAFETY",
        content=text,
        source_system="test",
        record_id="SAFETY",
        occurred_at=occurred_at,
        customer_id=customer_id,
        identity_quality=identity_quality,
    ).evidence


def _evaluate(
    primary: PrimaryState,
    condition: EvidenceCondition,
):
    return _reasoner().evaluate(primary, condition)


def test_wrong_identity_cannot_influence_result() -> None:
    evidence = _extract(
        "The customer wants another discussion about the proposal.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    result = _evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(evidence,),
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"


def test_ambiguous_identity_cannot_be_treated_as_confirmed() -> None:
    evidence = _extract(
        "The customer wants another discussion about the proposal.",
        identity_quality=IdentityQuality.AMBIGUOUS,
    )

    result = _evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(evidence,),
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"


def test_stale_relevant_evidence_does_not_change_current_state() -> None:
    evidence = _extract(
        "The customer wants another discussion about the proposal.",
        occurred_at="2026-08-01T10:00:00Z",
    )

    result = _evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(evidence,),
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "temporal_context_rejected"
    assert result.decision_strength == "moderate"


def test_unavailable_secondary_source_uses_safe_fallback() -> None:
    result = _evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="unavailable",
            items=(),
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "safe_fallback_primary_only"
    assert result.decision_strength == "moderate"


def test_available_source_without_evidence_is_not_unavailable() -> None:
    result = _evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "no_secondary_evidence"
    assert result.decision_strength == "moderate"


def test_missing_timestamp_cannot_become_fresh_evidence() -> None:
    evidence = _extract(
        "The customer wants another discussion about the proposal.",
        occurred_at=None,
    )

    result = _evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(evidence,),
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "temporal_context_rejected"
    assert result.decision_strength == "moderate"