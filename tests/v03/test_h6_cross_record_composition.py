from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

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


@dataclass(frozen=True)
class H6Composition:
    """
    Test-layer counterfactual composition.

    This is deliberately not production code.

    It preserves:
      - the composed factual semantics
      - source evidence boundaries
      - source provenance
      - detected semantic conflicts
    """

    semantics: EvidenceSemantics
    source_evidence_ids: tuple[str, ...]
    source_provenance: tuple[EvidenceProvenance, ...]
    conflicts: tuple[str, ...] = ()


def _evidence(
    *,
    evidence_id: str,
    semantics: EvidenceSemantics,
    customer_id: str = "C001",
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    occurred_at: datetime | None = None,
) -> SemanticEvidence:
    timestamp = (
        occurred_at
        if occurred_at is not None
        else EVALUATION_AT - timedelta(days=1)
    )

    return SemanticEvidence(
        evidence_id=evidence_id,
        content=evidence_id,
        provenance=EvidenceProvenance(
            source_system="secondary",
            record_id=evidence_id,
            occurred_at=timestamp,
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
        evidence_id=evidence_id,
        semantics=EvidenceSemantics(
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
        evidence_id=evidence_id,
        semantics=EvidenceSemantics(
            topic="migration",
            requests_next_step=True,
            concerns_same_work_item=True,
        ),
        **kwargs,
    )


def _combined() -> SemanticEvidence:
    return _evidence(
        evidence_id="COMBINED",
        semantics=EvidenceSemantics(
            topic="migration",
            confirms_completion=True,
            requests_next_step=True,
            concerns_same_work_item=True,
        ),
    )


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _decision(result) -> tuple[str, str | None]:
    return (
        result.support_level,
        result.recommended_focus,
    )


def _eligible(
    items: tuple[SemanticEvidence, ...],
) -> tuple[SemanticEvidence, ...]:
    eligible: list[SemanticEvidence] = []

    for item in items:
        if item.identity.quality != IdentityQuality.CONFIRMED:
            continue

        occurred_at = item.provenance.occurred_at
        if occurred_at is None:
            continue

        age = EVALUATION_AT - occurred_at
        if age > timedelta(days=30):
            continue

        if item.semantics.concerns_same_work_item is False:
            continue

        eligible.append(item)

    return tuple(eligible)


def _compose_compatible(
    items: tuple[SemanticEvidence, ...],
) -> H6Composition:
    """
    Development-only counterfactual.

    Positive factual assertions are combined only after eligibility
    filtering. Negative assertions are not silently converted into
    positive assertions; conflicts are recorded explicitly.
    """

    eligible = _eligible(items)

    negated = {
        concept
        for item in eligible
        for concept in item.semantics.negated_concepts
    }

    confirms_completion = any(
        item.semantics.confirms_completion is True
        for item in eligible
    )

    requests_next_step = any(
        item.semantics.requests_next_step is True
        for item in eligible
    )

    conflicts: list[str] = []

    if confirms_completion and "completion" in negated:
        conflicts.append("completion")

    if requests_next_step and "next_step" in negated:
        conflicts.append("next_step")

    semantics = EvidenceSemantics(
        topic="migration",
        confirms_completion=(
            True
            if confirms_completion and "completion" not in negated
            else None
        ),
        requests_next_step=(
            True
            if requests_next_step and "next_step" not in negated
            else None
        ),
        concerns_same_work_item=(
            True
            if eligible
            else None
        ),
    )

    return H6Composition(
        semantics=semantics,
        source_evidence_ids=tuple(
            item.evidence_id
            for item in eligible
        ),
        source_provenance=tuple(
            item.provenance
            for item in eligible
        ),
        conflicts=tuple(conflicts),
    )


def test_h6_positive_fixture_has_a_single_record_control():
    completion = _completion()
    next_step = _next_step()
    combined = _combined()

    assert completion.semantics.confirms_completion is True
    assert completion.semantics.requests_next_step is None

    assert next_step.semantics.confirms_completion is None
    assert next_step.semantics.requests_next_step is True

    assert combined.semantics.confirms_completion is True
    assert combined.semantics.requests_next_step is True


def test_h6_counterfactual_composition_matches_control_semantics():
    completion = _completion()
    next_step = _next_step()
    combined = _combined()

    composed = _compose_compatible(
        (
            completion,
            next_step,
        )
    )

    assert composed.semantics.confirms_completion == (
        combined.semantics.confirms_completion
    )

    assert composed.semantics.requests_next_step == (
        combined.semantics.requests_next_step
    )


def test_h6_composition_preserves_source_boundaries_and_provenance():
    completion = _completion()
    next_step = _next_step()

    composed = _compose_compatible(
        (
            completion,
            next_step,
        )
    )

    assert composed.source_evidence_ids == (
        "COMPLETION",
        "NEXT-STEP",
    )

    assert tuple(
        provenance.record_id
        for provenance in composed.source_provenance
    ) == (
        "COMPLETION",
        "NEXT-STEP",
    )

    assert len(composed.source_evidence_ids) == 2
    assert len(composed.source_provenance) == 2


@pytest.mark.parametrize(
    "invalid_item",
    [
        _next_step(
            evidence_id="WRONG-IDENTITY",
            customer_id="C999",
            identity_quality=IdentityQuality.NO_MATCH,
        ),
        _next_step(
            evidence_id="AMBIGUOUS",
            identity_quality=IdentityQuality.AMBIGUOUS,
        ),
        _next_step(
            evidence_id="STALE",
            occurred_at=EVALUATION_AT - timedelta(days=31),
        ),
        _evidence(
            evidence_id="WRONG-WORK-ITEM",
            semantics=EvidenceSemantics(
                topic="migration",
                requests_next_step=True,
                concerns_same_work_item=False,
            ),
        ),
    ],
)
def test_h6_invalid_negative_controls_are_excluded(invalid_item):
    completion = _completion()

    eligible = _eligible(
        (
            completion,
            invalid_item,
        )
    )

    assert tuple(
        item.evidence_id
        for item in eligible
    ) == ("COMPLETION",)


def test_h6_counterfactual_composition_excludes_invalid_next_step():
    completion = _completion()

    invalid_next_step = _next_step(
        evidence_id="WRONG-IDENTITY",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    composed = _compose_compatible(
        (
            completion,
            invalid_next_step,
        )
    )

    assert composed.semantics.confirms_completion is True
    assert composed.semantics.requests_next_step is None
    assert composed.source_evidence_ids == ("COMPLETION",)


def test_h6_conflicting_fixture_is_explicitly_detectable():
    positive = _completion()

    negative = _evidence(
        evidence_id="NEGATED-COMPLETION",
        semantics=EvidenceSemantics(
            topic="migration",
            polarity=AssertionPolarity.NEGATIVE,
            negated_concepts=("completion",),
            concerns_same_work_item=True,
        ),
    )

    composed = _compose_compatible(
        (
            positive,
            negative,
        )
    )

    assert "completion" in composed.conflicts

    assert composed.source_evidence_ids == (
        "COMPLETION",
        "NEGATED-COMPLETION",
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "H6 is not implemented in the production reasoner: "
        "split compatible facts currently do not reproduce the "
        "single-record joint decision."
    ),
)
def test_h6_production_reasoner_split_matches_single_record_control():
    completion = _completion()
    next_step = _next_step()
    combined = _combined()

    split_result = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=(completion, next_step),
        ),
    )

    control_result = _reasoner().evaluate(
        STATE,
        EvidenceCondition(
            availability="available",
            items=(combined,),
        ),
    )

    assert _decision(split_result) == _decision(control_result)