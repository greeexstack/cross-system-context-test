from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    EvidenceCondition,
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


@dataclass(frozen=True)
class SafeComposition:
    confirms_completion: bool = False
    requests_next_step: bool = False
    requests_followup: bool = False
    confirms_approval: bool = False
    expresses_acceptance: bool = False
    expresses_rejection: bool = False

    @classmethod
    def from_items(
        cls,
        items: tuple[SemanticEvidence, ...],
    ) -> "SafeComposition":
        eligible = tuple(
            item
            for item in items
            if item.identity.quality == IdentityQuality.CONFIRMED
            and _is_fresh(item)
            and item.semantics.concerns_same_work_item is not False
        )

        return cls(
            confirms_completion=any(
                item.semantics.confirms_completion is True
                and "completion"
                not in item.semantics.negated_concepts
                for item in eligible
            ),
            requests_next_step=any(
                item.semantics.requests_next_step is True
                and "next_step"
                not in item.semantics.negated_concepts
                for item in eligible
            ),
            requests_followup=any(
                item.semantics.requests_followup is True
                and "followup"
                not in item.semantics.negated_concepts
                for item in eligible
            ),
            confirms_approval=any(
                item.semantics.confirms_approval is True
                and "approval"
                not in item.semantics.negated_concepts
                for item in eligible
            ),
            expresses_acceptance=any(
                item.semantics.expresses_acceptance is True
                for item in eligible
            ),
            expresses_rejection=any(
                item.semantics.expresses_rejection is True
                for item in eligible
            ),
        )


def _is_fresh(item: SemanticEvidence) -> bool:
    timestamp = item.timestamp

    if timestamp is None:
        return False

    when = timestamp

    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)

    age = EVALUATION_AT - when

    return age <= timedelta(days=30)


def _extract(
    evidence_id: str,
    text: str,
    *,
    occurred_at: str = "2026-09-12T10:00:00Z",
    customer_id: str | None = "C001",
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system="secondary",
        record_id=evidence_id,
        occurred_at=occurred_at,
        customer_id=customer_id,
        identity_quality=identity_quality,
    ).evidence


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _condition(
    *items: SemanticEvidence,
) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=tuple(items),
    )


def test_safe_composition_accepts_valid_fresh_completion():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    composed = SafeComposition.from_items(
        (completion,),
    )

    assert composed.confirms_completion is True


def test_safe_composition_accepts_valid_fresh_next_step():
    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed = SafeComposition.from_items(
        (next_step,),
    )

    assert composed.requests_next_step is True


def test_safe_composition_combines_valid_cross_record_facts():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed = SafeComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True


def test_wrong_identity_cannot_contribute_to_composition():
    valid_completion = _extract(
        "VALID-COMPLETION",
        "The migration workshop is complete.",
    )

    wrong_identity_next_step = _extract(
        "WRONG-IDENTITY-NEXT-STEP",
        "The customer asks what comes next.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    composed = SafeComposition.from_items(
        (
            valid_completion,
            wrong_identity_next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False


def test_ambiguous_identity_cannot_contribute_to_composition():
    valid_completion = _extract(
        "VALID-COMPLETION",
        "The migration workshop is complete.",
    )

    ambiguous_next_step = _extract(
        "AMBIGUOUS-NEXT-STEP",
        "The customer asks what comes next.",
        identity_quality=IdentityQuality.AMBIGUOUS,
    )

    composed = SafeComposition.from_items(
        (
            valid_completion,
            ambiguous_next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False


def test_stale_evidence_cannot_contribute_to_composition():
    valid_next_step = _extract(
        "VALID-NEXT-STEP",
        "The customer asks what comes next.",
    )

    stale_completion = _extract(
        "STALE-COMPLETION",
        "The migration workshop is complete.",
        occurred_at="2026-07-01T10:00:00Z",
    )

    composed = SafeComposition.from_items(
        (
            stale_completion,
            valid_next_step,
        ),
    )

    assert composed.confirms_completion is False
    assert composed.requests_next_step is True


def test_negated_evidence_cannot_contribute_positive_fact():
    negated_completion = _extract(
        "NEGATED-COMPLETION",
        "The migration workshop is not complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed = SafeComposition.from_items(
        (
            negated_completion,
            next_step,
        ),
    )

    assert composed.confirms_completion is False
    assert composed.requests_next_step is True


def test_relevant_negative_followup_cannot_create_positive_followup():
    negated_followup = _extract(
        "NEGATED-FOLLOWUP",
        "The customer does not want another discussion about the proposal.",
    )

    composed = SafeComposition.from_items(
        (negated_followup,),
    )

    assert composed.requests_followup is False


def test_irrelevant_evidence_cannot_contribute_to_composition():
    relevant_completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    irrelevant = _extract(
        "IRRELEVANT",
        "The customer is discussing a separate store rollout "
        "and says nothing about this opportunity.",
    )

    composed = SafeComposition.from_items(
        (
            relevant_completion,
            irrelevant,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False


def test_mixed_valid_and_invalid_records_do_not_create_false_joint_signal():
    valid_completion = _extract(
        "VALID-COMPLETION",
        "The migration workshop is complete.",
    )

    wrong_identity_next_step = _extract(
        "WRONG-NEXT-STEP",
        "The customer asks what comes next.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    stale_next_step = _extract(
        "STALE-NEXT-STEP",
        "The customer asks what comes next.",
        occurred_at="2026-07-01T10:00:00Z",
    )

    negated_next_step = _extract(
        "NEGATED-NEXT-STEP",
        "The customer does not want to discuss what comes next.",
    )

    composed = SafeComposition.from_items(
        (
            valid_completion,
            wrong_identity_next_step,
            stale_next_step,
            negated_next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False


def test_safe_composition_preserves_individual_evidence():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    before_completion = completion.semantics
    before_next_step = next_step.semantics

    composed = SafeComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True

    assert completion.semantics == before_completion
    assert next_step.semantics == before_next_step


def test_safe_composition_is_order_independent():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    first = SafeComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    second = SafeComposition.from_items(
        (
            next_step,
            completion,
        ),
    )

    assert first == second


def test_safe_composition_does_not_change_current_production_reasoner():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed = SafeComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    production_result = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            completion,
            next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True

    # Production reasoner remains unchanged: separate evidence records
    # still do not activate its same-record joint rule.
    assert production_result.support_level == "primary_only"
    assert production_result.recommended_focus is None