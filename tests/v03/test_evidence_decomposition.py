from __future__ import annotations

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    EvidenceCondition,
    IdentityQuality,
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
    text: str,
):
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system="secondary",
        record_id=evidence_id,
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    ).evidence


def _condition(*items) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=tuple(items),
    )


def test_multi_fact_observation_exposes_each_fact_independently():
    evidence = _extract(
        "MULTI-FACT",
        "The migration workshop is complete and the customer asks "
        "what comes next.",
    )

    semantics = evidence.semantics

    assert semantics.confirms_completion is True
    assert semantics.requests_next_step is True
    assert semantics.negated_concepts == ()


def test_single_completion_fact_does_not_create_next_step_fact():
    evidence = _extract(
        "COMPLETION-ONLY",
        "The migration workshop is complete.",
    )

    semantics = evidence.semantics

    assert semantics.confirms_completion is True
    assert semantics.requests_next_step is None


def test_single_next_step_fact_does_not_create_completion_fact():
    evidence = _extract(
        "NEXT-ONLY",
        "The customer asks what comes next.",
    )

    semantics = evidence.semantics

    assert semantics.confirms_completion is None
    assert semantics.requests_next_step is True


def test_multi_fact_observation_triggers_existing_joint_reasoning_rule():
    result = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            _extract(
                "MULTI-FACT",
                "The migration workshop is complete and the customer "
                "asks what comes next.",
            ),
        ),
    )

    assert result.interpretation_class == (
        "service_completed_next_step_unrecorded"
    )
    assert result.support_level == "supported_by_secondary_context"
    assert result.recommended_focus == "next_step_followup"


def test_removing_completion_fact_removes_joint_completion_next_step_signal():
    result = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            _extract(
                "NEXT-ONLY",
                "The customer asks what comes next.",
            ),
        ),
    )

    assert result.interpretation_class == (
        "service_completed_next_step_unrecorded"
    )
    assert result.support_level == "primary_only"
    assert result.recommended_focus is None


def test_removing_next_step_fact_removes_joint_completion_next_step_signal():
    result = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            _extract(
                "COMPLETION-ONLY",
                "The migration workshop is complete.",
            ),
        ),
    )

    assert result.interpretation_class == (
        "service_completed_next_step_unrecorded"
    )
    assert result.support_level == "primary_only"
    assert result.recommended_focus is None


def test_negating_one_fact_preserves_the_other_fact():
    evidence = _extract(
        "MIXED-FACT",
        "The migration workshop is not complete and the customer "
        "asks what comes next.",
    )

    semantics = evidence.semantics

    assert semantics.confirms_completion is not True
    assert "completion" in semantics.negated_concepts

    assert semantics.requests_next_step is True
    assert "next_step" not in semantics.negated_concepts


def test_negated_fact_cannot_participate_in_joint_reasoning():
    result = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            _extract(
                "MIXED-FACT",
                "The migration workshop is not complete and the customer "
                "asks what comes next.",
            ),
        ),
    )

    assert result.interpretation_class == (
        "service_completed_next_step_unrecorded"
    )
    assert result.support_level == "primary_only"
    assert result.recommended_focus is None


def test_independent_facts_in_different_records_do_not_yet_combine():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    result = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            completion,
            next_step,
        ),
    )

    # Current v0.3 behavior:
    # the joint completion + next_step rule requires both facts
    # to exist on the same semantic evidence item.
    assert result.interpretation_class == (
        "service_completed_next_step_unrecorded"
    )
    assert result.support_level == "primary_only"
    assert result.recommended_focus is None


def test_fact_removal_from_single_multi_fact_observation_removes_joint_signal():
    both = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            _extract(
                "BOTH",
                "The migration workshop is complete and the customer "
                "asks what comes next.",
            ),
        ),
    )

    completion_only = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            _extract(
                "COMPLETION-ONLY",
                "The migration workshop is complete.",
            ),
        ),
    )

    assert both.recommended_focus == "next_step_followup"
    assert both.support_level == "supported_by_secondary_context"

    assert completion_only.recommended_focus is None
    assert completion_only.support_level == "primary_only"

    assert (
        both.interpretation_class
        == completion_only.interpretation_class
    )


def test_decomposition_does_not_mutate_original_evidence():
    evidence = _extract(
        "MULTI-FACT",
        "The migration workshop is complete and the customer "
        "asks what comes next.",
    )

    before = evidence.semantics

    result = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(evidence),
    )

    after = evidence.semantics

    assert before == after
    assert result.support_level == "supported_by_secondary_context"


def test_multi_fact_semantics_remain_benchmark_independent():
    evidence = _extract(
        "MULTI-FACT",
        "The migration workshop is complete and the customer "
        "asks what comes next.",
    )

    semantics = evidence.semantics

    assert semantics.confirms_completion is True
    assert semantics.requests_next_step is True

    # Factual evidence must remain independent of benchmark
    # expectations and transition labels.
    assert not hasattr(semantics, "expected_transition")
    assert not hasattr(semantics, "benchmark_family")
    assert not hasattr(semantics, "expected_direction")