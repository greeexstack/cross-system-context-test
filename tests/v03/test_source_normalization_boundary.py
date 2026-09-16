from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class NormalizedSourceFact:
    concept: str
    polarity: str
    evidence_id: str
    source_system: str
    occurred_at: datetime


def _extract(
    evidence_id: str,
    source_system: str,
    text: str,
    occurred_at: str = "2026-09-12T10:00:00Z",
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system=source_system,
        record_id=evidence_id,
        occurred_at=occurred_at,
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    ).evidence


def _normalize_followup(
    item: SemanticEvidence,
) -> NormalizedSourceFact | None:
    if item.identity.quality != IdentityQuality.CONFIRMED:
        return None

    if item.timestamp is None:
        return None

    if item.semantics.concerns_same_work_item is False:
        return None

    if item.semantics.requests_followup is True:
        if "followup" in item.semantics.negated_concepts:
            return None

        return NormalizedSourceFact(
            concept="followup",
            polarity="positive",
            evidence_id=item.evidence_id,
            source_system=item.provenance.source_system,
            occurred_at=item.timestamp,
        )

    if "followup" in item.semantics.negated_concepts:
        return NormalizedSourceFact(
            concept="followup",
            polarity="negative",
            evidence_id=item.evidence_id,
            source_system=item.provenance.source_system,
            occurred_at=item.timestamp,
        )

    return None


def test_different_source_wordings_normalize_to_same_positive_concept():
    crm = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    email = _extract(
        "EMAIL-1",
        "email",
        "The customer would like to speak about the offer again.",
    )

    crm_fact = _normalize_followup(crm)
    email_fact = _normalize_followup(email)

    assert crm_fact is not None
    assert email_fact is not None

    assert crm_fact.concept == "followup"
    assert email_fact.concept == "followup"

    assert crm_fact.polarity == "positive"
    assert email_fact.polarity == "positive"


def test_normalization_does_not_erase_source_identity():
    crm = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    email = _extract(
        "EMAIL-1",
        "email",
        "The customer would like to speak about the offer again.",
    )

    crm_fact = _normalize_followup(crm)
    email_fact = _normalize_followup(email)

    assert crm_fact is not None
    assert email_fact is not None

    assert crm_fact.source_system == "crm"
    assert email_fact.source_system == "email"

    assert crm_fact.evidence_id == "CRM-1"
    assert email_fact.evidence_id == "EMAIL-1"


def test_normalization_does_not_erase_occurrence_time():
    crm = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
        occurred_at="2026-09-10T10:00:00Z",
    )

    email = _extract(
        "EMAIL-1",
        "email",
        "The customer would like to speak about the offer again.",
        occurred_at="2026-09-12T10:00:00Z",
    )

    crm_fact = _normalize_followup(crm)
    email_fact = _normalize_followup(email)

    assert crm_fact is not None
    assert email_fact is not None

    assert crm_fact.occurred_at == datetime(
        2026,
        9,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    assert email_fact.occurred_at == datetime(
        2026,
        9,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )


def test_positive_and_negative_source_wordings_remain_distinct():
    positive = _extract(
        "CRM-POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "EMAIL-NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
    )

    positive_fact = _normalize_followup(positive)
    negative_fact = _normalize_followup(negative)

    assert positive_fact is not None
    assert negative_fact is not None

    assert positive_fact.concept == negative_fact.concept
    assert positive_fact.polarity == "positive"
    assert negative_fact.polarity == "negative"


def test_negated_source_fact_is_not_normalized_as_positive():
    evidence = _extract(
        "EMAIL-NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
    )

    fact = _normalize_followup(evidence)

    assert fact is not None
    assert fact.polarity == "negative"


def test_irrelevant_evidence_does_not_normalize_as_followup():
    evidence = _extract(
        "IRRELEVANT",
        "crm",
        "The customer is discussing a separate store rollout "
        "and says nothing about this opportunity.",
    )

    fact = _normalize_followup(evidence)

    assert fact is None


def test_identity_failure_prevents_source_fact_normalization():
    extractor = LexicalNormalizationSemanticExtractor()

    wrong_identity = extractor.extract(
        evidence_id="WRONG-ID",
        content=(
            "The customer wants another discussion about the proposal."
        ),
        source_system="crm",
        record_id="WRONG-ID",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    ).evidence

    fact = _normalize_followup(wrong_identity)

    assert fact is None


def test_same_concept_from_two_systems_is_not_collapsed():
    crm = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    email = _extract(
        "EMAIL-1",
        "email",
        "The customer wants another discussion about the proposal.",
    )

    crm_fact = _normalize_followup(crm)
    email_fact = _normalize_followup(email)

    assert crm_fact is not None
    assert email_fact is not None

    assert crm_fact != email_fact
    assert crm_fact.evidence_id != email_fact.evidence_id
    assert crm_fact.source_system != email_fact.source_system


def test_source_name_does_not_change_normalized_semantic_concept():
    source_names = (
        "crm",
        "email",
        "support",
        "billing",
        "legacy",
    )

    facts = tuple(
        _normalize_followup(
            _extract(
                source.upper(),
                source,
                "The customer wants another discussion about the proposal.",
            )
        )
        for source in source_names
    )

    assert all(fact is not None for fact in facts)

    assert {
        fact.concept
        for fact in facts
        if fact is not None
    } == {"followup"}

    assert {
        fact.polarity
        for fact in facts
        if fact is not None
    } == {"positive"}


def test_source_name_does_not_change_polarity():
    crm = _extract(
        "CRM",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    billing = _extract(
        "BILLING",
        "billing",
        "The customer does not want another discussion about the proposal.",
    )

    crm_fact = _normalize_followup(crm)
    billing_fact = _normalize_followup(billing)

    assert crm_fact is not None
    assert billing_fact is not None

    assert crm_fact.polarity == "positive"
    assert billing_fact.polarity == "negative"


def test_source_normalization_is_deterministic():
    evidence = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    first = _normalize_followup(evidence)
    second = _normalize_followup(evidence)

    assert first == second


def test_source_normalization_does_not_mutate_evidence():
    evidence = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    before_semantics = evidence.semantics
    before_provenance = evidence.provenance
    before_identity = evidence.identity

    fact = _normalize_followup(evidence)

    assert fact is not None

    assert evidence.semantics == before_semantics
    assert evidence.provenance == before_provenance
    assert evidence.identity == before_identity


def test_source_normalization_is_independent_of_benchmark_policy():
    evidence = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    fact = _normalize_followup(evidence)

    assert fact is not None

    assert not hasattr(
        fact,
        "expected_direction",
    )

    assert not hasattr(
        fact,
        "benchmark_family",
    )

    assert not hasattr(
        fact,
        "winner",
    )

    assert not hasattr(
        fact,
        "priority",
    )


def test_source_normalization_keeps_same_concept_and_different_provenance():
    crm = _extract(
        "CRM",
        "crm",
        "The customer wants another discussion about the proposal.",
        occurred_at="2026-09-10T10:00:00Z",
    )

    email = _extract(
        "EMAIL",
        "email",
        "The customer wants another discussion about the proposal.",
        occurred_at="2026-09-12T10:00:00Z",
    )

    crm_fact = _normalize_followup(crm)
    email_fact = _normalize_followup(email)

    assert crm_fact is not None
    assert email_fact is not None

    assert crm_fact.concept == email_fact.concept
    assert crm_fact.polarity == email_fact.polarity

    assert crm_fact.evidence_id != email_fact.evidence_id
    assert crm_fact.source_system != email_fact.source_system
    assert crm_fact.occurred_at != email_fact.occurred_at


def test_current_evaluation_time_is_not_substituted_for_event_time():
    evidence = _extract(
        "CRM",
        "crm",
        "The customer wants another discussion about the proposal.",
        occurred_at="2026-09-10T10:00:00Z",
    )

    fact = _normalize_followup(evidence)

    assert fact is not None

    assert fact.occurred_at == datetime(
        2026,
        9,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    assert fact.occurred_at != EVALUATION_AT