from __future__ import annotations

from dataclasses import dataclass

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class ComposedIdempotentResult:
    confirms_completion: bool | None
    requests_next_step: bool | None
    requests_followup: bool | None
    evidence_ids: tuple[str, ...]


def _extract(
    evidence_id: str,
    text: str,
    *,
    source_system: str = "secondary",
    customer_id: str = "C001",
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system=source_system,
        record_id=evidence_id,
        occurred_at="2026-09-12T10:00:00Z",
        customer_id=customer_id,
        identity_quality=identity_quality,
    ).evidence


def _compose(
    items: tuple[SemanticEvidence, ...],
) -> ComposedIdempotentResult:
    eligible = tuple(
        item
        for item in items
        if item.identity.quality == IdentityQuality.CONFIRMED
        and item.timestamp is not None
        and item.semantics.concerns_same_work_item is not False
        and EVALUATION_AT - item.timestamp
        <= __import__("datetime").timedelta(days=30)
    )

    unique_by_id: dict[str, SemanticEvidence] = {}

    for item in eligible:
        unique_by_id.setdefault(
            item.evidence_id,
            item,
        )

    deduplicated = tuple(
        unique_by_id.values(),
    )

    return ComposedIdempotentResult(
        confirms_completion=(
            True
            if any(
                item.semantics.confirms_completion is True
                and "completion"
                not in item.semantics.negated_concepts
                for item in deduplicated
            )
            else None
        ),
        requests_next_step=(
            True
            if any(
                item.semantics.requests_next_step is True
                and "next_step"
                not in item.semantics.negated_concepts
                for item in deduplicated
            )
            else None
        ),
        requests_followup=(
            True
            if any(
                item.semantics.requests_followup is True
                and "followup"
                not in item.semantics.negated_concepts
                for item in deduplicated
            )
            else None
        ),
        evidence_ids=tuple(
            unique_by_id.keys(),
        ),
    )


def test_single_evidence_is_composed_normally():
    evidence = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    result = _compose(
        (evidence,),
    )

    assert result.confirms_completion is True
    assert result.evidence_ids == ("E1",)


def test_duplicate_same_object_is_idempotent():
    evidence = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    first = _compose(
        (evidence,),
    )

    duplicated = _compose(
        (
            evidence,
            evidence,
        ),
    )

    assert duplicated == first


def test_duplicate_same_record_is_not_counted_twice():
    evidence = _extract(
        "E1",
        "The customer wants another discussion about the proposal.",
    )

    result = _compose(
        (
            evidence,
            evidence,
            evidence,
        ),
    )

    assert result.requests_followup is True
    assert result.evidence_ids == ("E1",)


def test_duplicate_same_record_does_not_create_additional_semantic_dimensions():
    evidence = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    result = _compose(
        (
            evidence,
            evidence,
        ),
    )

    assert result.confirms_completion is True
    assert result.requests_next_step is None
    assert result.requests_followup is None


def test_two_distinct_records_with_same_fact_remain_distinct():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
        source_system="crm",
    )

    second = _extract(
        "E2",
        "The migration workshop is complete.",
        source_system="email",
    )

    result = _compose(
        (
            first,
            second,
        ),
    )

    assert result.confirms_completion is True

    assert set(result.evidence_ids) == {
        "E1",
        "E2",
    }


def test_distinct_records_are_not_deduplicated_by_semantic_content():
    first = _extract(
        "CRM-COMPLETE",
        "The migration workshop is complete.",
        source_system="crm",
    )

    second = _extract(
        "EMAIL-COMPLETE",
        "The migration workshop is complete.",
        source_system="email",
    )

    result = _compose(
        (
            first,
            second,
        ),
    )

    assert len(result.evidence_ids) == 2

    assert set(result.evidence_ids) == {
        "CRM-COMPLETE",
        "EMAIL-COMPLETE",
    }


def test_duplicate_record_does_not_turn_unknown_into_positive_fact():
    evidence = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    result = _compose(
        (
            evidence,
            evidence,
        ),
    )

    assert result.requests_next_step is True
    assert result.confirms_completion is None


def test_duplicate_record_does_not_turn_negative_into_positive():
    evidence = _extract(
        "E1",
        "The customer does not want another discussion about the proposal.",
    )

    result = _compose(
        (
            evidence,
            evidence,
        ),
    )

    assert result.requests_followup is None


def test_duplicate_record_preserves_original_identity():
    evidence = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    before = evidence.identity

    _compose(
        (
            evidence,
            evidence,
        ),
    )

    assert evidence.identity == before


def test_duplicate_record_preserves_original_semantics():
    evidence = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    before = evidence.semantics

    _compose(
        (
            evidence,
            evidence,
        ),
    )

    assert evidence.semantics == before


def test_duplicate_record_preserves_original_provenance():
    evidence = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    before = evidence.provenance

    _compose(
        (
            evidence,
            evidence,
        ),
    )

    assert evidence.provenance == before


def test_duplicate_wrong_identity_record_remains_excluded():
    valid = _extract(
        "VALID",
        "The migration workshop is complete.",
    )

    wrong = _extract(
        "WRONG",
        "The customer asks what comes next.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    result = _compose(
        (
            valid,
            wrong,
            wrong,
            wrong,
        ),
    )

    assert result.confirms_completion is True
    assert result.requests_next_step is None

    assert result.evidence_ids == (
        "VALID",
    )


def test_duplicate_stale_record_remains_excluded():
    stale_extractor = LexicalNormalizationSemanticExtractor()

    stale = stale_extractor.extract(
        evidence_id="STALE",
        content="The customer asks what comes next.",
        source_system="legacy",
        record_id="STALE",
        occurred_at="2026-07-01T10:00:00Z",
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    ).evidence

    result = _compose(
        (
            stale,
            stale,
        ),
    )

    assert result.requests_next_step is None
    assert result.evidence_ids == ()


def test_duplicate_irrelevant_record_does_not_create_followup():
    irrelevant = _extract(
        "IRRELEVANT",
        "The customer is discussing a separate store rollout "
        "and says nothing about this opportunity.",
    )

    result = _compose(
        (
            irrelevant,
            irrelevant,
        ),
    )

    assert result.requests_followup is None
    assert result.requests_next_step is None


def test_duplicate_negated_record_preserves_negative_concept():
    evidence = _extract(
        "NEGATED",
        "The migration workshop is not complete.",
    )

    result = _compose(
        (
            evidence,
            evidence,
        ),
    )

    assert result.confirms_completion is None


def test_duplicate_positive_and_negative_records_remain_distinct():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
    )

    result = _compose(
        (
            positive,
            positive,
            negative,
            negative,
        ),
    )

    assert result.requests_followup is True

    assert set(result.evidence_ids) == {
        "POSITIVE",
        "NEGATIVE",
    }


def test_repeating_a_record_does_not_change_composed_result():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT",
        "The customer asks what comes next.",
    )

    baseline = _compose(
        (
            completion,
            next_step,
        ),
    )

    repeated = _compose(
        (
            completion,
            completion,
            next_step,
            next_step,
            completion,
        ),
    )

    assert repeated == baseline


def test_duplicate_input_is_order_independent():
    evidence = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    first = _compose(
        (
            evidence,
            evidence,
        ),
    )

    second = _compose(
        (
            evidence,
            evidence,
        ),
    )

    assert first == second


def test_distinct_records_from_different_sources_remain_auditable():
    crm = _extract(
        "CRM",
        "The migration workshop is complete.",
        source_system="crm",
    )

    email = _extract(
        "EMAIL",
        "The migration workshop is complete.",
        source_system="email",
    )

    result = _compose(
        (
            crm,
            email,
        ),
    )

    assert set(result.evidence_ids) == {
        "CRM",
        "EMAIL",
    }

    assert crm.provenance.source_system == "crm"
    assert email.provenance.source_system == "email"


def test_duplicate_same_id_from_different_python_objects_is_deduplicated():
    first = _extract(
        "SAME-ID",
        "The migration workshop is complete.",
    )

    second = _extract(
        "SAME-ID",
        "The migration workshop is complete.",
    )

    assert first is not second
    assert first.evidence_id == second.evidence_id

    result = _compose(
        (
            first,
            second,
        ),
    )

    assert result.evidence_ids == (
        "SAME-ID",
    )


def test_two_different_ids_are_not_deduplicated_even_with_same_text():
    first = _extract(
        "A",
        "The customer asks what comes next.",
    )

    second = _extract(
        "B",
        "The customer asks what comes next.",
    )

    result = _compose(
        (
            first,
            second,
        ),
    )

    assert result.requests_next_step is True
    assert set(result.evidence_ids) == {
        "A",
        "B",
    }


def test_duplicate_evidence_does_not_create_hidden_source_priority():
    evidence = _extract(
        "CRM",
        "The migration workshop is complete.",
        source_system="crm",
    )

    result = _compose(
        (
            evidence,
            evidence,
            evidence,
        ),
    )

    assert result.evidence_ids == ("CRM",)

    assert not hasattr(
        result,
        "source_priority",
    )

    assert not hasattr(
        result,
        "winner",
    )

    assert not hasattr(
        result,
        "recency_priority",
    )


def test_duplicate_evidence_does_not_create_benchmark_policy():
    evidence = _extract(
        "CRM",
        "The migration workshop is complete.",
    )

    result = _compose(
        (
            evidence,
            evidence,
        ),
    )

    assert not hasattr(
        result,
        "expected_direction",
    )

    assert not hasattr(
        result,
        "benchmark_family",
    )

    assert not hasattr(
        result,
        "winner",
    )


def test_idempotency_is_stable_under_three_repetitions():
    evidence = _extract(
        "E1",
        "The customer wants another discussion about the proposal.",
    )

    once = _compose((evidence,))
    twice = _compose((evidence, evidence))
    thrice = _compose(
        (
            evidence,
            evidence,
            evidence,
        )
    )

    assert once == twice
    assert twice == thrice