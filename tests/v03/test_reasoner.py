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


def make_reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def make_evidence(
    *,
    evidence_id: str,
    semantics: EvidenceSemantics,
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    customer_id: str = "C001",
    occurred_at: str = "2026-09-12T10:00:00+00:00",
    content: str = "synthetic semantic evidence",
) -> SemanticEvidence:
    return SemanticEvidence(
        evidence_id=evidence_id,
        content=content,
        provenance=EvidenceProvenance(
            source_system="test",
            record_id=evidence_id,
            occurred_at=datetime.fromisoformat(occurred_at),
        ),
        identity=EvidenceIdentity(
            customer_id=customer_id,
            quality=identity_quality,
        ),
        semantics=semantics,
    )


def available(*items: SemanticEvidence) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=items,
    )


def unavailable() -> EvidenceCondition:
    return EvidenceCondition(
        availability="unavailable",
        items=(),
    )


def primary(
    interpretation_class: str,
    decision_strength: str = "moderate",
) -> PrimaryState:
    return PrimaryState(
        interpretation_class=interpretation_class,
        decision_strength=decision_strength,
    )


def test_relevant_followup_changes_quote_pending_to_followup_pending() -> None:
    reasoner = make_reasoner()

    evidence = make_evidence(
        evidence_id="E1",
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
    )

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(evidence),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"
    assert result.decision_strength == "moderate"


def test_supporting_approval_strengthens_without_changing_class() -> None:
    reasoner = make_reasoner()

    evidence = make_evidence(
        evidence_id="E2",
        semantics=EvidenceSemantics(
            topic="proposal",
            confirms_approval=True,
            expresses_acceptance=True,
            concerns_same_work_item=True,
        ),
    )

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(evidence),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "secondary_supported"
    assert result.decision_strength == "stronger"


def test_contradictory_rejection_weakens_support() -> None:
    reasoner = make_reasoner()

    evidence = make_evidence(
        evidence_id="E3",
        semantics=EvidenceSemantics(
            topic="commercial_terms",
            expresses_rejection=True,
            concerns_same_work_item=True,
        ),
    )

    result = reasoner.evaluate(
        primary("negotiation_open"),
        available(evidence),
    )

    assert result.interpretation_class == "negotiation_open"
    assert result.support_level == "weakened_by_secondary_context"
    assert result.decision_strength == "weaker"


def test_irrelevant_evidence_preserves_primary_state() -> None:
    reasoner = make_reasoner()

    evidence = make_evidence(
        evidence_id="E4",
        semantics=EvidenceSemantics(
            topic="store_rollout",
            concerns_same_work_item=False,
        ),
    )

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(evidence),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"


def test_wrong_identity_cannot_influence_interpretation() -> None:
    reasoner = make_reasoner()

    evidence = make_evidence(
        evidence_id="E5",
        identity_quality=IdentityQuality.NO_MATCH,
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
    )

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(evidence),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"


def test_ambiguous_identity_cannot_influence_interpretation() -> None:
    reasoner = make_reasoner()

    evidence = make_evidence(
        evidence_id="E6",
        identity_quality=IdentityQuality.AMBIGUOUS,
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
    )

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(evidence),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"


def test_service_completion_and_next_step_sets_focus() -> None:
    reasoner = make_reasoner()

    evidence = make_evidence(
        evidence_id="E7",
        semantics=EvidenceSemantics(
            topic="service",
            confirms_completion=True,
            requests_next_step=True,
            concerns_same_work_item=True,
        ),
    )

    result = reasoner.evaluate(
        primary("service_completed_next_step_unrecorded"),
        available(evidence),
    )

    assert (
        result.interpretation_class
        == "service_completed_next_step_unrecorded"
    )
    assert result.support_level == "supported_by_secondary_context"
    assert result.decision_strength == "moderate"
    assert result.recommended_focus == "next_step_followup"


def test_unavailable_secondary_source_preserves_primary_interpretation() -> None:
    reasoner = make_reasoner()

    result = reasoner.evaluate(
        primary("quote_followup_pending"),
        unavailable(),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "safe_fallback_primary_only"
    assert result.decision_strength == "moderate"


def test_no_secondary_evidence_preserves_primary_interpretation() -> None:
    reasoner = make_reasoner()

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "no_secondary_evidence"
    assert result.decision_strength == "moderate"


def test_semantic_representation_is_wording_independent() -> None:
    reasoner = make_reasoner()

    first = make_evidence(
        evidence_id="E8A",
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
        content=(
            "The customer is reviewing the proposal and wants another "
            "discussion next week."
        ),
    )

    second = make_evidence(
        evidence_id="E8B",
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
        content=(
            "The customer is considering the offer and would like to "
            "speak about it again during the coming week."
        ),
    )

    first_result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(first),
    )

    second_result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(second),
    )

    assert first_result == second_result


def test_mixed_evidence_does_not_treat_conflict_as_unqualified_support() -> None:
    reasoner = make_reasoner()

    supporting = make_evidence(
        evidence_id="E9A",
        semantics=EvidenceSemantics(
            topic="proposal",
            confirms_approval=True,
            expresses_acceptance=True,
            concerns_same_work_item=True,
        ),
    )

    contradictory = make_evidence(
        evidence_id="E9B",
        semantics=EvidenceSemantics(
            topic="commercial_terms",
            expresses_rejection=True,
            concerns_same_work_item=True,
        ),
    )

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(supporting, contradictory),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "weakened_by_secondary_context"
    assert result.decision_strength == "weaker"


def test_stale_evidence_does_not_influence_current_state() -> None:
    reasoner = make_reasoner()

    stale = make_evidence(
        evidence_id="E10",
        occurred_at="2026-08-01T10:00:00+00:00",
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
    )

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(stale),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "temporal_context_rejected"
    assert result.decision_strength == "moderate"


def test_removing_secondary_evidence_preserves_primary_state() -> None:
    reasoner = make_reasoner()

    primary_state = primary("quote_pending_decision")

    result_with_evidence = reasoner.evaluate(
        primary_state,
        available(
            make_evidence(
                evidence_id="E11",
                semantics=EvidenceSemantics(
                    topic="proposal",
                    requests_followup=True,
                    concerns_same_work_item=True,
                ),
            )
        ),
    )

    result_without_evidence = reasoner.evaluate(
        primary_state,
        available(),
    )

    assert (
        result_with_evidence.interpretation_class
        == "quote_followup_pending"
    )
    assert (
        result_without_evidence.interpretation_class
        == "quote_pending_decision"
    )
    assert result_without_evidence.support_level == "no_secondary_evidence"


def test_rejection_has_priority_over_supporting_evidence() -> None:
    reasoner = make_reasoner()

    supporting = make_evidence(
        evidence_id="E12A",
        semantics=EvidenceSemantics(
            topic="proposal",
            confirms_approval=True,
            concerns_same_work_item=True,
        ),
    )

    contradictory = make_evidence(
        evidence_id="E12B",
        semantics=EvidenceSemantics(
            topic="commercial_terms",
            expresses_rejection=True,
            concerns_same_work_item=True,
        ),
    )

    result = reasoner.evaluate(
        primary("negotiation_open"),
        available(supporting, contradictory),
    )

    assert result.support_level == "weakened_by_secondary_context"
    assert result.decision_strength == "weaker"


def test_multiple_irrelevant_items_preserve_primary_state() -> None:
    reasoner = make_reasoner()

    first = make_evidence(
        evidence_id="E13A",
        semantics=EvidenceSemantics(
            topic="store_rollout",
            concerns_same_work_item=False,
        ),
    )

    second = make_evidence(
        evidence_id="E13B",
        semantics=EvidenceSemantics(
            topic="service_rollout",
            concerns_same_work_item=False,
        ),
    )

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(first, second),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "primary_only"
    assert result.decision_strength == "moderate"


def test_confirmed_evidence_can_be_used_when_other_evidence_is_invalid() -> None:
    reasoner = make_reasoner()

    invalid = make_evidence(
        evidence_id="E14A",
        identity_quality=IdentityQuality.NO_MATCH,
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
    )

    valid = make_evidence(
        evidence_id="E14B",
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
    )

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(invalid, valid),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_semantic_equivalence_does_not_depend_on_raw_content() -> None:
    reasoner = make_reasoner()

    first = make_evidence(
        evidence_id="E15A",
        content="Completely different wording.",
        semantics=EvidenceSemantics(
            topic="proposal",
            confirms_approval=True,
            expresses_acceptance=True,
            concerns_same_work_item=True,
        ),
    )

    second = make_evidence(
        evidence_id="E15B",
        content="Another unrelated sentence structure.",
        semantics=EvidenceSemantics(
            topic="proposal",
            confirms_approval=True,
            expresses_acceptance=True,
            concerns_same_work_item=True,
        ),
    )

    first_result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(first),
    )

    second_result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(second),
    )

    assert first_result == second_result


def test_boundary_age_is_fresh() -> None:
    reasoner = make_reasoner()

    boundary = make_evidence(
        evidence_id="E16",
        occurred_at="2026-08-14T12:00:00+00:00",
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
    )

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(boundary),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_evidence_one_second_past_boundary_is_stale() -> None:
    reasoner = make_reasoner()

    stale = make_evidence(
        evidence_id="E17",
        occurred_at="2026-08-14T11:59:59+00:00",
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
    )

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(stale),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "temporal_context_rejected"


def test_missing_timestamp_does_not_count_as_fresh_evidence() -> None:
    reasoner = make_reasoner()

    evidence = make_evidence(
        evidence_id="E18",
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
    )

    evidence = SemanticEvidence(
        evidence_id=evidence.evidence_id,
        content=evidence.content,
        provenance=EvidenceProvenance(
            source_system=evidence.provenance.source_system,
            record_id=evidence.provenance.record_id,
            occurred_at=None,
        ),
        identity=evidence.identity,
        semantics=evidence.semantics,
    )

    result = reasoner.evaluate(
        primary("quote_pending_decision"),
        available(evidence),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "temporal_context_rejected"


def test_config_rejects_naive_evaluation_time() -> None:
    try:
        ReasonerConfig(
            evaluation_at=datetime(2026, 9, 13, 12, 0, 0),
            stale_after_days=30,
        )
    except ValueError as exc:
        assert "timezone-aware" in str(exc)
    else:
        raise AssertionError(
            "Expected naive evaluation_at to be rejected"
        )


def test_config_rejects_negative_stale_threshold() -> None:
    try:
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=-1,
        )
    except ValueError as exc:
        assert "non-negative" in str(exc)
    else:
        raise AssertionError(
            "Expected negative stale_after_days to be rejected"
        )