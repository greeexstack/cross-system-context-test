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
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system="test",
        record_id=evidence_id,
        occurred_at="2026-09-12T10:00:00Z",
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


def test_single_positive_followup_is_still_supported():
    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            _extract(
                "POSITIVE",
                "The customer wants another discussion about the proposal.",
            ),
        ),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_single_negated_followup_is_not_supported():
    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            _extract(
                "NEGATIVE",
                "The customer does not want another discussion about the proposal.",
            ),
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"


def test_conflicting_followup_evidence_is_explicitly_exercised():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            positive,
            negative,
        ),
    )

    # Both propositions concern the same work item, so both reach
    # the reasoning layer.
    assert positive.semantics.requests_followup is True
    assert "followup" in negative.semantics.negated_concepts

    # This assertion deliberately records the CURRENT behavior.
    # It may expose an ambiguity in the reasoner's conflict policy.
    assert result.interpretation_class == "quote_followup_pending"


def test_conflicting_approval_evidence_is_explicitly_exercised():
    positive = _extract(
        "POSITIVE",
        "The quoted amount has budget approval.",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not have budget approval for the quoted amount.",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            positive,
            negative,
        ),
    )

    assert positive.semantics.confirms_approval is True
    assert "approval" in negative.semantics.negated_concepts

    # Record current behavior without yet declaring it correct.
    assert result.support_level == "secondary_supported"


def test_conflicting_rejection_and_acceptance_are_exposed():
    accepted = _extract(
        "ACCEPTED",
        "The customer accepted the revised commercial terms.",
    )

    rejected = _extract(
        "REJECTED",
        "The customer rejected the revised commercial terms.",
    )

    result = _reasoner().evaluate(
        PrimaryState("negotiation_open"),
        _condition(
            accepted,
            rejected,
        ),
    )

    assert accepted.semantics.expresses_acceptance is True
    assert rejected.semantics.expresses_rejection is True

    # Current reasoner precedence gives rejection priority.
    assert result.support_level == "weakened_by_secondary_context"
    assert result.decision_strength == "weaker"


def test_conflict_items_remain_individually_inspectable():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
    )

    condition = _condition(
        positive,
        negative,
    )

    assert len(condition.items) == 2

    assert condition.items[0].semantics.requests_followup is True
    assert "followup" in condition.items[1].semantics.negated_concepts