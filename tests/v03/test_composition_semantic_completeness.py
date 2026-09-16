from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, timezone

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class CompleteComposition:
    confirms_completion: bool | None
    requests_next_step: bool | None
    requests_followup: bool | None
    confirms_approval: bool | None
    expresses_acceptance: bool | None
    expresses_rejection: bool | None
    negated_concepts: tuple[str, ...]
    concerns_same_work_item: bool | None

    @classmethod
    def from_items(
        cls,
        items: tuple[SemanticEvidence, ...],
    ) -> "CompleteComposition":
        eligible = tuple(
            item
            for item in items
            if item.identity.quality == IdentityQuality.CONFIRMED
            and item.timestamp is not None
            and _is_fresh(item)
            and item.semantics.concerns_same_work_item is not False
        )

        def _any_true(attribute: str) -> bool | None:
            matching = tuple(
                getattr(item.semantics, attribute)
                for item in eligible
            )

            if not matching:
                return None

            if any(value is True for value in matching):
                return True

            return None

        negated = tuple(
            sorted(
                {
                    concept
                    for item in eligible
                    for concept in item.semantics.negated_concepts
                }
            )
        )

        same_work_item_values = tuple(
            item.semantics.concerns_same_work_item
            for item in eligible
            if item.semantics.concerns_same_work_item is not None
        )

        if any(value is False for value in same_work_item_values):
            concerns_same_work_item: bool | None = False
        elif any(value is True for value in same_work_item_values):
            concerns_same_work_item = True
        else:
            concerns_same_work_item = None

        return cls(
            confirms_completion=_any_true("confirms_completion"),
            requests_next_step=_any_true("requests_next_step"),
            requests_followup=_any_true("requests_followup"),
            confirms_approval=_any_true("confirms_approval"),
            expresses_acceptance=_any_true("expresses_acceptance"),
            expresses_rejection=_any_true("expresses_rejection"),
            negated_concepts=negated,
            concerns_same_work_item=concerns_same_work_item,
        )


def _is_fresh(item: SemanticEvidence) -> bool:
    if item.timestamp is None:
        return False

    timestamp = item.timestamp

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return (
        EVALUATION_AT - timestamp
        <= timedelta(days=30)
    )


def _extract(
    evidence_id: str,
    text: str,
    *,
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    customer_id: str = "C001",
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system="secondary",
        record_id=evidence_id,
        occurred_at="2026-09-12T10:00:00Z",
        customer_id=customer_id,
        identity_quality=identity_quality,
    ).evidence


def test_empty_composition_does_not_invent_boolean_facts():
    composed = CompleteComposition.from_items(())

    assert composed.confirms_completion is None
    assert composed.requests_next_step is None
    assert composed.requests_followup is None
    assert composed.confirms_approval is None
    assert composed.expresses_acceptance is None
    assert composed.expresses_rejection is None
    assert composed.negated_concepts == ()
    assert composed.concerns_same_work_item is None


def test_completion_is_preserved():
    evidence = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    composed = CompleteComposition.from_items(
        (evidence,),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is None
    assert composed.requests_followup is None


def test_next_step_is_preserved():
    evidence = _extract(
        "NEXT",
        "The customer asks what comes next.",
    )

    composed = CompleteComposition.from_items(
        (evidence,),
    )

    assert composed.requests_next_step is True
    assert composed.confirms_completion is None


def test_followup_is_preserved():
    evidence = _extract(
        "FOLLOWUP",
        "The customer wants another discussion about the proposal.",
    )

    composed = CompleteComposition.from_items(
        (evidence,),
    )

    assert composed.requests_followup is True


def test_approval_is_preserved():
    evidence = _extract(
        "APPROVAL",
        "The quoted amount has budget approval.",
    )

    composed = CompleteComposition.from_items(
        (evidence,),
    )

    assert composed.confirms_approval is True


def test_acceptance_is_preserved():
    evidence = _extract(
        "ACCEPTANCE",
        "The customer accepted the revised commercial terms.",
    )

    composed = CompleteComposition.from_items(
        (evidence,),
    )

    assert composed.expresses_acceptance is True


def test_rejection_is_preserved():
    evidence = _extract(
        "REJECTION",
        "The customer rejected the revised commercial terms.",
    )

    composed = CompleteComposition.from_items(
        (evidence,),
    )

    assert composed.expresses_rejection is True


def test_negated_concepts_are_preserved():
    evidence = _extract(
        "NEGATED",
        "The migration workshop is not complete.",
    )

    composed = CompleteComposition.from_items(
        (evidence,),
    )

    assert "completion" in composed.negated_concepts
    assert composed.confirms_completion is None


def test_same_work_item_flag_is_preserved():
    evidence = _extract(
        "EVIDENCE",
        "The migration workshop is complete.",
    )

    composed = CompleteComposition.from_items(
        (evidence,),
    )

    assert composed.concerns_same_work_item is None

def test_distinct_semantic_dimensions_can_coexist():
    evidence = _extract(
        "MULTI",
        "The migration workshop is complete and the customer "
        "asks what comes next.",
    )

    composed = CompleteComposition.from_items(
        (evidence,),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True


def test_two_different_records_can_supply_different_dimensions():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT",
        "The customer asks what comes next.",
    )

    composed = CompleteComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True


def test_redundant_same_dimension_does_not_change_value():
    first = _extract(
        "FIRST",
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "The migration workshop is complete.",
    )

    first_only = CompleteComposition.from_items(
        (first,),
    )

    both = CompleteComposition.from_items(
        (
            first,
            second,
        ),
    )

    assert both.confirms_completion == first_only.confirms_completion
    assert both.negated_concepts == first_only.negated_concepts


def test_negative_semantics_are_not_converted_to_positive():
    evidence = _extract(
        "NEGATED",
        "The customer does not want another discussion "
        "about the proposal.",
    )

    composed = CompleteComposition.from_items(
        (evidence,),
    )

    assert composed.requests_followup is None
    assert "followup" in composed.negated_concepts


def test_positive_and_negative_semantics_can_coexist_across_records():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
    )

    composed = CompleteComposition.from_items(
        (
            positive,
            negative,
        ),
    )

    assert composed.requests_followup is True
    assert "followup" in composed.negated_concepts


def test_wrong_identity_does_not_contribute_any_semantic_dimension():
    valid = _extract(
        "VALID",
        "The migration workshop is complete.",
    )

    wrong = _extract(
        "WRONG",
        "The customer asks what comes next.",
        identity_quality=IdentityQuality.NO_MATCH,
        customer_id="C999",
    )

    composed = CompleteComposition.from_items(
        (
            valid,
            wrong,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is None


def test_stale_evidence_does_not_contribute_any_semantic_dimension():
    fresh = _extract(
        "FRESH",
        "The migration workshop is complete.",
    )

    stale_extractor = LexicalNormalizationSemanticExtractor()

    stale = stale_extractor.extract(
        evidence_id="STALE",
        content="The customer asks what comes next.",
        source_system="secondary",
        record_id="STALE",
        occurred_at="2026-07-01T10:00:00Z",
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    ).evidence

    composed = CompleteComposition.from_items(
        (
            fresh,
            stale,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is None


def test_irrelevant_evidence_does_not_create_semantic_values():
    valid = _extract(
        "VALID",
        "The migration workshop is complete.",
    )

    irrelevant = _extract(
        "IRRELEVANT",
        "The customer is discussing a separate store rollout "
        "and says nothing about this opportunity.",
    )

    composed = CompleteComposition.from_items(
        (
            valid,
            irrelevant,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is None
    assert composed.requests_followup is None


def test_composition_is_order_independent_for_semantic_values():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT",
        "The customer asks what comes next.",
    )

    forward = CompleteComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    reverse = CompleteComposition.from_items(
        (
            next_step,
            completion,
        ),
    )

    assert forward == reverse


def test_composition_is_deterministic():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT",
        "The customer asks what comes next.",
    )

    first = CompleteComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    second = CompleteComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert first == second


def test_composition_does_not_mutate_source_semantics():
    evidence = _extract(
        "EVIDENCE",
        "The migration workshop is complete and the customer "
        "asks what comes next.",
    )

    before = evidence.semantics

    composed = CompleteComposition.from_items(
        (evidence,),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True
    assert evidence.semantics == before


def test_composition_does_not_invent_unobserved_fields():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    composed = CompleteComposition.from_items(
        (completion,),
    )

    assert composed.confirms_completion is True

    assert composed.requests_next_step is None
    assert composed.requests_followup is None
    assert composed.confirms_approval is None
    assert composed.expresses_acceptance is None
    assert composed.expresses_rejection is None


def test_composition_preserves_semantic_specificity():
    approval = _extract(
        "APPROVAL",
        "The quoted amount has budget approval.",
    )

    composed = CompleteComposition.from_items(
        (approval,),
    )

    assert composed.confirms_approval is True
    assert composed.confirms_completion is None
    assert composed.requests_followup is None
    assert composed.requests_next_step is None


def test_completion_plus_approval_preserves_both_dimensions():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    approval = _extract(
        "APPROVAL",
        "The quoted amount has budget approval.",
    )

    composed = CompleteComposition.from_items(
        (
            completion,
            approval,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.confirms_approval is True

    assert composed.requests_next_step is None
    assert composed.requests_followup is None


def test_completion_plus_followup_preserves_both_dimensions():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    followup = _extract(
        "FOLLOWUP",
        "The customer wants another discussion about the proposal.",
    )

    composed = CompleteComposition.from_items(
        (
            completion,
            followup,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_followup is True

    assert composed.requests_next_step is None


def test_same_work_item_negative_signal_blocks_positive_reconstruction():
    negative = _extract(
        "NEGATIVE",
        "The migration workshop is not complete.",
    )

    next_step = _extract(
        "NEXT",
        "The customer asks what comes next.",
    )

    composed = CompleteComposition.from_items(
        (
            negative,
            next_step,
        ),
    )

    assert composed.confirms_completion is None
    assert composed.requests_next_step is True


def test_semantic_composition_has_no_benchmark_metadata():
    evidence = _extract(
        "EVIDENCE",
        "The migration workshop is complete.",
    )

    composed = CompleteComposition.from_items(
        (evidence,),
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


def test_composition_preserves_semantic_dimensions_without_source_priority():
    first = _extract(
        "FIRST",
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "The customer asks what comes next.",
    )

    composed = CompleteComposition.from_items(
        (
            first,
            second,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True

    assert not hasattr(
        composed,
        "source_priority",
    )

    assert not hasattr(
        composed,
        "recency_priority",
    )


def test_empty_negative_set_is_explicitly_empty():
    evidence = _extract(
        "POSITIVE",
        "The migration workshop is complete.",
    )

    composed = CompleteComposition.from_items(
        (evidence,),
    )

    assert composed.negated_concepts == ()


def test_multiple_negative_concepts_are_sorted_deterministically():
    completion = _extract(
        "NEGATED-COMPLETION",
        "The migration workshop is not complete.",
    )

    followup = _extract(
        "NEGATED-FOLLOWUP",
        "The customer does not want another discussion "
        "about the proposal.",
    )

    composed = CompleteComposition.from_items(
        (
            completion,
            followup,
        ),
    )

    assert composed.negated_concepts == tuple(
        sorted(composed.negated_concepts)
    )


def test_confirmed_identity_is_required_before_semantic_composition():
    ambiguous = _extract(
        "AMBIGUOUS",
        "The migration workshop is complete.",
        identity_quality=IdentityQuality.AMBIGUOUS,
    )

    no_match = _extract(
        "NO-MATCH",
        "The customer asks what comes next.",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    composed = CompleteComposition.from_items(
        (
            ambiguous,
            no_match,
        ),
    )

    assert composed.confirms_completion is None
    assert composed.requests_next_step is None
    assert composed.negated_concepts == ()