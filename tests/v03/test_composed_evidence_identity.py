from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    EvidenceCondition,
    EvidenceIdentity,
    EvidenceProvenance,
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class CompositionIdentity:
    customer_id: str
    quality: IdentityQuality
    contributor_ids: tuple[str, ...]


@dataclass(frozen=True)
class ComposedEvidenceEnvelope:
    evidence_id: str
    identity: CompositionIdentity
    provenance: tuple[EvidenceProvenance, ...]
    semantics: EvidenceSemantics


def _extract(
    evidence_id: str,
    source_system: str,
    text: str,
    occurred_at: str,
    *,
    customer_id: str = "C001",
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
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


def _compose(
    items: tuple[SemanticEvidence, ...],
) -> ComposedEvidenceEnvelope:
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

    if len(customer_ids) != 1:
        raise ValueError(
            "composition requires exactly one confirmed customer identity"
        )

    customer_id = next(iter(customer_ids))

    provenance = tuple(
        item.provenance
        for item in confirmed
    )

    semantics = EvidenceSemantics(
        confirms_completion=any(
            item.semantics.confirms_completion is True
            for item in confirmed
        ),
        requests_next_step=any(
            item.semantics.requests_next_step is True
            for item in confirmed
        ),
        requests_followup=any(
            item.semantics.requests_followup is True
            for item in confirmed
        ),
        confirms_approval=any(
            item.semantics.confirms_approval is True
            for item in confirmed
        ),
        expresses_acceptance=any(
            item.semantics.expresses_acceptance is True
            for item in confirmed
        ),
        expresses_rejection=any(
            item.semantics.expresses_rejection is True
            for item in confirmed
        ),
        negated_concepts=tuple(
            sorted(
                {
                    concept
                    for item in confirmed
                    for concept in item.semantics.negated_concepts
                }
            )
        ),
        concerns_same_work_item=True,
    )

    return ComposedEvidenceEnvelope(
        evidence_id="COMPOSED:"
        + "+".join(
            item.evidence_id
            for item in confirmed
        ),
        identity=CompositionIdentity(
            customer_id=customer_id,
            quality=IdentityQuality.CONFIRMED,
            contributor_ids=tuple(
                item.evidence_id
                for item in confirmed
            ),
        ),
        provenance=provenance,
        semantics=semantics,
    )


def test_composed_evidence_requires_one_customer_identity():
    crm = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    email = _extract(
        "EMAIL",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T11:00:00Z",
    )

    composed = _compose(
        (
            crm,
            email,
        ),
    )

    assert composed.identity.customer_id == "C001"


def test_composed_identity_is_confirmed_when_all_contributors_are_confirmed():
    first = _extract(
        "FIRST",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    second = _extract(
        "SECOND",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T11:00:00Z",
    )

    composed = _compose(
        (
            first,
            second,
        ),
    )

    assert composed.identity.quality == IdentityQuality.CONFIRMED


def test_composed_identity_retains_all_contributor_ids():
    first = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    second = _extract(
        "EMAIL",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T11:00:00Z",
    )

    composed = _compose(
        (
            first,
            second,
        ),
    )

    assert composed.identity.contributor_ids == (
        "CRM",
        "EMAIL",
    )


def test_composed_evidence_retains_each_source_provenance():
    first = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
        "2026-09-10T10:00:00Z",
    )

    second = _extract(
        "EMAIL",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T10:00:00Z",
    )

    composed = _compose(
        (
            first,
            second,
        ),
    )

    assert composed.provenance == (
        first.provenance,
        second.provenance,
    )


def test_composed_evidence_does_not_replace_event_times_with_one_timestamp():
    first = _extract(
        "EARLY",
        "crm",
        "The migration workshop is complete.",
        "2026-09-10T10:00:00Z",
    )

    second = _extract(
        "LATE",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T10:00:00Z",
    )

    composed = _compose(
        (
            first,
            second,
        ),
    )

    assert composed.provenance[0].occurred_at == first.timestamp
    assert composed.provenance[1].occurred_at == second.timestamp


def test_composed_evidence_has_no_single_synthetic_event_time():
    first = _extract(
        "FIRST",
        "crm",
        "The migration workshop is complete.",
        "2026-09-10T10:00:00Z",
    )

    second = _extract(
        "SECOND",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T10:00:00Z",
    )

    composed = _compose(
        (
            first,
            second,
        ),
    )

    assert not hasattr(
        composed,
        "occurred_at",
    )


def test_mismatched_customer_ids_cannot_be_silently_composed():
    first = _extract(
        "CUSTOMER-A",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
        customer_id="C001",
    )

    second = _extract(
        "CUSTOMER-B",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T11:00:00Z",
        customer_id="C002",
    )

    try:
        _compose(
            (
                first,
                second,
            ),
        )
    except ValueError as exc:
        assert "customer identity" in str(exc)
    else:
        raise AssertionError(
            "mismatched customer IDs were silently composed"
        )


def test_wrong_identity_record_is_not_contributor_identity():
    valid = _extract(
        "VALID",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
        customer_id="C001",
    )

    wrong = _extract(
        "WRONG",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T11:00:00Z",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    composed = _compose(
        (
            valid,
            wrong,
        ),
    )

    assert composed.identity.customer_id == "C001"
    assert composed.identity.contributor_ids == (
        "VALID",
    )


def test_ambiguous_identity_record_is_not_contributor_identity():
    valid = _extract(
        "VALID",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
        customer_id="C001",
    )

    ambiguous = _extract(
        "AMBIGUOUS",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T11:00:00Z",
        customer_id="C001",
        identity_quality=IdentityQuality.AMBIGUOUS,
    )

    composed = _compose(
        (
            valid,
            ambiguous,
        ),
    )

    assert composed.identity.customer_id == "C001"
    assert composed.identity.contributor_ids == (
        "VALID",
    )


def test_composition_identity_is_not_inferred_from_record_id():
    first = _extract(
        "CUSTOMER-DOES-NOT-MEAN-CUSTOMER-ID",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
        customer_id="C001",
    )

    composed = _compose(
        (first,),
    )

    assert composed.identity.customer_id == "C001"
    assert composed.identity.customer_id != first.evidence_id


def test_composition_keeps_identity_separate_from_source_provenance():
    first = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
        customer_id="C001",
    )

    composed = _compose(
        (first,),
    )

    assert composed.identity.customer_id == "C001"
    assert composed.provenance[0].source_system == "crm"


def test_composition_semantics_are_distinct_from_identity():
    first = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
        customer_id="C001",
    )

    composed = _compose(
        (first,),
    )

    assert composed.semantics.confirms_completion is True
    assert composed.identity.customer_id == "C001"


def test_composed_evidence_id_is_deterministic():
    first = _extract(
        "A",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    second = _extract(
        "B",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T11:00:00Z",
    )

    first_result = _compose(
        (
            first,
            second,
        ),
    )

    second_result = _compose(
        (
            first,
            second,
        ),
    )

    assert first_result.evidence_id == second_result.evidence_id


def test_reversing_items_changes_only_composition_order_metadata():
    first = _extract(
        "A",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    second = _extract(
        "B",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T11:00:00Z",
    )

    forward = _compose(
        (
            first,
            second,
        ),
    )

    reverse = _compose(
        (
            second,
            first,
        ),
    )

    assert forward.identity.customer_id == (
        reverse.identity.customer_id
    )

    assert forward.semantics == reverse.semantics

    assert set(forward.identity.contributor_ids) == set(
        reverse.identity.contributor_ids
    )


def test_composition_identity_does_not_invent_benchmark_metadata():
    first = _extract(
        "A",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    composed = _compose(
        (first,),
    )

    assert not hasattr(
        composed.identity,
        "expected_direction",
    )

    assert not hasattr(
        composed.identity,
        "benchmark_family",
    )

    assert not hasattr(
        composed.identity,
        "winner",
    )


def test_composition_envelope_is_deterministic():
    first = _extract(
        "A",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    second = _extract(
        "B",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T11:00:00Z",
    )

    first_result = _compose(
        (
            first,
            second,
        ),
    )

    second_result = _compose(
        (
            first,
            second,
        ),
    )

    assert first_result == second_result


def test_composition_does_not_mutate_source_identity():
    first = _extract(
        "A",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    original_identity = first.identity

    _compose(
        (first,),
    )

    assert first.identity == original_identity


def test_composition_does_not_mutate_source_provenance():
    first = _extract(
        "A",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    original_provenance = first.provenance

    _compose(
        (first,),
    )

    assert first.provenance == original_provenance


def test_composition_preserves_source_event_time_type():
    first = _extract(
        "A",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    composed = _compose(
        (first,),
    )

    assert isinstance(
        composed.provenance[0].occurred_at,
        datetime,
    )


def test_composition_identity_has_no_implicit_priority():
    first = _extract(
        "A",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    composed = _compose(
        (first,),
    )

    assert not hasattr(
        composed.identity,
        "source_priority",
    )

    assert not hasattr(
        composed.identity,
        "recency_priority",
    )