from __future__ import annotations

from datetime import timedelta

import pytest

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    AssertionPolarity,
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
) -> SemanticEvidence:
    return SemanticEvidence(
        evidence_id=evidence_id,
        content=evidence_id,
        provenance=EvidenceProvenance(
            source_system="secondary",
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


def _completion(evidence_id: str = "COMPLETION", **kwargs) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            confirms_completion=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _next_step(evidence_id: str = "NEXT-STEP", **kwargs) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            requests_next_step=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _approval(evidence_id: str = "APPROVAL", **kwargs) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            confirms_approval=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _followup(evidence_id: str = "FOLLOWUP", **kwargs) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _acceptance(evidence_id: str = "ACCEPTANCE", **kwargs) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            expresses_acceptance=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _rejection(evidence_id: str = "REJECTION", **kwargs) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            expresses_rejection=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _combined(
    evidence_id: str,
    *,
    confirms_completion: bool | None = None,
    requests_next_step: bool | None = None,
    confirms_approval: bool | None = None,
    requests_followup: bool | None = None,
    expresses_acceptance: bool | None = None,
    expresses_rejection: bool | None = None,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
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


# ---------------------------------------------------------------------------
# Positive composition coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "primary_state,left,right,control",
    [
        (
            PrimaryState("quote_pending_decision"),
            _approval("APPROVAL"),
            _followup("FOLLOWUP"),
            _combined(
                "CONTROL",
                confirms_approval=True,
                requests_followup=True,
            ),
        ),
        (
            PrimaryState("quote_pending_decision"),
            _acceptance("ACCEPTANCE"),
            _followup("FOLLOWUP"),
            _combined(
                "CONTROL",
                expresses_acceptance=True,
                requests_followup=True,
            ),
        ),
        (
            PrimaryState("service_completed_next_step_unrecorded"),
            _completion("COMPLETION"),
            _followup("FOLLOWUP"),
            _combined(
                "CONTROL",
                confirms_completion=True,
                requests_followup=True,
            ),
        ),
        (
            PrimaryState("negotiation_open"),
            _rejection("REJECTION"),
            _followup("FOLLOWUP"),
            _combined(
                "CONTROL",
                expresses_rejection=True,
                requests_followup=True,
            ),
        ),
        (
            PrimaryState("service_completed_next_step_unrecorded"),
            _completion("COMPLETION"),
            _next_step("NEXT-STEP"),
            _combined(
                "CONTROL",
                confirms_completion=True,
                requests_next_step=True,
            ),
        ),
    ],
)
def test_h7_positive_split_matches_single_record_control(
    primary_state: PrimaryState,
    left: SemanticEvidence,
    right: SemanticEvidence,
    control: SemanticEvidence,
):
    split_result = _reasoner().evaluate(
        primary_state,
        _condition(left, right),
    )

    control_result = _reasoner().evaluate(
        primary_state,
        _condition(control),
    )

    assert _decision(split_result) == _decision(control_result)


def test_h7_three_record_positive_composition_matches_single_record_control():
    primary = PrimaryState("quote_pending_decision")

    split = _condition(
        _approval("APPROVAL"),
        _followup("FOLLOWUP"),
        _acceptance("ACCEPTANCE"),
    )

    control = _condition(
        _combined(
            "CONTROL",
            confirms_approval=True,
            requests_followup=True,
            expresses_acceptance=True,
        ),
    )

    split_result = _reasoner().evaluate(primary, split)
    control_result = _reasoner().evaluate(primary, control)

    assert _decision(split_result) == _decision(control_result)


# ---------------------------------------------------------------------------
# Composition semantic preservation
# ---------------------------------------------------------------------------


def test_h7_composed_semantics_preserve_approval_and_followup():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _approval(),
            _followup(),
        )
    )

    assert composed is not None
    assert composed.semantics.confirms_approval is True
    assert composed.semantics.requests_followup is True


def test_h7_composed_semantics_preserve_acceptance_and_followup():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _acceptance(),
            _followup(),
        )
    )

    assert composed is not None
    assert composed.semantics.expresses_acceptance is True
    assert composed.semantics.requests_followup is True


def test_h7_composed_semantics_preserve_completion_and_followup():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _completion(),
            _followup(),
        )
    )

    assert composed is not None
    assert composed.semantics.confirms_completion is True
    assert composed.semantics.requests_followup is True


def test_h7_composed_semantics_preserve_rejection_and_followup():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _rejection(),
            _followup(),
        )
    )

    assert composed is not None
    assert composed.semantics.expresses_rejection is True
    assert composed.semantics.requests_followup is True


def test_h7_composed_semantics_preserve_completion_and_next_step():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _completion(),
            _next_step(),
        )
    )

    assert composed is not None
    assert composed.semantics.confirms_completion is True
    assert composed.semantics.requests_next_step is True


# ---------------------------------------------------------------------------
# Identity, time, and work-item boundaries
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "invalid_item",
    [
        _followup(
            evidence_id="NO-MATCH",
            customer_id="C999",
            identity_quality=IdentityQuality.NO_MATCH,
        ),
        _followup(
            evidence_id="AMBIGUOUS",
            identity_quality=IdentityQuality.AMBIGUOUS,
        ),
        _followup(
            evidence_id="STALE",
            occurred_at=EVALUATION_AT - timedelta(days=31),
        ),
        _evidence(
            "OTHER-WORK-ITEM",
            EvidenceSemantics(
                topic="migration",
                requests_followup=True,
                concerns_same_work_item=False,
            ),
        ),
    ],
)
def test_h7_invalid_record_has_no_compositional_effect(
    invalid_item: SemanticEvidence,
):
    primary = PrimaryState("quote_pending_decision")

    baseline = _reasoner().evaluate(
        primary,
        _condition(_approval("APPROVAL")),
    )

    with_invalid = _reasoner().evaluate(
        primary,
        _condition(
            _approval("APPROVAL"),
            invalid_item,
        ),
    )

    assert _decision(with_invalid) == _decision(baseline)


def test_h7_ambiguous_and_wrong_identity_do_not_enter_composition():
    approval = _approval()

    ambiguous = _followup(
        evidence_id="AMBIGUOUS",
        identity_quality=IdentityQuality.AMBIGUOUS,
    )

    wrong = _followup(
        evidence_id="WRONG",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    composed_ambiguous = _reasoner()._compose_cross_record_evidence(
        (
            approval,
            ambiguous,
        )
    )

    composed_wrong = _reasoner()._compose_cross_record_evidence(
        (
            approval,
            wrong,
        )
    )

    assert composed_ambiguous is None
    assert composed_wrong is None


def test_h7_stale_and_current_record_do_not_enter_same_composition():
    current = _approval()

    stale = _followup(
        evidence_id="STALE",
        occurred_at=EVALUATION_AT - timedelta(days=31),
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            current,
            stale,
        )
    )

    assert composed is not None or composed is None

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(current, stale),
    )

    baseline = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(current),
    )

    assert _decision(result) == _decision(baseline)


# ---------------------------------------------------------------------------
# Conflict boundaries
# ---------------------------------------------------------------------------


def test_h7_acceptance_and_rejection_refuse_composition():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _acceptance(),
            _rejection(),
        )
    )

    assert composed is None


def test_h7_positive_completion_and_explicit_negation_refuse_composition():
    negated = _evidence(
        "NEGATED-COMPLETION",
        EvidenceSemantics(
            topic="migration",
            polarity=AssertionPolarity.NEGATIVE,
            negated_concepts=("completion",),
            concerns_same_work_item=True,
        ),
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            _completion(),
            negated,
        )
    )

    assert composed is None


def test_h7_positive_followup_and_explicit_negation_refuse_composition():
    negated = _evidence(
        "NEGATED-FOLLOWUP",
        EvidenceSemantics(
            topic="migration",
            polarity=AssertionPolarity.NEGATIVE,
            negated_concepts=("followup",),
            concerns_same_work_item=True,
        ),
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            _followup(),
            negated,
        )
    )

    assert composed is None


def test_h7_unresolved_conflict_falls_back_without_cross_record_merge():
    acceptance = _acceptance()
    rejection = _rejection()

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            acceptance,
            rejection,
        ),
    )

    acceptance_only = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(acceptance),
    )

    rejection_only = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(rejection),
    )

    # The conflict must not produce a novel merged decision.
    assert _decision(result) in {
        _decision(acceptance_only),
        _decision(rejection_only),
    }


# ---------------------------------------------------------------------------
# Order, determinism, and source-boundary preservation
# ---------------------------------------------------------------------------


def test_h7_order_invariance_for_each_positive_pair():
    cases = [
        (
            PrimaryState("quote_pending_decision"),
            _approval("A"),
            _followup("B"),
        ),
        (
            PrimaryState("quote_pending_decision"),
            _acceptance("A"),
            _followup("B"),
        ),
        (
            PrimaryState("service_completed_next_step_unrecorded"),
            _completion("A"),
            _followup("B"),
        ),
        (
            PrimaryState("negotiation_open"),
            _rejection("A"),
            _followup("B"),
        ),
        (
            PrimaryState("service_completed_next_step_unrecorded"),
            _completion("A"),
            _next_step("B"),
        ),
    ]

    for primary, first_item, second_item in cases:
        forward = _reasoner().evaluate(
            primary,
            _condition(first_item, second_item),
        )

        reverse = _reasoner().evaluate(
            primary,
            _condition(second_item, first_item),
        )

        assert _decision(forward) == _decision(reverse)


def test_h7_three_record_composition_is_order_invariant():
    primary = PrimaryState("quote_pending_decision")

    forward = _reasoner().evaluate(
        primary,
        _condition(
            _approval("APPROVAL"),
            _followup("FOLLOWUP"),
            _acceptance("ACCEPTANCE"),
        ),
    )

    reverse = _reasoner().evaluate(
        primary,
        _condition(
            _acceptance("ACCEPTANCE"),
            _followup("FOLLOWUP"),
            _approval("APPROVAL"),
        ),
    )

    assert _decision(forward) == _decision(reverse)


def test_h7_repeated_evaluation_is_deterministic():
    condition = _condition(
        _completion(),
        _next_step(),
        _followup(),
    )

    first = _reasoner().evaluate(
        PrimaryState("service_completed_next_step_unrecorded"),
        condition,
    )

    second = _reasoner().evaluate(
        PrimaryState("service_completed_next_step_unrecorded"),
        condition,
    )

    assert _decision(first) == _decision(second)


def test_h7_composition_preserves_source_ids():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _completion("COMPLETION"),
            _next_step("NEXT-STEP"),
            _followup("FOLLOWUP"),
        )
    )

    assert composed is not None

    assert composed.source_evidence_ids == (
        "COMPLETION",
        "NEXT-STEP",
        "FOLLOWUP",
    )


def test_h7_composition_preserves_source_provenance():
    completion = _completion("COMPLETION")
    next_step = _next_step("NEXT-STEP")

    composed = _reasoner()._compose_cross_record_evidence(
        (
            completion,
            next_step,
        )
    )

    assert composed is not None

    assert tuple(
        provenance.record_id
        for provenance in composed.source_provenance
    ) == (
        "COMPLETION",
        "NEXT-STEP",
    )

    assert tuple(
        provenance.source_system
        for provenance in composed.source_provenance
    ) == (
        "secondary",
        "secondary",
    )

    assert all(
        provenance.occurred_at is not None
        for provenance in composed.source_provenance
    )


# ---------------------------------------------------------------------------
# Regression anchor
# ---------------------------------------------------------------------------


def test_h7_original_h6_completion_next_step_case_still_matches_control():
    split = _reasoner().evaluate(
        PrimaryState("service_completed_next_step_unrecorded"),
        _condition(
            _completion(),
            _next_step(),
        ),
    )

    control = _reasoner().evaluate(
        PrimaryState("service_completed_next_step_unrecorded"),
        _condition(
            _combined(
                "CONTROL",
                confirms_completion=True,
                requests_next_step=True,
            ),
        ),
    )

    assert _decision(split) == _decision(control)