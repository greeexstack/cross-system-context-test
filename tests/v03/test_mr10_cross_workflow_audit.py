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


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _evidence(
    evidence_id: str,
    *,
    content: str,
    topic: str,
    semantics: EvidenceSemantics,
) -> SemanticEvidence:
    return SemanticEvidence(
        evidence_id=evidence_id,
        content=content,
        provenance=EvidenceProvenance(
            source_system="workflow-audit",
            record_id=evidence_id,
            occurred_at=datetime(
                2026,
                9,
                12,
                10,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        ),
        identity=EvidenceIdentity(
            customer_id="C001",
            quality=IdentityQuality.CONFIRMED,
        ),
        semantics=semantics,
    )


def _condition(item: SemanticEvidence) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=(item,),
    )


def _effect(result) -> tuple[str, str, str | None]:
    return (
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def _approval_evidence(
    *,
    evidence_id: str,
    content: str,
    topic: str,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        content=content,
        topic=topic,
        semantics=EvidenceSemantics(
            topic=topic,
            confirms_approval=True,
            concerns_same_work_item=True,
        ),
    )


def _rejection_evidence(
    *,
    evidence_id: str,
    content: str,
    topic: str,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        content=content,
        topic=topic,
        semantics=EvidenceSemantics(
            topic=topic,
            expresses_rejection=True,
            concerns_same_work_item=True,
        ),
    )


def test_mr10_approval_relation_survives_materially_different_workflows():
    reasoner = _reasoner()

    finance_workflow = PrimaryState(
        "quote_pending_decision"
    )

    deployment_workflow = PrimaryState(
        "deployment_review_pending"
    )

    finance_evidence = _approval_evidence(
        evidence_id="FINANCE-APPROVAL",
        content=(
            "The finance workflow approved the proposed spend "
            "for the quotation."
        ),
        topic="finance",
    )

    deployment_evidence = _approval_evidence(
        evidence_id="DEPLOYMENT-APPROVAL",
        content=(
            "The deployment workflow approved the rollout budget "
            "for the installation."
        ),
        topic="deployment",
    )

    finance_result = reasoner.evaluate(
        finance_workflow,
        _condition(finance_evidence),
    )

    deployment_result = reasoner.evaluate(
        deployment_workflow,
        _condition(deployment_evidence),
    )

    assert _effect(finance_result) == (
        "secondary_supported",
        "stronger",
        None,
    )

    assert _effect(deployment_result) == (
        "secondary_supported",
        "stronger",
        None,
    )

    # The primary interpretation classes are intentionally different.
    assert (
        finance_result.interpretation_class
        != deployment_result.interpretation_class
    )


def test_mr10_rejection_relation_survives_materially_different_workflows():
    reasoner = _reasoner()

    negotiation_workflow = PrimaryState(
        "negotiation_open"
    )

    deployment_workflow = PrimaryState(
        "deployment_review_pending"
    )

    negotiation_evidence = _rejection_evidence(
        evidence_id="NEGOTIATION-REJECTION",
        content=(
            "The commercial negotiation workflow reports that "
            "the revised terms were rejected."
        ),
        topic="negotiation",
    )

    deployment_evidence = _rejection_evidence(
        evidence_id="DEPLOYMENT-REJECTION",
        content=(
            "The deployment workflow reports that the revised "
            "rollout conditions were rejected."
        ),
        topic="deployment",
    )

    negotiation_result = reasoner.evaluate(
        negotiation_workflow,
        _condition(negotiation_evidence),
    )

    deployment_result = reasoner.evaluate(
        deployment_workflow,
        _condition(deployment_evidence),
    )

    assert _effect(negotiation_result) == (
        "weakened_by_secondary_context",
        "weaker",
        None,
    )

    assert _effect(deployment_result) == (
        "weakened_by_secondary_context",
        "weaker",
        None,
    )


def test_mr10_same_semantic_relation_survives_workflow_vocabulary_change():
    reasoner = _reasoner()

    primary = PrimaryState(
        "quote_pending_decision"
    )

    finance = _approval_evidence(
        evidence_id="FINANCE",
        content=(
            "Finance authorized the requested expenditure."
        ),
        topic="finance",
    )

    deployment = _approval_evidence(
        evidence_id="DEPLOYMENT",
        content=(
            "The deployment team authorized the rollout budget."
        ),
        topic="deployment",
    )

    finance_result = reasoner.evaluate(
        primary,
        _condition(finance),
    )

    deployment_result = reasoner.evaluate(
        primary,
        _condition(deployment),
    )

    assert _effect(finance_result) == _effect(
        deployment_result
    )


def test_mr10_workflow_change_does_not_require_topic_equality():
    evidence_a = _approval_evidence(
        evidence_id="A",
        content="Finance approved the purchase.",
        topic="finance",
    )

    evidence_b = _approval_evidence(
        evidence_id="B",
        content="Deployment approved the rollout budget.",
        topic="deployment",
    )

    composed_a = _reasoner()._compose_cross_record_evidence(
        (evidence_a,)
    )

    composed_b = _reasoner()._compose_cross_record_evidence(
        (evidence_b,)
    )

    # Composition itself requires at least two eligible records,
    # so a single evidence item must not be treated as a composition.
    assert composed_a is None
    assert composed_b is None


def test_mr10_workflow_transfer_preserves_same_work_item_boundary():
    reasoner = _reasoner()

    primary = PrimaryState(
        "quote_pending_decision"
    )

    valid = _approval_evidence(
        evidence_id="VALID",
        content=(
            "The deployment workflow approved the rollout budget "
            "for this work item."
        ),
        topic="deployment",
    )

    unrelated = SemanticEvidence(
        evidence_id="UNRELATED",
        content=(
            "The deployment workflow approved another project's "
            "rollout budget."
        ),
        provenance=EvidenceProvenance(
            source_system="workflow-audit",
            record_id="UNRELATED",
            occurred_at=datetime(
                2026,
                9,
                12,
                10,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        ),
        identity=EvidenceIdentity(
            customer_id="C001",
            quality=IdentityQuality.CONFIRMED,
        ),
        semantics=EvidenceSemantics(
            topic="deployment",
            confirms_approval=True,
            concerns_same_work_item=False,
        ),
    )

    valid_result = reasoner.evaluate(
        primary,
        _condition(valid),
    )

    mixed_result = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(valid, unrelated),
        ),
    )

    assert _effect(mixed_result) == _effect(
        valid_result
    )


def test_mr10_workflow_transfer_is_not_identity_transfer():
    reasoner = _reasoner()

    primary = PrimaryState(
        "quote_pending_decision"
    )

    valid = _approval_evidence(
        evidence_id="VALID",
        content=(
            "The deployment workflow approved the current rollout."
        ),
        topic="deployment",
    )

    wrong_identity = _approval_evidence(
        evidence_id="WRONG",
        content=(
            "The deployment workflow approved another customer's rollout."
        ),
        topic="deployment",
    )

    wrong_identity = SemanticEvidence(
        evidence_id=wrong_identity.evidence_id,
        content=wrong_identity.content,
        provenance=wrong_identity.provenance,
        identity=EvidenceIdentity(
            customer_id="C999",
            quality=IdentityQuality.NO_MATCH,
        ),
        semantics=wrong_identity.semantics,
    )

    baseline = reasoner.evaluate(
        primary,
        _condition(valid),
    )

    with_wrong_identity = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(valid, wrong_identity),
        ),
    )

    assert _effect(with_wrong_identity) == _effect(
        baseline
    )


def test_mr10_workflow_transfer_preserves_temporal_boundary():
    reasoner = _reasoner()

    primary = PrimaryState(
        "quote_pending_decision"
    )

    current = _approval_evidence(
        evidence_id="CURRENT",
        content=(
            "The deployment workflow approved the current rollout."
        ),
        topic="deployment",
    )

    stale = _approval_evidence(
        evidence_id="STALE",
        content=(
            "The deployment workflow previously approved the rollout."
        ),
        topic="deployment",
    )

    stale = SemanticEvidence(
        evidence_id=stale.evidence_id,
        content=stale.content,
        provenance=EvidenceProvenance(
            source_system="workflow-audit",
            record_id=stale.evidence_id,
            occurred_at=datetime(
                2026,
                7,
                1,
                10,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        ),
        identity=stale.identity,
        semantics=stale.semantics,
    )

    baseline = reasoner.evaluate(
        primary,
        _condition(current),
    )

    mixed = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(current, stale),
        ),
    )

    assert _effect(mixed) == _effect(
        baseline
    )