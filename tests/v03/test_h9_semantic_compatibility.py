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


def _approval(
    evidence_id: str = "APPROVAL",
    *,
    topic: str | None = "migration",
    concerns_same_work_item: bool | None = True,
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic=topic,
            confirms_approval=True,
            concerns_same_work_item=concerns_same_work_item,
        ),
        **kwargs,
    )


def _followup(
    evidence_id: str = "FOLLOWUP",
    *,
    topic: str | None = "migration",
    concerns_same_work_item: bool | None = True,
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic=topic,
            requests_followup=True,
            concerns_same_work_item=concerns_same_work_item,
        ),
        **kwargs,
    )


def _acceptance(
    evidence_id: str = "ACCEPTANCE",
    *,
    topic: str | None = "migration",
    concerns_same_work_item: bool | None = True,
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic=topic,
            expresses_acceptance=True,
            concerns_same_work_item=concerns_same_work_item,
        ),
        **kwargs,
    )


def _rejection(
    evidence_id: str = "REJECTION",
    *,
    topic: str | None = "migration",
    concerns_same_work_item: bool | None = True,
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic=topic,
            expresses_rejection=True,
            concerns_same_work_item=concerns_same_work_item,
        ),
        **kwargs,
    )


def _completion(
    evidence_id: str = "COMPLETION",
    *,
    topic: str | None = "migration",
    concerns_same_work_item: bool | None = True,
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic=topic,
            confirms_completion=True,
            concerns_same_work_item=concerns_same_work_item,
        ),
        **kwargs,
    )


def _next_step(
    evidence_id: str = "NEXT-STEP",
    *,
    topic: str | None = "migration",
    concerns_same_work_item: bool | None = True,
    **kwargs,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic=topic,
            requests_next_step=True,
            concerns_same_work_item=concerns_same_work_item,
        ),
        **kwargs,
    )


def _negated(
    evidence_id: str,
    concept: str,
    *,
    topic: str | None = "migration",
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic=topic,
            polarity=AssertionPolarity.NEGATIVE,
            negated_concepts=(concept,),
            concerns_same_work_item=True,
        ),
    )


def _combined(
    evidence_id: str,
    *,
    topic: str | None = "migration",
    confirms_approval: bool | None = None,
    expresses_acceptance: bool | None = None,
    expresses_rejection: bool | None = None,
    confirms_completion: bool | None = None,
    requests_followup: bool | None = None,
    requests_next_step: bool | None = None,
    negated_concepts: tuple[str, ...] = (),
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        EvidenceSemantics(
            topic=topic,
            negated_concepts=negated_concepts,
            confirms_approval=confirms_approval,
            expresses_acceptance=expresses_acceptance,
            expresses_rejection=expresses_rejection,
            confirms_completion=confirms_completion,
            requests_followup=requests_followup,
            requests_next_step=requests_next_step,
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


# ---------------------------------------------------------------------------
# H9 compatible factual combinations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "left,right,control",
    [
        (
            _approval("A"),
            _followup("B"),
            _combined(
                "CONTROL",
                confirms_approval=True,
                requests_followup=True,
            ),
        ),
        (
            _acceptance("A"),
            _followup("B"),
            _combined(
                "CONTROL",
                expresses_acceptance=True,
                requests_followup=True,
            ),
        ),
        (
            _completion("A"),
            _followup("B"),
            _combined(
                "CONTROL",
                confirms_completion=True,
                requests_followup=True,
            ),
        ),
        (
            _completion("A"),
            _next_step("B"),
            _combined(
                "CONTROL",
                confirms_completion=True,
                requests_next_step=True,
            ),
        ),
        (
            _rejection("A"),
            _followup("B"),
            _combined(
                "CONTROL",
                expresses_rejection=True,
                requests_followup=True,
            ),
        ),
        (
            _approval("A"),
            _completion("B"),
            _combined(
                "CONTROL",
                confirms_approval=True,
                confirms_completion=True,
            ),
        ),
    ],
)
def test_h9_compatible_split_matches_single_record_control(
    left: SemanticEvidence,
    right: SemanticEvidence,
    control: SemanticEvidence,
):
    reasoner = _reasoner()

    split = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(left, right),
    )

    single = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(control),
    )

    assert _decision(split) == _decision(single)


@pytest.mark.parametrize(
    "items",
    [
        (
            _approval("A"),
            _followup("B"),
        ),
        (
            _acceptance("A"),
            _followup("B"),
        ),
        (
            _completion("A"),
            _followup("B"),
        ),
        (
            _completion("A"),
            _next_step("B"),
        ),
        (
            _rejection("A"),
            _followup("B"),
        ),
        (
            _approval("A"),
            _completion("B"),
        ),
    ],
)
def test_h9_compatible_pairs_produce_composed_semantics(
    items: tuple[SemanticEvidence, ...],
):
    composed = _reasoner()._compose_cross_record_evidence(items)

    assert composed is not None


# ---------------------------------------------------------------------------
# H9 semantic field preservation
# ---------------------------------------------------------------------------


def test_h9_approval_followup_fields_are_preserved():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _approval(),
            _followup(),
        )
    )

    assert composed is not None
    assert composed.semantics.confirms_approval is True
    assert composed.semantics.requests_followup is True


def test_h9_acceptance_followup_fields_are_preserved():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _acceptance(),
            _followup(),
        )
    )

    assert composed is not None
    assert composed.semantics.expresses_acceptance is True
    assert composed.semantics.requests_followup is True


def test_h9_completion_followup_fields_are_preserved():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _completion(),
            _followup(),
        )
    )

    assert composed is not None
    assert composed.semantics.confirms_completion is True
    assert composed.semantics.requests_followup is True


def test_h9_approval_completion_fields_are_preserved():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _approval(),
            _completion(),
        )
    )

    assert composed is not None
    assert composed.semantics.confirms_approval is True
    assert composed.semantics.confirms_completion is True


# ---------------------------------------------------------------------------
# H9 conflict matrix
# ---------------------------------------------------------------------------


def test_h9_acceptance_rejection_refuse_composition():
    composed = _reasoner()._compose_cross_record_evidence(
        (
            _acceptance(),
            _rejection(),
        )
    )

    assert composed is None


@pytest.mark.parametrize(
    "positive,concept",
    [
        (_completion(), "completion"),
        (_followup(), "followup"),
        (_approval(), "approval"),
        (_acceptance(), "acceptance"),
        (_rejection(), "rejection"),
        (_next_step(), "next_step"),
    ],
)
def test_h9_same_concept_positive_and_negation_refuse_composition(
    positive: SemanticEvidence,
    concept: str,
):
    negative = _negated(
        f"NEGATED-{concept.upper()}",
        concept,
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            positive,
            negative,
        )
    )

    assert composed is None


@pytest.mark.parametrize(
    "positive,negative_concept",
    [
        (_approval(), "completion"),
        (_completion(), "approval"),
        (_followup(), "completion"),
        (_next_step(), "approval"),
        (_acceptance(), "completion"),
    ],
)
def test_h9_unrelated_negation_does_not_block_other_fact(
    positive: SemanticEvidence,
    negative_concept: str,
):
    negative = _negated(
        f"NEGATED-{negative_concept.upper()}",
        negative_concept,
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            positive,
            negative,
        )
    )

    assert composed is not None


# ---------------------------------------------------------------------------
# H9 mixed eligible/ineligible controls
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
            "OTHER-WORK-ITEM",
            concerns_same_work_item=False,
        ),
        _followup(
            "UNKNOWN-WORK-ITEM",
            concerns_same_work_item=None,
        ),
        _followup(
            "STALE",
            occurred_at=EVALUATION_AT - timedelta(days=31),
        ),
    ],
)
def test_h9_mixed_invalid_record_does_not_change_eligible_result(
    invalid_item: SemanticEvidence,
):
    primary = PrimaryState("quote_pending_decision")

    baseline = _reasoner().evaluate(
        primary,
        _condition(
            _approval("APPROVAL"),
            _followup("FOLLOWUP"),
        ),
    )

    mixed = _reasoner().evaluate(
        primary,
        _condition(
            _approval("APPROVAL"),
            _followup("FOLLOWUP"),
            invalid_item,
        ),
    )

    assert _decision(mixed) == _decision(baseline)


# ---------------------------------------------------------------------------
# H9 order and determinism
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "items",
    [
        (
            _approval("A"),
            _followup("B"),
        ),
        (
            _acceptance("A"),
            _followup("B"),
        ),
        (
            _completion("A"),
            _followup("B"),
        ),
        (
            _completion("A"),
            _next_step("B"),
        ),
        (
            _rejection("A"),
            _followup("B"),
        ),
        (
            _approval("A"),
            _completion("B"),
        ),
    ],
)
def test_h9_composition_is_order_invariant(
    items: tuple[SemanticEvidence, ...],
):
    reasoner = _reasoner()

    forward = reasoner._compose_cross_record_evidence(items)
    reverse = reasoner._compose_cross_record_evidence(
        tuple(reversed(items))
    )

    assert forward is not None
    assert reverse is not None

    assert _semantic_signature(
        forward.semantics
    ) == _semantic_signature(
        reverse.semantics
    )


def test_h9_three_record_composition_is_deterministic():
    items = (
        _approval("A"),
        _completion("B"),
        _followup("C"),
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


# ---------------------------------------------------------------------------
# H9 source preservation
# ---------------------------------------------------------------------------


def test_h9_composition_preserves_source_identifiers():
    a = _approval("A")
    b = _followup("B")
    c = _completion("C")

    composed = _reasoner()._compose_cross_record_evidence(
        (
            a,
            b,
            c,
        )
    )

    assert composed is not None

    assert composed.source_evidence_ids == (
        "A",
        "B",
        "C",
    )


def test_h9_composition_preserves_source_provenance():
    a = _approval("A")
    b = _followup("B")

    composed = _reasoner()._compose_cross_record_evidence(
        (
            a,
            b,
        )
    )

    assert composed is not None

    assert tuple(
        provenance.record_id
        for provenance in composed.source_provenance
    ) == (
        "A",
        "B",
    )

    assert all(
        provenance.occurred_at is not None
        for provenance in composed.source_provenance
    )


# ---------------------------------------------------------------------------
# H9 topic diagnostic
# ---------------------------------------------------------------------------


def test_h9_different_topics_are_not_automatically_treated_as_conflict():
    approval = _approval(
        "APPROVAL",
        topic="finance",
    )

    followup = _followup(
        "FOLLOWUP",
        topic="customer_contact",
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            approval,
            followup,
        )
    )

    assert composed is not None

    assert composed.semantics.confirms_approval is True
    assert composed.semantics.requests_followup is True

    # The current implementation does not claim a common topic when
    # component topics disagree.
    assert composed.semantics.topic is None


# ---------------------------------------------------------------------------
# H9 temporal conflict diagnostic
# ---------------------------------------------------------------------------


def test_h9_timestamp_order_does_not_automatically_resolve_conflict():
    older_acceptance = _acceptance(
        "OLDER-ACCEPTANCE",
        occurred_at=EVALUATION_AT - timedelta(days=5),
    )

    newer_rejection = _rejection(
        "NEWER-REJECTION",
        occurred_at=EVALUATION_AT - timedelta(days=1),
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            older_acceptance,
            newer_rejection,
        )
    )

    # This is deliberately diagnostic rather than a production invariant.
    # H9 does not authorize timestamp-based conflict resolution.
    assert composed is None


def test_h9_same_time_conflict_is_refused():
    acceptance = _acceptance(
        "ACCEPTANCE",
        occurred_at=EVALUATION_AT - timedelta(days=1),
    )

    rejection = _rejection(
        "REJECTION",
        occurred_at=EVALUATION_AT - timedelta(days=1),
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            acceptance,
            rejection,
        )
    )

    assert composed is None


# ---------------------------------------------------------------------------
# H9 three-record compatibility
# ---------------------------------------------------------------------------


def test_h9_three_record_split_matches_single_record_control():
    primary = PrimaryState("quote_pending_decision")

    split = _reasoner().evaluate(
        primary,
        _condition(
            _approval("A"),
            _acceptance("B"),
            _followup("C"),
        ),
    )

    control = _reasoner().evaluate(
        primary,
        _condition(
            _combined(
                "CONTROL",
                confirms_approval=True,
                expresses_acceptance=True,
                requests_followup=True,
            ),
        ),
    )

    assert _decision(split) == _decision(control)


# ---------------------------------------------------------------------------
# H9 explicit compatibility-limit diagnostics
# ---------------------------------------------------------------------------


def test_h9_multiple_positive_assertions_of_same_field_are_idempotent():
    approval_a = _approval("A")
    approval_b = _approval("B")

    composed = _reasoner()._compose_cross_record_evidence(
        (
            approval_a,
            approval_b,
        )
    )

    assert composed is not None
    assert composed.semantics.confirms_approval is True


def test_h9_repeated_same_fact_does_not_create_a_new_fact():
    primary = PrimaryState("quote_pending_decision")

    single = _reasoner().evaluate(
        primary,
        _condition(
            _approval("A"),
        ),
    )

    duplicated = _reasoner().evaluate(
        primary,
        _condition(
            _approval("A"),
            _approval("B"),
        ),
    )

    assert _decision(duplicated) == _decision(single)


def test_h9_unrelated_negation_preserves_positive_field():
    approval = _approval("APPROVAL")
    unrelated_negation = _negated(
        "NEGATED-COMPLETION",
        "completion",
    )

    composed = _reasoner()._compose_cross_record_evidence(
        (
            approval,
            unrelated_negation,
        )
    )

    assert composed is not None
    assert composed.semantics.confirms_approval is True
    assert "completion" in composed.semantics.negated_concepts