from __future__ import annotations

from dataclasses import replace

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    EvidenceCondition,
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
    *,
    source_system: str = "secondary",
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


def _condition(
    *items: SemanticEvidence,
) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=tuple(items),
    )


def _compose_semantics(
    items: tuple[SemanticEvidence, ...],
) -> EvidenceSemantics:
    """
    Test-layer semantic composition.

    This intentionally creates a synthetic SemanticEvidence object
    later. It does not modify the production reasoner or extractor.
    """
    eligible = tuple(
        item
        for item in items
        if item.identity.quality == IdentityQuality.CONFIRMED
        and item.timestamp is not None
        and item.semantics.concerns_same_work_item is not False
    )

    negated = set()

    for item in eligible:
        negated.update(
            item.semantics.negated_concepts
        )

    confirms_completion = any(
        item.semantics.confirms_completion is True
        and "completion" not in item.semantics.negated_concepts
        for item in eligible
    )

    requests_next_step = any(
        item.semantics.requests_next_step is True
        and "next_step" not in item.semantics.negated_concepts
        for item in eligible
    )

    requests_followup = any(
        item.semantics.requests_followup is True
        and "followup" not in item.semantics.negated_concepts
        for item in eligible
    )

    confirms_approval = any(
        item.semantics.confirms_approval is True
        and "approval" not in item.semantics.negated_concepts
        for item in eligible
    )

    expresses_acceptance = any(
        item.semantics.expresses_acceptance is True
        for item in eligible
    )

    expresses_rejection = any(
        item.semantics.expresses_rejection is True
        for item in eligible
    )

    return EvidenceSemantics(
        confirms_completion=confirms_completion,
        requests_next_step=requests_next_step,
        requests_followup=requests_followup,
        confirms_approval=confirms_approval,
        expresses_acceptance=expresses_acceptance,
        expresses_rejection=expresses_rejection,
        negated_concepts=tuple(sorted(negated)),
        concerns_same_work_item=True,
    )


def _synthetic_evidence(
    evidence_id: str,
    semantics: EvidenceSemantics,
) -> SemanticEvidence:
    source = _extract(
        evidence_id,
        "Synthetic composed semantic evidence.",
        source_system="composition",
    )

    return replace(
        source,
        semantics=semantics,
    )


def test_current_reasoner_cannot_use_separate_completion_and_next_step():
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

    assert result.support_level == "primary_only"
    assert result.recommended_focus is None


def test_composition_adapter_can_create_joint_semantics():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    semantics = _compose_semantics(
        (
            completion,
            next_step,
        )
    )

    assert semantics.confirms_completion is True
    assert semantics.requests_next_step is True


def test_synthetic_composed_evidence_activates_existing_joint_reasoning():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed_semantics = _compose_semantics(
        (
            completion,
            next_step,
        )
    )

    synthetic = _synthetic_evidence(
        "COMPOSED-COMPLETION-NEXT",
        composed_semantics,
    )

    result = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            synthetic,
        ),
    )

    assert result.support_level == "supported_by_secondary_context"
    assert result.recommended_focus == "next_step_followup"


def test_adapter_does_not_change_original_evidence():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    completion_semantics = completion.semantics
    next_step_semantics = next_step.semantics

    composed = _compose_semantics(
        (
            completion,
            next_step,
        )
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True

    assert completion.semantics == completion_semantics
    assert next_step.semantics == next_step_semantics


def test_adapter_requires_both_facts_for_joint_completion_next_step():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    completion_only = _compose_semantics(
        (completion,)
    )

    assert completion_only.confirms_completion is True
    assert completion_only.requests_next_step is False

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    next_step_only = _compose_semantics(
        (next_step,)
    )

    assert next_step_only.confirms_completion is False
    assert next_step_only.requests_next_step is True


def test_negated_completion_blocks_positive_composed_completion():
    negated_completion = _extract(
        "NEGATED-COMPLETION",
        "The migration workshop is not complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed = _compose_semantics(
        (
            negated_completion,
            next_step,
        )
    )

    assert composed.confirms_completion is False
    assert composed.requests_next_step is True


def test_wrong_identity_is_not_composed_into_joint_semantics():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    wrong = _extract(
        "WRONG-NEXT",
        "The customer asks what comes next.",
    )

    wrong = replace(
        wrong,
        identity=replace(
            wrong.identity,
            quality=IdentityQuality.NO_MATCH,
        ),
    )

    composed = _compose_semantics(
        (
            completion,
            wrong,
        )
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False


def test_composed_semantics_can_be_reasoned_without_source_data_loss():
    completion = _extract(
        "CRM-COMPLETION",
        "The migration workshop is complete.",
        source_system="crm",
    )

    next_step = _extract(
        "EMAIL-NEXT",
        "The customer asks what comes next.",
        source_system="email",
    )

    composed = _compose_semantics(
        (
            completion,
            next_step,
        )
    )

    synthetic = _synthetic_evidence(
        "COMPOSED",
        composed,
    )

    result = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(synthetic),
    )

    assert result.recommended_focus == "next_step_followup"

    assert completion.provenance.source_system == "crm"
    assert next_step.provenance.source_system == "email"


def test_redundant_completion_does_not_change_composed_truth():
    first = _extract(
        "COMPLETION-1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "COMPLETION-2",
        "The migration workshop is complete.",
    )

    first_only = _compose_semantics(
        (first,)
    )

    both = _compose_semantics(
        (
            first,
            second,
        )
    )

    assert first_only == both


def test_redundant_next_step_does_not_change_composed_truth():
    first = _extract(
        "NEXT-1",
        "The customer asks what comes next.",
    )

    second = _extract(
        "NEXT-2",
        "The customer asks what comes next.",
    )

    first_only = _compose_semantics(
        (first,)
    )

    both = _compose_semantics(
        (
            first,
            second,
        )
    )

    assert first_only == both


def test_distinct_facts_change_composed_semantics():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT",
        "The customer asks what comes next.",
    )

    completion_only = _compose_semantics(
        (completion,)
    )

    combined = _compose_semantics(
        (
            completion,
            next_step,
        )
    )

    assert completion_only.requests_next_step is False
    assert combined.requests_next_step is True


def test_composed_followup_can_activate_existing_reasoning_rule():
    first = _extract(
        "FOLLOWUP-1",
        "The customer wants another discussion about the proposal.",
    )

    second = _extract(
        "FOLLOWUP-2",
        "The customer would like to speak about the offer again.",
    )

    composed = _compose_semantics(
        (
            first,
            second,
        )
    )

    assert composed.requests_followup is True

    synthetic = _synthetic_evidence(
        "COMPOSED-FOLLOWUP",
        composed,
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(synthetic),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_composition_adapter_has_no_benchmark_specific_fields():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT",
        "The customer asks what comes next.",
    )

    composed = _compose_semantics(
        (
            completion,
            next_step,
        )
    )

    assert not hasattr(
        composed,
        "expected_direction",
    )

    assert not hasattr(
        composed,
        "benchmark_family",
    )

    assert not hasattr(
        composed,
        "winner",
    )

    assert not hasattr(
        composed,
        "priority",
    )


def test_production_reasoner_is_unchanged_by_adapter():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT",
        "The customer asks what comes next.",
    )

    before = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            completion,
            next_step,
        ),
    )

    composed = _compose_semantics(
        (
            completion,
            next_step,
        )
    )

    synthetic = _synthetic_evidence(
        "COMPOSED",
        composed,
    )

    after = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            completion,
            next_step,
        ),
    )

    composed_result = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            synthetic,
        ),
    )

    assert before == after

    assert before.support_level == "primary_only"
    assert before.recommended_focus is None

    assert composed_result.support_level == (
        "supported_by_secondary_context"
    )
    assert composed_result.recommended_focus == (
        "next_step_followup"
    )