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


def test_two_independent_positive_sources_preserve_positive_signal():
    first = _extract(
        "CRM",
        "The customer wants another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    second = _extract(
        "EMAIL",
        "The customer would like to speak about the offer again.",
        "2026-09-12T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(first, second),
    )

    assert first.provenance.source_system == "test"
    assert second.provenance.source_system == "test"

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_duplicate_semantics_from_multiple_records_remain_distinguishable():
    first = _extract(
        "RECORD-1",
        "The customer wants another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    second = _extract(
        "RECORD-2",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    assert first.evidence_id != second.evidence_id
    assert first.provenance.record_id != second.provenance.record_id

    assert first.semantics == second.semantics


def test_positive_and_negative_sources_remain_semantically_distinct():
    positive = _extract(
        "CRM",
        "The customer wants another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    negative = _extract(
        "EMAIL",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    assert positive.semantics.requests_followup is True
    assert positive.semantics.negated_concepts == ()

    assert negative.semantics.requests_followup is None
    assert negative.semantics.negated_concepts == ("followup",)


def test_conflicting_sources_do_not_get_resolved_by_source_name():
    first = _extract(
        "CRM",
        "The customer wants another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    second = _extract(
        "EMAIL",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(first, second),
    )

    assert first.provenance.record_id == "CRM"
    assert second.provenance.record_id == "EMAIL"

    # The current reasoner has no source-system weighting policy.
    # The assertion records the observed behavior rather than declaring
    # source priority correct.
    assert result.interpretation_class == "quote_followup_pending"


def test_source_metadata_does_not_change_semantic_extraction():
    crm = _extract(
        "CRM",
        "The customer has budget approval for the quoted amount.",
        "2026-09-11T10:00:00Z",
    )

    email = _extract(
        "EMAIL",
        "The customer has budget approval for the quoted amount.",
        "2026-09-12T10:00:00Z",
    )

    assert crm.semantics == email.semantics

    assert crm.provenance.record_id != email.provenance.record_id
    assert crm.timestamp != email.timestamp


def test_identity_and_source_metadata_are_kept_separate_from_semantics():
    confirmed = _extract(
        "CONFIRMED",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    assert confirmed.semantics.requests_followup is True
    assert confirmed.identity.customer_id == "C001"
    assert confirmed.identity.quality == IdentityQuality.CONFIRMED
    assert confirmed.provenance.source_system == "test"


def test_source_disagreement_does_not_modify_raw_evidence():
    positive = _extract(
        "SOURCE-A",
        "The customer wants another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    negative = _extract(
        "SOURCE-B",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    condition = _condition(positive, negative)

    assert condition.items[0].content == (
        "The customer wants another discussion about the proposal."
    )
    assert condition.items[1].content == (
        "The customer does not want another discussion about the proposal."
    )

    assert condition.items[0].semantics.requests_followup is True
    assert condition.items[1].semantics.requests_followup is None
    assert "followup" in condition.items[1].semantics.negated_concepts