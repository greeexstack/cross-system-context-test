from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from experiment.v03.evidence import EvidenceCondition, IdentityQuality
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


def _evidence(
    text: str,
    *,
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    occurred_at: str | None = "2026-09-12T10:00:00Z",
):
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id="NEGATIVE",
        content=text,
        source_system="diagnostic",
        record_id="NEGATIVE",
        occurred_at=occurred_at,
        customer_id="C001",
        identity_quality=identity_quality,
    ).evidence


def _state(result) -> tuple:
    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


PRIMARY = PrimaryState("quote_pending_decision")

BASELINE_STATE = _state(
    _reasoner().evaluate(
        PRIMARY,
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )
)


def test_mr6_ambiguous_identity_does_not_receive_confirmed_evidence_effect():
    result = _reasoner().evaluate(
        PRIMARY,
        EvidenceCondition(
            availability="available",
            items=(
                _evidence(
                    "The customer wants another discussion about the proposal.",
                    identity_quality=IdentityQuality.AMBIGUOUS,
                ),
            ),
        ),
    )

    assert result.interpretation_class == PRIMARY.interpretation_class
    assert result.decision_strength == PRIMARY.decision_strength
    assert result.support_level == "primary_only"


def test_mr7_stale_evidence_does_not_change_current_interpretation():
    result = _reasoner().evaluate(
        PRIMARY,
        EvidenceCondition(
            availability="available",
            items=(
                _evidence(
                    "The customer wants another discussion about the proposal.",
                    occurred_at="2026-07-01T10:00:00Z",
                ),
            ),
        ),
    )

    assert result.interpretation_class == PRIMARY.interpretation_class
    assert result.decision_strength == PRIMARY.decision_strength
    assert result.support_level == "temporal_context_rejected"


def test_mr8_unavailable_source_has_explicit_safe_fallback():
    result = _reasoner().evaluate(
        PRIMARY,
        EvidenceCondition(
            availability="unavailable",
            items=(),
        ),
    )

    assert _state(result) == (
        PRIMARY.interpretation_class,
        "safe_fallback_primary_only",
        PRIMARY.decision_strength,
        None,
    )


def test_mr9_removing_secondary_evidence_removes_secondary_effect():
    reasoner = _reasoner()

    with_secondary = reasoner.evaluate(
        PRIMARY,
        EvidenceCondition(
            availability="available",
            items=(
                _evidence(
                    "The customer wants another discussion about the proposal.",
                ),
            ),
        ),
    )

    primary_only = reasoner.evaluate(
        PRIMARY,
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    assert with_secondary.interpretation_class == "quote_followup_pending"
    assert with_secondary.support_level == "supported_by_secondary_context"

    assert _state(primary_only) == BASELINE_STATE


def test_mr10_same_relation_survives_different_workflow_vocabulary():
    reasoner = _reasoner()

    primary = PrimaryState("service_completed_next_step_unrecorded")

    result_a = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(
                _evidence(
                    "The migration workshop is complete and the customer "
                    "is asking what comes next.",
                ),
            ),
        ),
    )

    result_b = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(
                _evidence(
                    "The onboarding session has finished and the customer "
                    "wants guidance on the next handoff.",
                ),
            ),
        ),
    )

    assert result_a.support_level == "supported_by_secondary_context"
    assert result_b.support_level == "supported_by_secondary_context"

    assert result_a.recommended_focus == "next_step_followup"
    assert result_b.recommended_focus == "next_step_followup"

    assert result_a.interpretation_class == primary.interpretation_class
    assert result_b.interpretation_class == primary.interpretation_class
def test_mr10_cross_workflow_relation_survives_semantic_transfer():
    reasoner = _reasoner()

    primary = PrimaryState("quote_pending_decision")

    from experiment.v03.evidence import EvidenceSemantics

    evidence_a = _evidence(
        "A finance workflow confirms the proposed spend is approved "
        "and procurement is progressing."
    )

    evidence_b = replace(
        evidence_a,
        evidence_id="NEGATIVE-WORKFLOW",
        content=(
            "A deployment workflow confirms the rollout budget is approved "
            "and the purchasing process is progressing."
        ),
        semantics=EvidenceSemantics(
            topic="deployment",
            confirms_approval=True,
            expresses_acceptance=True,
            concerns_same_work_item=True,
        ),
    )

    result_a = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(
                replace(
                    evidence_a,
                    semantics=EvidenceSemantics(
                        topic="finance",
                        confirms_approval=True,
                        expresses_acceptance=True,
                        concerns_same_work_item=True,
                    ),
                ),
            ),
        ),
    )

    result_b = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(evidence_b,),
        ),
    )

    assert result_a.support_level == "secondary_supported"
    assert result_b.support_level == "secondary_supported"

    assert result_a.decision_strength == "stronger"
    assert result_b.decision_strength == "stronger"

    assert result_a.interpretation_class == primary.interpretation_class
    assert result_b.interpretation_class == primary.interpretation_class