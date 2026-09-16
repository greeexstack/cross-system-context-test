from __future__ import annotations

from experiment.v03.battery import EVALUATION_AT
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


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _extract(
    evidence_id: str,
    source_system: str,
    text: str,
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system=source_system,
        record_id=evidence_id,
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    ).evidence


def _condition(*items: SemanticEvidence) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=tuple(items),
    )


def _control() -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=(),
    )


def test_source_a_alone_produces_one_observable_result():
    source_a = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(source_a),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"
    assert result.decision_strength == "moderate"


def test_source_b_alone_produces_a_different_observable_result():
    source_b = _extract(
        "FINANCE-1",
        "finance",
        "The quoted amount has budget approval.",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(source_b),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "secondary_supported"
    assert result.decision_strength == "stronger"


def test_combining_distinct_sources_produces_a_joint_result():
    source_a = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    source_b = _extract(
        "FINANCE-1",
        "finance",
        "The quoted amount has budget approval.",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            source_a,
            source_b,
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "secondary_supported"
    assert result.decision_strength == "stronger"


def test_combined_result_differs_from_primary_only_control():
    source_a = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    source_b = _extract(
        "FINANCE-1",
        "finance",
        "The quoted amount has budget approval.",
    )

    control = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _control(),
    )

    combined = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            source_a,
            source_b,
        ),
    )

    assert control.interpretation_class == "quote_pending_decision"
    assert control.support_level == "no_secondary_evidence"
    assert control.decision_strength == "moderate"

    assert combined.interpretation_class == "quote_pending_decision"
    assert combined.support_level == "secondary_supported"
    assert combined.decision_strength == "stronger"


def test_combined_result_contains_distinct_source_provenance():
    source_a = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    source_b = _extract(
        "FINANCE-1",
        "finance",
        "The quoted amount has budget approval.",
    )

    condition = _condition(
        source_a,
        source_b,
    )

    assert len(condition.items) == 2

    assert condition.items[0].provenance.source_system == "crm"
    assert condition.items[1].provenance.source_system == "finance"

    assert condition.items[0].provenance.record_id == "CRM-1"
    assert condition.items[1].provenance.record_id == "FINANCE-1"


def test_same_fact_from_two_sources_is_not_the_same_as_two_distinct_facts():
    crm = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    email = _extract(
        "EMAIL-1",
        "email",
        "The customer wants another discussion about the proposal.",
    )

    finance = _extract(
        "FINANCE-1",
        "finance",
        "The quoted amount has budget approval.",
    )

    duplicate_sources = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            crm,
            email,
        ),
    )

    distinct_sources = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            crm,
            finance,
        ),
    )

    assert duplicate_sources.interpretation_class == (
        "quote_followup_pending"
    )
    assert duplicate_sources.decision_strength == "moderate"

    assert distinct_sources.interpretation_class == (
        "quote_pending_decision"
    )
    assert distinct_sources.decision_strength == "stronger"


def test_one_source_can_be_removed_without_corrupting_the_other():
    source_a = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    source_b = _extract(
        "FINANCE-1",
        "finance",
        "The quoted amount has budget approval.",
    )

    only_a = _condition(source_a)
    only_b = _condition(source_b)

    assert len(only_a.items) == 1
    assert len(only_b.items) == 1

    assert only_a.items[0].provenance.source_system == "crm"
    assert only_b.items[0].provenance.source_system == "finance"