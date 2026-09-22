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


STATE = PrimaryState("service_completed_next_step_unrecorded")


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


def _completion(
    evidence_id: str = "COMPLETION",
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            confirms_completion=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _next_step(
    evidence_id: str = "NEXT-STEP",
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            requests_next_step=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _approval(
    evidence_id: str = "APPROVAL",
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            confirms_approval=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _followup(
    evidence_id: str = "FOLLOWUP",
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _acceptance(
    evidence_id: str = "ACCEPTANCE",
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            expresses_acceptance=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _rejection(
    evidence_id: str = "REJECTION",
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            expresses_rejection=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _negated_completion(
    evidence_id: str = "NEGATED-COMPLETION",
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic="migration",
            polarity=AssertionPolarity.NEGATIVE,
            negated_concepts=("completion",),
            concerns_same_work_item=True,
        ),
    )


def _decision(result) -> tuple[str, str, str, str | None]:
    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def test_h6_composes_completion_and_next_step():
    result = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=(
                _completion(),
                _next_step(),
            ),
        ),
    )

    control = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=(
                _evidence(
                    "COMBINED",
                    EvidenceSemantics(
                        topic="migration",
                        confirms_completion=True,
                        requests_next_step=True,
                        concerns_same_work_item=True,
                    ),
                ),
            ),
        ),
    )

    assert _decision(result) == _decision(control)


def test_h6_composes_other_compatible_positive_facts():
    split = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(
                _approval(),
                _followup(),
            ),
        ),
    )

    control = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(
                _evidence(
                    "COMBINED",
                    EvidenceSemantics(
                        topic="migration",
                        confirms_approval=True,
                        requests_followup=True,
                        concerns_same_work_item=True,
                    ),
                ),
            ),
        ),
    )

    assert _decision(split) == _decision(control)


def test_h6_composition_is_order_invariant():
    first = (
        _completion(),
        _next_step(),
        _followup(),
    )

    second = tuple(reversed(first))

    first_result = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=first,
        ),
    )

    second_result = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=second,
        ),
    )

    assert _decision(first_result) == _decision(second_result)


def test_h6_three_record_composition_is_deterministic():
    items = (
        _completion(),
        _next_step(),
        _followup(),
    )

    first = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=items,
        ),
    )

    second = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=items,
        ),
    )

    assert _decision(first) == _decision(second)


def test_h6_same_fact_positive_and_negated_refuses_composition():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _completion(),
            _negated_completion(),
        )
    )

    assert composed is None


def test_h6_direct_acceptance_rejection_conflict_must_refuse_composition():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _acceptance(),
            _rejection(),
        )
    )

    assert composed is None


def test_h6_wrong_identity_is_excluded_before_composition():
    result = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=(
                _completion(),
                _next_step(
                    evidence_id="WRONG-ID",
                    customer_id="C999",
                    identity_quality=IdentityQuality.NO_MATCH,
                ),
            ),
        ),
    )

    control = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=(
                _completion(),
            ),
        ),
    )

    assert _decision(result) == _decision(control)


def test_h6_ambiguous_identity_is_excluded_before_composition():
    result = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=(
                _completion(),
                _next_step(
                    evidence_id="AMBIGUOUS",
                    identity_quality=IdentityQuality.AMBIGUOUS,
                ),
            ),
        ),
    )

    control = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=(
                _completion(),
            ),
        ),
    )

    assert _decision(result) == _decision(control)


def test_h6_stale_evidence_is_excluded_before_composition():
    result = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=(
                _completion(),
                _next_step(
                    evidence_id="STALE",
                    occurred_at=EVALUATION_AT - timedelta(days=31),
                ),
            ),
        ),
    )

    control = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=(
                _completion(),
            ),
        ),
    )

    assert _decision(result) == _decision(control)


def test_h6_unrelated_work_item_is_excluded_before_composition():
    result = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=(
                _completion(),
                _evidence(
                    "OTHER-WORK-ITEM",
                    EvidenceSemantics(
                        topic="migration",
                        requests_next_step=True,
                        concerns_same_work_item=False,
                    ),
                ),
            ),
        ),
    )

    control = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=(
                _completion(),
            ),
        ),
    )

    assert _decision(result) == _decision(control)


def test_h6_composed_result_retains_all_source_ids_and_provenance():
    completion = _completion()
    next_step = _next_step()
    followup = _followup()

    composed = _reasoner()._compose_cross_record_evidence(
        (
            completion,
            next_step,
            followup,
        )
    )

    assert composed is not None

    assert composed.source_evidence_ids == (
        "COMPLETION",
        "NEXT-STEP",
        "FOLLOWUP",
    )

    assert tuple(
        provenance.record_id
        for provenance in composed.source_provenance
    ) == (
        "COMPLETION",
        "NEXT-STEP",
        "FOLLOWUP",
    )

    assert tuple(
        provenance.source_system
        for provenance in composed.source_provenance
    ) == (
        "secondary",
        "secondary",
        "secondary",
    )


def test_h6_composed_semantics_preserve_distinct_facts():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _approval(),
            _followup(),
            _next_step(),
        )
    )

    assert composed is not None

    assert composed.semantics.confirms_approval is True
    assert composed.semantics.requests_followup is True
    assert composed.semantics.requests_next_step is True


@pytest.mark.parametrize(
    "items",
    [
        (
            _completion("A"),
            _next_step("B"),
        ),
        (
            _next_step("A"),
            _completion("B"),
        ),
        (
            _approval("A"),
            _followup("B"),
        ),
        (
            _followup("A"),
            _approval("B"),
        ),
    ],
)
def test_h6_composition_repeated_evaluation_is_stable(items):
    first = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=items,
        ),
    )

    second = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=items,
        ),
    )

    assert _decision(first) == _decision(second)