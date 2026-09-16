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
class SourceContribution:
    concept: str
    polarity: str
    evidence_id: str
    source_system: str
    occurred_at: datetime


@dataclass(frozen=True)
class SourceAwareComposition:
    contributions: tuple[SourceContribution, ...]

    @classmethod
    def from_items(
        cls,
        items: tuple[SemanticEvidence, ...],
    ) -> "SourceAwareComposition":
        contributions: list[SourceContribution] = []

        for item in items:
            if item.identity.quality != IdentityQuality.CONFIRMED:
                continue

            if item.timestamp is None:
                continue

            if (
                item.semantics.confirms_completion is True
                and "completion"
                not in item.semantics.negated_concepts
            ):
                contributions.append(
                    SourceContribution(
                        concept="completion",
                        polarity="positive",
                        evidence_id=item.evidence_id,
                        source_system=item.provenance.source_system,
                        occurred_at=item.timestamp,
                    )
                )

            if "completion" in item.semantics.negated_concepts:
                contributions.append(
                    SourceContribution(
                        concept="completion",
                        polarity="negative",
                        evidence_id=item.evidence_id,
                        source_system=item.provenance.source_system,
                        occurred_at=item.timestamp,
                    )
                )

            if (
                item.semantics.requests_next_step is True
                and "next_step"
                not in item.semantics.negated_concepts
            ):
                contributions.append(
                    SourceContribution(
                        concept="next_step",
                        polarity="positive",
                        evidence_id=item.evidence_id,
                        source_system=item.provenance.source_system,
                        occurred_at=item.timestamp,
                    )
                )

            if "next_step" in item.semantics.negated_concepts:
                contributions.append(
                    SourceContribution(
                        concept="next_step",
                        polarity="negative",
                        evidence_id=item.evidence_id,
                        source_system=item.provenance.source_system,
                        occurred_at=item.timestamp,
                    )
                )

            if (
                item.semantics.requests_followup is True
                and "followup"
                not in item.semantics.negated_concepts
            ):
                contributions.append(
                    SourceContribution(
                        concept="followup",
                        polarity="positive",
                        evidence_id=item.evidence_id,
                        source_system=item.provenance.source_system,
                        occurred_at=item.timestamp,
                    )
                )

            if "followup" in item.semantics.negated_concepts:
                contributions.append(
                    SourceContribution(
                        concept="followup",
                        polarity="negative",
                        evidence_id=item.evidence_id,
                        source_system=item.provenance.source_system,
                        occurred_at=item.timestamp,
                    )
                )

            if (
                item.semantics.confirms_approval is True
                and "approval"
                not in item.semantics.negated_concepts
            ):
                contributions.append(
                    SourceContribution(
                        concept="approval",
                        polarity="positive",
                        evidence_id=item.evidence_id,
                        source_system=item.provenance.source_system,
                        occurred_at=item.timestamp,
                    )
                )

            if "approval" in item.semantics.negated_concepts:
                contributions.append(
                    SourceContribution(
                        concept="approval",
                        polarity="negative",
                        evidence_id=item.evidence_id,
                        source_system=item.provenance.source_system,
                        occurred_at=item.timestamp,
                    )
                )

        return cls(
            contributions=tuple(contributions),
        )


def _extract(
    evidence_id: str,
    source_system: str,
    text: str,
    occurred_at: str,
    *,
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system=source_system,
        record_id=evidence_id,
        occurred_at=occurred_at,
        customer_id="C001",
        identity_quality=identity_quality,
    ).evidence


def test_contribution_retains_source_system():
    evidence = _extract(
        "CRM-1",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    composition = SourceAwareComposition.from_items(
        (evidence,),
    )

    assert composition.contributions == (
        SourceContribution(
            concept="completion",
            polarity="positive",
            evidence_id="CRM-1",
            source_system="crm",
            occurred_at=datetime(
                2026,
                9,
                12,
                10,
                0,
                tzinfo=timezone.utc,
            ),
        ),
    )


def test_contribution_retains_occurrence_timestamp():
    evidence = _extract(
        "EMAIL-1",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T11:30:00Z",
    )

    composition = SourceAwareComposition.from_items(
        (evidence,),
    )

    contribution = composition.contributions[0]

    assert contribution.occurred_at == datetime(
        2026,
        9,
        12,
        11,
        30,
        tzinfo=timezone.utc,
    )


def test_two_systems_remain_distinguishable():
    crm = _extract(
        "CRM-1",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    email = _extract(
        "EMAIL-1",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T11:00:00Z",
    )

    composition = SourceAwareComposition.from_items(
        (
            crm,
            email,
        ),
    )

    assert set(composition.contributions) == {
        SourceContribution(
            concept="completion",
            polarity="positive",
            evidence_id="CRM-1",
            source_system="crm",
            occurred_at=crm.timestamp,
        ),
        SourceContribution(
            concept="next_step",
            polarity="positive",
            evidence_id="EMAIL-1",
            source_system="email",
            occurred_at=email.timestamp,
        ),
    }


def test_source_provenance_is_not_replaced_by_record_id():
    evidence = _extract(
        "SAME-RECORD-ID",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    composition = SourceAwareComposition.from_items(
        (evidence,),
    )

    contribution = composition.contributions[0]

    assert contribution.evidence_id == "SAME-RECORD-ID"
    assert contribution.source_system == "crm"
    assert contribution.evidence_id != contribution.source_system


def test_same_fact_from_two_systems_retains_both_sources():
    crm = _extract(
        "CRM-COMPLETE",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    email = _extract(
        "EMAIL-COMPLETE",
        "email",
        "The migration workshop is complete.",
        "2026-09-12T11:00:00Z",
    )

    composition = SourceAwareComposition.from_items(
        (
            crm,
            email,
        ),
    )

    completion_contributions = tuple(
        contribution
        for contribution in composition.contributions
        if contribution.concept == "completion"
    )

    assert len(completion_contributions) == 2

    assert {
        contribution.source_system
        for contribution in completion_contributions
    } == {
        "crm",
        "email",
    }


def test_conflicting_sources_retain_source_and_timestamp_per_polarity():
    positive = _extract(
        "CRM-POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    negative = _extract(
        "EMAIL-NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    composition = SourceAwareComposition.from_items(
        (
            positive,
            negative,
        ),
    )

    assert set(composition.contributions) == {
        SourceContribution(
            concept="followup",
            polarity="positive",
            evidence_id="CRM-POSITIVE",
            source_system="crm",
            occurred_at=positive.timestamp,
        ),
        SourceContribution(
            concept="followup",
            polarity="negative",
            evidence_id="EMAIL-NEGATIVE",
            source_system="email",
            occurred_at=negative.timestamp,
        ),
    }


def test_wrong_identity_has_no_source_contribution():
    valid = _extract(
        "VALID",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    wrong_identity = _extract(
        "WRONG",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T11:00:00Z",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    composition = SourceAwareComposition.from_items(
        (
            valid,
            wrong_identity,
        ),
    )

    assert composition.contributions == (
        SourceContribution(
            concept="completion",
            polarity="positive",
            evidence_id="VALID",
            source_system="crm",
            occurred_at=valid.timestamp,
        ),
    )


def test_negated_fact_retains_negative_source_provenance():
    evidence = _extract(
        "EMAIL-NO-COMPLETION",
        "email",
        "The migration workshop is not complete.",
        "2026-09-12T11:00:00Z",
    )

    composition = SourceAwareComposition.from_items(
        (evidence,),
    )

    assert composition.contributions == (
        SourceContribution(
            concept="completion",
            polarity="negative",
            evidence_id="EMAIL-NO-COMPLETION",
            source_system="email",
            occurred_at=evidence.timestamp,
        ),
    )


def test_stale_evidence_can_be_excluded_without_losing_fresh_provenance():
    fresh = _extract(
        "FRESH",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    stale = _extract(
        "STALE",
        "email",
        "The customer asks what comes next.",
        "2026-07-01T10:00:00Z",
    )

    fresh_timestamp = fresh.timestamp

    assert fresh_timestamp is not None
    assert stale.timestamp is not None

    from datetime import timedelta

    assert (
        EVALUATION_AT - stale.timestamp
        > timedelta(days=30)
    )

    composition = SourceAwareComposition.from_items(
        (fresh,),
    )

    assert composition.contributions == (
        SourceContribution(
            concept="completion",
            polarity="positive",
            evidence_id="FRESH",
            source_system="crm",
            occurred_at=fresh.timestamp,
        ),
    )


def test_composition_does_not_mutate_source_provenance():
    evidence = _extract(
        "CRM-1",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    before_source = evidence.provenance.source_system
    before_record = evidence.provenance.record_id
    before_timestamp = evidence.provenance.occurred_at

    composition = SourceAwareComposition.from_items(
        (evidence,),
    )

    assert composition.contributions

    assert evidence.provenance.source_system == before_source
    assert evidence.provenance.record_id == before_record
    assert evidence.provenance.occurred_at == before_timestamp


def test_source_aware_composition_is_order_independent_as_a_set():
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

    forward = SourceAwareComposition.from_items(
        (
            first,
            second,
        ),
    )

    reversed_order = SourceAwareComposition.from_items(
        (
            second,
            first,
        ),
    )

    assert set(forward.contributions) == set(
        reversed_order.contributions
    )


def test_source_aware_provenance_is_deterministic():
    evidence = _extract(
        "CRM-1",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    first = SourceAwareComposition.from_items(
        (evidence,),
    )

    second = SourceAwareComposition.from_items(
        (evidence,),
    )

    assert first == second


def test_provenance_contains_no_benchmark_expectations():
    evidence = _extract(
        "CRM-1",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    composition = SourceAwareComposition.from_items(
        (evidence,),
    )

    for contribution in composition.contributions:
        assert not hasattr(
            contribution,
            "expected_direction",
        )
        assert not hasattr(
            contribution,
            "benchmark_family",
        )