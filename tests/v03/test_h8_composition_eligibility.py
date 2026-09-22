from __future__ import annotations

from datetime import timedelta

import pytest

from experiment.v03.battery import EVALUATION_AT
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


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _evidence(
    evidence_id: str,
    semantics: EvidenceSemantics,
    *,
    customer_id: str = "C001",
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    occurred_at=None,
    source_system: str = "secondary",
) -> SemanticEvidence:
    return SemanticEvidence(
        evidence_id=evidence_id,
        content=evidence_id,
        provenance=EvidenceProvenance(
            source_system=source_system,
            record_id=evidence_id,
            occurred_at=(
                EVALUATION_AT - timedelta(days=1)
                if occurred_at is None
                else occurred_at
            ),
        ),
        identity=EvidenceIdentity(
            customer_id=customer_id,
            quality=identity_quality,
        ),
        semantics=semantics,
    )


def _completion(
    evidence_id: str = "COMPLETION",
    *,
    concerns_same_work_item: bool | None = True,
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            confirms_completion=True,
            concerns_same_work_item=concerns_same_work_item,
        ),
        **kwargs,
    )


def _next_step(
    evidence_id: str = "NEXT-STEP",
    *,
    concerns_same_work_item: bool | None = True,
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            requests_next_step=True,
            concerns_same_work_item=concerns_same_work_item,
        ),
        **kwargs,
    )


def _approval(
    evidence_id: str = "APPROVAL",
    *,
    concerns_same_work_item: bool | None = True,
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            confirms_approval=True,
            concerns_same_work_item=concerns_same_work_item,
        ),
        **kwargs,
    )


def _followup(
    evidence_id: str = "FOLLOWUP",
    *,
    concerns_same_work_item: bool | None = True,
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            requests_followup=True,
            concerns_same_work_item=concerns_same_work_item,
        ),
        **kwargs,
    )


def _acceptance(
    evidence_id: str = "ACCEPTANCE",
    *,
    concerns_same_work_item: bool | None = True,
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            expresses_acceptance=True,
            concerns_same_work_item=concerns_same_work_item,
        ),
        **kwargs,
    )
def _rejection(
    evidence_id: str = "REJECTION",
    *,
    concerns_same_work_item: bool | None = True,
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            expresses_rejection=True,
            concerns_same_work_item=concerns_same_work_item,
        ),
        **kwargs,
    )

def _combined_semantics(
    evidence_id: str,
    *,
    confirms_completion: bool | None = None,
    requests_next_step: bool | None = None,
    confirms_approval: bool | None = None,
    requests_followup: bool | None = None,
    expresses_acceptance: bool | None = None,
    expresses_rejection: bool | None = None,
    topic: str | None = "migration",
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic=topic,
            confirms_completion=confirms_completion,
            requests_next_step=requests_next_step,
            confirms_approval=confirms_approval,
            requests_followup=requests_followup,
            expresses_acceptance=expresses_acceptance,
            expresses_rejection=expresses_rejection,
            concerns_same_work_item=True,
        ),
    )


def _condition(
    *items: SemanticEvidence,
) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=tuple(items),
    )


def _decision(result) -> tuple[str, str, str, str | None]:
    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def _semantic_signature(
    semantics: EvidenceSemantics,
) -> tuple:
    return (
        semantics.topic,
        semantics.polarity,
        semantics.negated_concepts,
        semantics.requests_followup,
        semantics.expresses_acceptance,
        semantics.expresses_rejection,
        semantics.confirms_approval,
        semantics.confirms_completion,
        semantics.requests_next_step,
        semantics.concerns_same_work_item,
    )


def _lift_composed(
    composed,
    evidence_id: str,
) -> SemanticEvidence:
    """
    Test-layer lifting of a composed semantic state back into a
    SemanticEvidence container.

    This does not alter production code. It allows the already measured
    production composition operation to be applied again so that grouping
    behavior can be tested.
    """

    return SemanticEvidence(
        evidence_id=evidence_id,
        content=evidence_id,
        provenance=EvidenceProvenance(
            source_system="composition",
            record_id=evidence_id,
            occurred_at=EVALUATION_AT - timedelta(days=1),
        ),
        identity=EvidenceIdentity(
            customer_id="C001",
            quality=IdentityQuality.CONFIRMED,
        ),
        semantics=composed.semantics,
    )


# ---------------------------------------------------------------------------
# H8-I1: unknown work-item relation
# ---------------------------------------------------------------------------


def test_h8_unknown_work_item_relation_is_not_composable():
    completion = _completion("COMPLETION")
    unknown_followup = _followup(
        "UNKNOWN-FOLLOWUP",
        concerns_same_work_item=None,
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            completion,
            unknown_followup,
        )
    )

    assert composed is None


def test_h8_unknown_relation_does_not_appear_in_composed_source_set():
    completion = _completion("COMPLETION")
    next_step = _next_step("NEXT-STEP")
    unknown_followup = _followup(
        "UNKNOWN-FOLLOWUP",
        concerns_same_work_item=None,
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            completion,
            next_step,
            unknown_followup,
        )
    )

    assert composed is not None

    assert composed.source_evidence_ids == (
        "COMPLETION",
        "NEXT-STEP",
    )

    assert "UNKNOWN-FOLLOWUP" not in composed.source_evidence_ids


def test_h8_unknown_relation_does_not_change_composition_semantics():
    completion = _completion("COMPLETION")
    next_step = _next_step("NEXT-STEP")

    unknown_followup = _followup(
        "UNKNOWN-FOLLOWUP",
        concerns_same_work_item=None,
    )

    baseline = _reasoner()._compose_cross_record_evidence(
        (
            completion,
            next_step,
        )
    )

    with_unknown = _reasoner()._compose_cross_record_evidence(
        (
            completion,
            next_step,
            unknown_followup,
        )
    )

    assert baseline is not None
    assert with_unknown is not None

    assert _semantic_signature(
        baseline.semantics
    ) == _semantic_signature(
        with_unknown.semantics
    )


# ---------------------------------------------------------------------------
# H8-I2: mixed eligibility containment
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "invalid_item",
    [
        _followup(
            "NO-MATCH",
            customer_id="C999",
            identity_quality=IdentityQuality.NO_MATCH,
        ),
        _followup(
            "AMBIGUOUS",
            identity_quality=IdentityQuality.AMBIGUOUS,
        ),
        _followup(
            "STALE",
            occurred_at=EVALUATION_AT - timedelta(days=31),
        ),
        _followup(
            "OTHER-WORK-ITEM",
            concerns_same_work_item=False,
        ),
        _followup(
            "UNKNOWN-WORK-ITEM",
            concerns_same_work_item=None,
        ),
    ],
)
def test_h8_mixed_eligible_and_ineligible_records_preserve_production_behavior(
    invalid_item: SemanticEvidence,
):
    completion = _completion("COMPLETION")
    next_step = _next_step("NEXT-STEP")

    primary = PrimaryState(
        "service_completed_next_step_unrecorded"
    )

    baseline = _reasoner().evaluate(
        primary,
        _condition(
            completion,
            next_step,
        ),
    )

    mixed = _reasoner().evaluate(
        primary,
        _condition(
            completion,
            next_step,
            invalid_item,
        ),
    )

    assert _decision(mixed) == _decision(baseline)


def test_h8_stale_record_does_not_change_production_decision():
    approval = _approval("APPROVAL")

    stale_followup = _followup(
        "STALE-FOLLOWUP",
        occurred_at=EVALUATION_AT - timedelta(days=31),
    )

    baseline = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(approval),
    )

    mixed = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            approval,
            stale_followup,
        ),
    )

    assert _decision(mixed) == _decision(baseline)


def test_h8_unknown_relation_does_not_change_composable_source_set():
    approval = _approval("APPROVAL")
    followup = _followup("FOLLOWUP")
    unknown = _followup(
        "UNKNOWN",
        concerns_same_work_item=None,
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            approval,
            followup,
            unknown,
        )
    )

    assert composed is not None

    assert composed.source_evidence_ids == (
        "APPROVAL",
        "FOLLOWUP",
    )


# ---------------------------------------------------------------------------
# H8-I3: associativity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "primary,left,middle,right,control",
    [
        (
            PrimaryState("quote_pending_decision"),
            _approval("A"),
            _followup("B"),
            _acceptance("C"),
            _combined_semantics(
                "CONTROL",
                confirms_approval=True,
                requests_followup=True,
                expresses_acceptance=True,
            ),
        ),
        (
            PrimaryState("service_completed_next_step_unrecorded"),
            _completion("A"),
            _next_step("B"),
            _followup("C"),
            _combined_semantics(
                "CONTROL",
                confirms_completion=True,
                requests_next_step=True,
                requests_followup=True,
            ),
        ),
    ],
)
def test_h8_grouping_matches_direct_three_record_composition(
    primary: PrimaryState,
    left: SemanticEvidence,
    middle: SemanticEvidence,
    right: SemanticEvidence,
    control: SemanticEvidence,
):
    reasoner = _reasoner()

    direct = reasoner._compose_cross_record_evidence(
        (
            left,
            middle,
            right,
        )
    )

    first_group = reasoner._compose_cross_record_evidence(
        (
            left,
            middle,
        )
    )

    assert direct is not None
    assert first_group is not None

    grouped = reasoner._compose_cross_record_evidence(
        (
            _lift_composed(
                first_group,
                "GROUP-AB",
            ),
            right,
        )
    )

    assert grouped is not None

    assert _semantic_signature(
        direct.semantics
    ) == _semantic_signature(
        grouped.semantics
    )

    direct_result = reasoner.evaluate(
        primary,
        _condition(
            left,
            middle,
            right,
        ),
    )

    grouped_result = reasoner.evaluate(
        primary,
        _condition(
            _lift_composed(
                first_group,
                "GROUP-AB",
            ),
            right,
        ),
    )

    control_result = reasoner.evaluate(
        primary,
        _condition(control),
    )

    assert _decision(direct_result) == _decision(control_result)
    assert _decision(grouped_result) == _decision(control_result)


def test_h8_grouping_with_reversed_partition_is_semantically_stable():
    reasoner = _reasoner()

    a = _approval("A")
    b = _followup("B")
    c = _acceptance("C")

    ab = reasoner._compose_cross_record_evidence((a, b))
    bc = reasoner._compose_cross_record_evidence((b, c))

    assert ab is not None
    assert bc is not None

    ab_then_c = reasoner._compose_cross_record_evidence(
        (
            _lift_composed(ab, "AB"),
            c,
        )
    )

    a_then_bc = reasoner._compose_cross_record_evidence(
        (
            a,
            _lift_composed(bc, "BC"),
        )
    )

    direct = reasoner._compose_cross_record_evidence(
        (
            a,
            b,
            c,
        )
    )

    assert ab_then_c is not None
    assert a_then_bc is not None
    assert direct is not None

    assert _semantic_signature(
        ab_then_c.semantics
    ) == _semantic_signature(
        direct.semantics
    )

    assert _semantic_signature(
        a_then_bc.semantics
    ) == _semantic_signature(
        direct.semantics
    )


# ---------------------------------------------------------------------------
# H8-I4: order invariance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "items",
    [
        (
            _approval("A"),
            _followup("B"),
            _acceptance("C"),
        ),
        (
            _completion("A"),
            _next_step("B"),
            _followup("C"),
        ),
        (
            _rejection("A"),
            _followup("B"),
        ),
    ],
)
def test_h8_composition_is_order_invariant(
    items: tuple[SemanticEvidence, ...],
):
    reasoner = _reasoner()

    forward = reasoner._compose_cross_record_evidence(items)
    reverse = reasoner._compose_cross_record_evidence(tuple(reversed(items)))

    if forward is None or reverse is None:
        assert forward is None
        assert reverse is None
        return

    assert _semantic_signature(
        forward.semantics
    ) == _semantic_signature(
        reverse.semantics
    )


# ---------------------------------------------------------------------------
# H8-I5: determinism
# ---------------------------------------------------------------------------


def test_h8_composition_is_deterministic():
    items = (
        _approval("APPROVAL"),
        _followup("FOLLOWUP"),
        _acceptance("ACCEPTANCE"),
    )

    reasoner = _reasoner()

    first = reasoner._compose_cross_record_evidence(items)
    second = reasoner._compose_cross_record_evidence(items)

    assert first is not None
    assert second is not None

    assert _semantic_signature(
        first.semantics
    ) == _semantic_signature(
        second.semantics
    )

    assert first.source_evidence_ids == second.source_evidence_ids
    assert first.source_provenance == second.source_provenance


# ---------------------------------------------------------------------------
# Provenance / evidence-boundary preservation
# ---------------------------------------------------------------------------


def test_h8_direct_three_record_composition_preserves_leaf_boundaries():
    a = _approval("APPROVAL")
    b = _followup("FOLLOWUP")
    c = _acceptance("ACCEPTANCE")

    composed = _reasoner()._compose_cross_record_evidence(
        (
            a,
            b,
            c,
        )
    )

    assert composed is not None

    assert composed.source_evidence_ids == (
        "APPROVAL",
        "FOLLOWUP",
        "ACCEPTANCE",
    )

    assert tuple(
        provenance.record_id
        for provenance in composed.source_provenance
    ) == (
        "APPROVAL",
        "FOLLOWUP",
        "ACCEPTANCE",
    )

    assert len(composed.source_evidence_ids) == 3
    assert len(composed.source_provenance) == 3


# ---------------------------------------------------------------------------
# Topic compatibility diagnostic
# ---------------------------------------------------------------------------


def test_h8_topic_difference_is_recorded_as_diagnostic_not_assumed_invalid():
    approval = _evidence(
        "APPROVAL",
        EvidenceSemantics(
            topic="finance",
            confirms_approval=True,
            concerns_same_work_item=True,
        ),
    )

    followup = _evidence(
        "FOLLOWUP",
        EvidenceSemantics(
            topic="customer_contact",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            approval,
            followup,
        )
    )

    assert composed is not None

    assert composed.source_evidence_ids == (
        "APPROVAL",
        "FOLLOWUP",
    )

    assert composed.semantics.confirms_approval is True
    assert composed.semantics.requests_followup is True


# ---------------------------------------------------------------------------
# Regression anchors
# ---------------------------------------------------------------------------


def test_h8_h6_completion_next_step_behavior_remains_unchanged():
    result = _reasoner().evaluate(
        PrimaryState("service_completed_next_step_unrecorded"),
        _condition(
            _completion(),
            _next_step(),
        ),
    )

    control = _reasoner().evaluate(
        PrimaryState("service_completed_next_step_unrecorded"),
        _condition(
            _combined_semantics(
                "CONTROL",
                confirms_completion=True,
                requests_next_step=True,
            ),
        ),
    )

    assert _decision(result) == _decision(control)


def test_h8_h7_approval_followup_behavior_remains_unchanged():
    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            _approval(),
            _followup(),
        ),
    )

    control = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            _combined_semantics(
                "CONTROL",
                confirms_approval=True,
                requests_followup=True,
            ),
        ),
    )

    assert _decision(result) == _decision(control)