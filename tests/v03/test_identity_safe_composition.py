from __future__ import annotations

from dataclasses import dataclass

from experiment.v03.evidence import (
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class SafeIdentityComposition:
    customer_id: str | None
    quality: IdentityQuality
    accepted_evidence_ids: tuple[str, ...]
    confirms_completion: bool
    requests_next_step: bool

    @classmethod
    def from_items(
        cls,
        items: tuple[SemanticEvidence, ...],
    ) -> "SafeIdentityComposition":
        confirmed = tuple(
            item
            for item in items
            if item.identity.quality == IdentityQuality.CONFIRMED
        )

        customer_ids = {
            item.identity.customer_id
            for item in confirmed
            if item.identity.customer_id is not None
        }

        if len(customer_ids) > 1:
            return cls(
                customer_id=None,
                quality=IdentityQuality.AMBIGUOUS,
                accepted_evidence_ids=(),
                confirms_completion=False,
                requests_next_step=False,
            )

        customer_id = (
            next(iter(customer_ids))
            if len(customer_ids) == 1
            else None
        )

        if customer_id is None:
            return cls(
                customer_id=None,
                quality=IdentityQuality.AMBIGUOUS,
                accepted_evidence_ids=(),
                confirms_completion=False,
                requests_next_step=False,
            )

        accepted = tuple(
            item
            for item in confirmed
            if item.identity.customer_id == customer_id
        )

        return cls(
            customer_id=customer_id,
            quality=IdentityQuality.CONFIRMED,
            accepted_evidence_ids=tuple(
                item.evidence_id
                for item in accepted
            ),
            confirms_completion=any(
                item.semantics.confirms_completion is True
                and "completion"
                not in item.semantics.negated_concepts
                for item in accepted
            ),
            requests_next_step=any(
                item.semantics.requests_next_step is True
                and "next_step"
                not in item.semantics.negated_concepts
                for item in accepted
            ),
        )


def _extract(
    evidence_id: str,
    customer_id: str | None,
    identity_quality: IdentityQuality,
    text: str,
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


def test_same_customer_confirmed_records_can_compose():
    completion = _extract(
        "COMPLETION",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "C001",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert composed.customer_id == "C001"
    assert composed.quality == IdentityQuality.CONFIRMED

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True


def test_same_customer_contributors_remain_traceable():
    first = _extract(
        "FIRST",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "C001",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            first,
            second,
        ),
    )

    assert composed.accepted_evidence_ids == (
        "FIRST",
        "SECOND",
    )


def test_different_confirmed_customers_cannot_compose():
    customer_a = _extract(
        "CUSTOMER-A",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    customer_b = _extract(
        "CUSTOMER-B",
        "C002",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            customer_a,
            customer_b,
        ),
    )

    assert composed.customer_id is None
    assert composed.quality == IdentityQuality.AMBIGUOUS

    assert composed.accepted_evidence_ids == ()

    assert composed.confirms_completion is False
    assert composed.requests_next_step is False


def test_different_customers_do_not_cross_combine_facts():
    customer_a = _extract(
        "A-COMPLETION",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    customer_b = _extract(
        "B-NEXT-STEP",
        "C002",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            customer_a,
            customer_b,
        ),
    )

    assert composed.confirms_completion is False
    assert composed.requests_next_step is False


def test_wrong_identity_does_not_contribute_to_same_customer():
    valid_completion = _extract(
        "VALID-COMPLETION",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    wrong_identity_next = _extract(
        "WRONG-NEXT",
        "C999",
        IdentityQuality.NO_MATCH,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            valid_completion,
            wrong_identity_next,
        ),
    )

    assert composed.customer_id == "C001"
    assert composed.quality == IdentityQuality.CONFIRMED

    assert composed.accepted_evidence_ids == (
        "VALID-COMPLETION",
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False


def test_ambiguous_identity_does_not_contribute_to_composition():
    valid_completion = _extract(
        "VALID-COMPLETION",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    ambiguous_next = _extract(
        "AMBIGUOUS-NEXT",
        "C001",
        IdentityQuality.AMBIGUOUS,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            valid_completion,
            ambiguous_next,
        ),
    )

    assert composed.customer_id == "C001"
    assert composed.quality == IdentityQuality.CONFIRMED

    assert composed.accepted_evidence_ids == (
        "VALID-COMPLETION",
    )

    assert composed.requests_next_step is False


def test_no_match_record_cannot_override_confirmed_identity():
    valid = _extract(
        "VALID",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    invalid = _extract(
        "INVALID",
        "C999",
        IdentityQuality.NO_MATCH,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            valid,
            invalid,
        ),
    )

    assert composed.customer_id == "C001"
    assert composed.quality == IdentityQuality.CONFIRMED


def test_identity_conflict_is_not_resolved_by_first_record():
    first = _extract(
        "FIRST",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "C002",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            first,
            second,
        ),
    )

    assert composed.customer_id is None
    assert composed.quality == IdentityQuality.AMBIGUOUS


def test_identity_conflict_is_not_resolved_by_last_record():
    first = _extract(
        "FIRST",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "C002",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            first,
            second,
        ),
    )

    assert composed.customer_id != "C002"


def test_identity_conflict_is_symmetric_to_input_order():
    first = _extract(
        "FIRST",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "C002",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    forward = SafeIdentityComposition.from_items(
        (
            first,
            second,
        ),
    )

    reverse = SafeIdentityComposition.from_items(
        (
            second,
            first,
        ),
    )

    assert forward.customer_id == reverse.customer_id
    assert forward.quality == reverse.quality
    assert forward.accepted_evidence_ids == (
        reverse.accepted_evidence_ids
    )


def test_three_same_customer_records_can_compose():
    first = _extract(
        "FIRST",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "C001",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    third = _extract(
        "THIRD",
        "C001",
        IdentityQuality.CONFIRMED,
        "The customer wants another discussion about the proposal.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            first,
            second,
            third,
        ),
    )

    assert composed.customer_id == "C001"
    assert composed.quality == IdentityQuality.CONFIRMED

    assert set(composed.accepted_evidence_ids) == {
        "FIRST",
        "SECOND",
        "THIRD",
    }


def test_three_customer_identity_conflict_remains_ambiguous():
    first = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    second = _extract(
        "B",
        "C002",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    third = _extract(
        "C",
        "C003",
        IdentityQuality.CONFIRMED,
        "The customer wants another discussion about the proposal.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            first,
            second,
            third,
        ),
    )

    assert composed.customer_id is None
    assert composed.quality == IdentityQuality.AMBIGUOUS
    assert composed.accepted_evidence_ids == ()


def test_negated_fact_from_same_customer_does_not_create_positive_fact():
    completion = _extract(
        "COMPLETION",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is not complete.",
    )

    next_step = _extract(
        "NEXT",
        "C001",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert composed.customer_id == "C001"
    assert composed.quality == IdentityQuality.CONFIRMED

    assert composed.confirms_completion is False
    assert composed.requests_next_step is True


def test_wrong_identity_cannot_create_cross_customer_joint_signal():
    valid_completion = _extract(
        "VALID-COMPLETION",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    wrong_identity_next = _extract(
        "WRONG-NEXT",
        "C002",
        IdentityQuality.NO_MATCH,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            valid_completion,
            wrong_identity_next,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False


def test_ambiguous_identity_cannot_create_cross_customer_joint_signal():
    valid_completion = _extract(
        "VALID-COMPLETION",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    ambiguous_next = _extract(
        "AMBIGUOUS-NEXT",
        "C002",
        IdentityQuality.AMBIGUOUS,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            valid_completion,
            ambiguous_next,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False


def test_composition_does_not_infer_identity_from_semantics():
    evidence = _extract(
        "EVIDENCE",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete and the customer "
        "asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (evidence,),
    )

    assert composed.customer_id == "C001"
    assert composed.quality == IdentityQuality.CONFIRMED


def test_composition_identity_is_deterministic():
    first = _extract(
        "FIRST",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "C001",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    first_result = SafeIdentityComposition.from_items(
        (
            first,
            second,
        ),
    )

    second_result = SafeIdentityComposition.from_items(
        (
            first,
            second,
        ),
    )

    assert first_result == second_result


def test_composition_identity_does_not_mutate_source_identity():
    evidence = _extract(
        "EVIDENCE",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    original_identity = evidence.identity

    composed = SafeIdentityComposition.from_items(
        (evidence,),
    )

    assert composed.customer_id == "C001"
    assert evidence.identity == original_identity


def test_composition_identity_does_not_mutate_source_semantics():
    evidence = _extract(
        "EVIDENCE",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    original_semantics = evidence.semantics

    composed = SafeIdentityComposition.from_items(
        (evidence,),
    )

    assert composed.confirms_completion is True
    assert evidence.semantics == original_semantics


def test_composition_identity_has_no_winner_or_priority_policy():
    first = _extract(
        "FIRST",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "C002",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            first,
            second,
        ),
    )

    assert not hasattr(composed, "winner")
    assert not hasattr(composed, "priority")
    assert not hasattr(composed, "source_priority")
    assert not hasattr(composed, "recency_priority")


def test_composition_identity_is_separate_from_source_system():
    evidence = _extract(
        "CRM",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    composed = SafeIdentityComposition.from_items(
        (evidence,),
    )

    assert composed.customer_id == "C001"
    assert evidence.provenance.source_system == "secondary"
    assert composed.customer_id != evidence.provenance.source_system


def test_composition_identity_is_separate_from_record_id():
    evidence = _extract(
        "C001",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    composed = SafeIdentityComposition.from_items(
        (evidence,),
    )

    assert composed.customer_id == "C001"
    assert composed.accepted_evidence_ids == ("C001",)


def test_composed_identity_does_not_depend_on_input_order_for_customer():
    first = _extract(
        "FIRST",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "C001",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    forward = SafeIdentityComposition.from_items(
        (
            first,
            second,
        ),
    )

    reverse = SafeIdentityComposition.from_items(
        (
            second,
            first,
        ),
    )

    assert forward.customer_id == "C001"
    assert reverse.customer_id == "C001"
    assert forward.quality == reverse.quality


def test_composed_identity_is_only_confirmed_from_confirmed_contributors():
    ambiguous = _extract(
        "AMBIGUOUS",
        "C001",
        IdentityQuality.AMBIGUOUS,
        "The migration workshop is complete.",
    )

    no_match = _extract(
        "NO-MATCH",
        "C001",
        IdentityQuality.NO_MATCH,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            ambiguous,
            no_match,
        ),
    )

    assert composed.customer_id is None
    assert composed.quality == IdentityQuality.AMBIGUOUS
    assert composed.accepted_evidence_ids == ()


def test_identity_conflict_has_no_positive_composition_even_when_facts_are_valid():
    first = _extract(
        "CUSTOMER-A-COMPLETION",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    second = _extract(
        "CUSTOMER-B-NEXT",
        "C002",
        IdentityQuality.CONFIRMED,
        "The customer asks what comes next.",
    )

    composed = SafeIdentityComposition.from_items(
        (
            first,
            second,
        ),
    )

    assert composed.customer_id is None
    assert composed.quality == IdentityQuality.AMBIGUOUS

    assert composed.confirms_completion is False
    assert composed.requests_next_step is False


def test_identity_safe_composition_remains_benchmark_independent():
    evidence = _extract(
        "EVIDENCE",
        "C001",
        IdentityQuality.CONFIRMED,
        "The migration workshop is complete.",
    )

    composed = SafeIdentityComposition.from_items(
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