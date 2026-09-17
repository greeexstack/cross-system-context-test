from __future__ import annotations

from dataclasses import dataclass

from experiment.v03.evidence import IdentityQuality, SemanticEvidence
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class DuplicateConflict:
    evidence_id: str
    conflicting: bool
    evidence_ids: tuple[str, ...]
    semantic_signatures: tuple[tuple, ...]


def _extract(
    evidence_id: str,
    text: str,
    *,
    source_system: str = "secondary",
    customer_id: str = "C001",
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    occurred_at: str = "2026-09-12T10:00:00Z",
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system=source_system,
        record_id=evidence_id,
        occurred_at=occurred_at,
        customer_id=customer_id,
        identity_quality=identity_quality,
    ).evidence


def _signature(item: SemanticEvidence) -> tuple:
    semantics = item.semantics

    return (
        semantics.confirms_completion,
        semantics.requests_next_step,
        semantics.requests_followup,
        semantics.confirms_approval,
        semantics.expresses_acceptance,
        semantics.expresses_rejection,
        semantics.negated_concepts,
        semantics.concerns_same_work_item,
    )


def _detect_duplicate_conflict(
    items: tuple[SemanticEvidence, ...],
) -> tuple[DuplicateConflict, ...]:
    by_id: dict[str, list[SemanticEvidence]] = {}

    for item in items:
        by_id.setdefault(
            item.evidence_id,
            [],
        ).append(item)

    conflicts: list[DuplicateConflict] = []

    for evidence_id, records in by_id.items():
        signatures = tuple(
            _signature(record)
            for record in records
        )

        unique_signatures = tuple(
            dict.fromkeys(signatures)
        )

        conflicts.append(
            DuplicateConflict(
                evidence_id=evidence_id,
                conflicting=len(unique_signatures) > 1,
                evidence_ids=tuple(
                    record.evidence_id
                    for record in records
                ),
                semantic_signatures=unique_signatures,
            )
        )

    return tuple(conflicts)


def test_same_id_same_payload_is_not_a_conflict():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
        source_system="crm",
    )

    second = _extract(
        "E1",
        "The migration workshop is complete.",
        source_system="crm",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert result == (
        DuplicateConflict(
            evidence_id="E1",
            conflicting=False,
            evidence_ids=("E1", "E1"),
            semantic_signatures=(
                _signature(first),
            ),
        ),
    )


def test_same_id_different_semantics_is_a_conflict():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
        source_system="crm",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
        source_system="email",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert result[0].evidence_id == "E1"
    assert result[0].conflicting is True
    assert len(result[0].semantic_signatures) == 2


def test_same_id_positive_and_negative_payload_is_a_conflict():
    positive = _extract(
        "E1",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "E1",
        "The customer does not want another discussion about the proposal.",
    )

    result = _detect_duplicate_conflict(
        (
            positive,
            negative,
        ),
    )

    assert result[0].conflicting is True


def test_same_id_different_source_system_is_not_alone_a_semantic_conflict():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
        source_system="crm",
    )

    second = _extract(
        "E1",
        "The migration workshop is complete.",
        source_system="email",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert result[0].conflicting is False


def test_same_id_different_customer_is_an_identity_conflict():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
        customer_id="C001",
    )

    second = _extract(
        "E1",
        "The migration workshop is complete.",
        customer_id="C002",
    )

    assert first.identity.customer_id == "C001"
    assert second.identity.customer_id == "C002"

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert result[0].conflicting is False

    # The semantic payload is the same, but the identity metadata conflicts.
    assert first.identity != second.identity


def test_same_id_different_event_time_is_not_semantic_conflict():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
        occurred_at="2026-09-10T10:00:00Z",
    )

    second = _extract(
        "E1",
        "The migration workshop is complete.",
        occurred_at="2026-09-12T10:00:00Z",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert result[0].conflicting is False
    assert first.timestamp != second.timestamp


def test_duplicate_conflict_does_not_choose_first_payload():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert result[0].conflicting is True
    assert len(result[0].semantic_signatures) == 2


def test_duplicate_conflict_does_not_choose_last_payload():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert result[0].conflicting is True


def test_reversing_conflicting_duplicates_preserves_conflict_status():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    forward = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    reverse = _detect_duplicate_conflict(
        (
            second,
            first,
        ),
    )

    assert forward[0].conflicting is True
    assert reverse[0].conflicting is True

    assert set(forward[0].semantic_signatures) == set(
        reverse[0].semantic_signatures
    )


def test_duplicate_conflict_is_deterministic():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    result_a = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    result_b = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert result_a == result_b


def test_identical_duplicate_records_keep_one_semantic_signature():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert result[0].conflicting is False
    assert len(result[0].semantic_signatures) == 1


def test_three_duplicates_with_two_semantic_payloads_are_conflicted():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    third = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
            third,
        ),
    )

    assert result[0].conflicting is True
    assert len(result[0].semantic_signatures) == 2


def test_three_identical_duplicates_are_not_conflicted():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    third = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
            third,
        ),
    )

    assert result[0].conflicting is False
    assert len(result[0].semantic_signatures) == 1


def test_duplicate_conflict_keeps_record_id_traceability():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert result[0].evidence_ids == (
        "E1",
        "E1",
    )


def test_duplicate_conflict_does_not_modify_source_evidence():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    first_semantics = first.semantics
    second_semantics = second.semantics

    first_provenance = first.provenance
    second_provenance = second.provenance

    _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert first.semantics == first_semantics
    assert second.semantics == second_semantics

    assert first.provenance == first_provenance
    assert second.provenance == second_provenance


def test_invalid_identity_does_not_hide_a_duplicate_semantic_conflict():
    valid = _extract(
        "E1",
        "The migration workshop is complete.",
        identity_quality=IdentityQuality.CONFIRMED,
    )

    invalid = _extract(
        "E1",
        "The customer asks what comes next.",
        identity_quality=IdentityQuality.NO_MATCH,
        customer_id="C999",
    )

    result = _detect_duplicate_conflict(
        (
            valid,
            invalid,
        ),
    )

    # Conflict detection operates before downstream eligibility decisions.
    assert result[0].conflicting is True


def test_duplicate_conflict_has_no_source_priority_rule():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
        source_system="crm",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
        source_system="email",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert not hasattr(
        result[0],
        "source_priority",
    )

    assert not hasattr(
        result[0],
        "winner",
    )

    assert not hasattr(
        result[0],
        "recency_priority",
    )


def test_duplicate_conflict_has_no_benchmark_policy():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert not hasattr(
        result[0],
        "expected_direction",
    )

    assert not hasattr(
        result[0],
        "benchmark_family",
    )


def test_multiple_distinct_ids_produce_independent_duplicate_results():
    first_a = _extract(
        "A",
        "The migration workshop is complete.",
    )

    second_a = _extract(
        "A",
        "The migration workshop is complete.",
    )

    first_b = _extract(
        "B",
        "The customer asks what comes next.",
    )

    second_b = _extract(
        "B",
        "The customer asks what comes next.",
    )

    results = _detect_duplicate_conflict(
        (
            first_a,
            second_a,
            first_b,
            second_b,
        ),
    )

    assert len(results) == 2

    by_id = {
        result.evidence_id: result
        for result in results
    }

    assert by_id["A"].conflicting is False
    assert by_id["B"].conflicting is False


def test_empty_input_has_no_duplicate_conflicts():
    assert _detect_duplicate_conflict(()) == ()


def test_single_record_has_no_duplicate_conflict():
    evidence = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    result = _detect_duplicate_conflict(
        (evidence,),
    )

    assert result[0].conflicting is False


def test_duplicate_conflict_is_about_payload_difference_not_text_difference_alone():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    assert first.semantics == second.semantics

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert result[0].conflicting is False


def test_duplicate_conflict_representation_is_not_a_reasoning_result():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    result = _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert not hasattr(
        result[0],
        "interpretation_class",
    )

    assert not hasattr(
        result[0],
        "decision_strength",
    )


def test_duplicate_conflict_does_not_mutate_identity():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
        customer_id="C001",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
        customer_id="C001",
    )

    first_identity = first.identity
    second_identity = second.identity

    _detect_duplicate_conflict(
        (
            first,
            second,
        ),
    )

    assert first.identity == first_identity
    assert second.identity == second_identity