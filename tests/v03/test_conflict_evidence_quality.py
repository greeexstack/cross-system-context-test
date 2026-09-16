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
    identity_quality: IdentityQuality,
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system="test",
        record_id=evidence_id,
        occurred_at=occurred_at,
        customer_id="C001",
        identity_quality=identity_quality,
    ).evidence


def _condition(
    *items: SemanticEvidence,
) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=items,
    )


def test_confirmed_identity_evidence_can_participate_in_conflict():
    positive = _extract(
        "CONFIRMED-POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
        IdentityQuality.CONFIRMED,
    )

    negative = _extract(
        "CONFIRMED-NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T11:00:00Z",
        IdentityQuality.CONFIRMED,
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            positive,
            negative,
        ),
    )

    assert positive.identity.quality == IdentityQuality.CONFIRMED
    assert negative.identity.quality == IdentityQuality.CONFIRMED

    assert result.interpretation_class == "quote_followup_pending"


def test_ambiguous_identity_is_excluded_from_conflict_resolution():
    confirmed_negative = _extract(
        "CONFIRMED-NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T11:00:00Z",
        IdentityQuality.CONFIRMED,
    )

    ambiguous_positive = _extract(
        "AMBIGUOUS-POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T12:00:00Z",
        IdentityQuality.AMBIGUOUS,
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            confirmed_negative,
            ambiguous_positive,
        ),
    )

    assert ambiguous_positive.identity.quality == IdentityQuality.AMBIGUOUS
    assert confirmed_negative.identity.quality == IdentityQuality.CONFIRMED

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"


def test_no_match_identity_is_excluded_from_conflict_resolution():
    confirmed_negative = _extract(
        "CONFIRMED-NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T11:00:00Z",
        IdentityQuality.CONFIRMED,
    )

    wrong_customer_positive = _extract(
        "WRONG-POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T12:00:00Z",
        IdentityQuality.NO_MATCH,
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            confirmed_negative,
            wrong_customer_positive,
        ),
    )

    assert wrong_customer_positive.identity.quality == (
        IdentityQuality.NO_MATCH
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"


def test_two_non_confirmed_items_do_not_create_supported_context():
    ambiguous = _extract(
        "AMBIGUOUS",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
        IdentityQuality.AMBIGUOUS,
    )

    wrong_match = _extract(
        "WRONG-MATCH",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T11:00:00Z",
        IdentityQuality.NO_MATCH,
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            ambiguous,
            wrong_match,
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"


def test_identity_quality_is_preserved_on_individual_evidence_items():
    confirmed = _extract(
        "CONFIRMED",
        "The quoted amount has budget approval.",
        "2026-09-12T10:00:00Z",
        IdentityQuality.CONFIRMED,
    )

    ambiguous = _extract(
        "AMBIGUOUS",
        "The quoted amount has budget approval.",
        "2026-09-12T11:00:00Z",
        IdentityQuality.AMBIGUOUS,
    )

    assert confirmed.identity == EvidenceIdentity(
        customer_id="C001",
        quality=IdentityQuality.CONFIRMED,
    )

    assert ambiguous.identity == EvidenceIdentity(
        customer_id="C001",
        quality=IdentityQuality.AMBIGUOUS,
    )

    assert confirmed.provenance == EvidenceProvenance(
        source_system="test",
        record_id="CONFIRMED",
        occurred_at=datetime(
            2026,
            9,
            12,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert ambiguous.provenance == EvidenceProvenance(
        source_system="test",
        record_id="AMBIGUOUS",
        occurred_at=datetime(
            2026,
            9,
            12,
            11,
            0,
            tzinfo=timezone.utc,
        ),
    )


def test_identity_quality_does_not_change_semantic_extraction():
    confirmed = _extract(
        "CONFIRMED",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
        IdentityQuality.CONFIRMED,
    )

    ambiguous = _extract(
        "AMBIGUOUS",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
        IdentityQuality.AMBIGUOUS,
    )

    wrong_match = _extract(
        "WRONG-MATCH",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
        IdentityQuality.NO_MATCH,
    )

    assert confirmed.semantics == ambiguous.semantics
    assert confirmed.semantics == wrong_match.semantics


def test_conflict_resolution_is_downstream_of_identity_filtering():
    confirmed_positive = _extract(
        "CONFIRMED-POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
        IdentityQuality.CONFIRMED,
    )

    wrong_customer_negative = _extract(
        "WRONG-NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T11:00:00Z",
        IdentityQuality.NO_MATCH,
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            confirmed_positive,
            wrong_customer_negative,
        ),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"