from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class ChronologicalFact:
    evidence_id: str
    concept: str
    polarity: str
    occurred_at: datetime
    source_system: str


@dataclass(frozen=True)
class ChronologicalComposition:
    facts: tuple[ChronologicalFact, ...]

    @property
    def ordered_facts(self) -> tuple[ChronologicalFact, ...]:
        return tuple(
            sorted(
                self.facts,
                key=lambda item: (
                    item.occurred_at,
                    item.evidence_id,
                ),
            )
        )

    @property
    def earliest(self) -> ChronologicalFact | None:
        ordered = self.ordered_facts
        return ordered[0] if ordered else None

    @property
    def latest(self) -> ChronologicalFact | None:
        ordered = self.ordered_facts
        return ordered[-1] if ordered else None

    @classmethod
    def from_items(
        cls,
        items: tuple[SemanticEvidence, ...],
    ) -> "ChronologicalComposition":
        facts: list[ChronologicalFact] = []

        for item in items:
            if item.identity.quality != IdentityQuality.CONFIRMED:
                continue

            timestamp = item.timestamp

            if timestamp is None:
                continue

            when = timestamp

            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)

            if EVALUATION_AT - when > timedelta(days=30):
                continue

            if item.semantics.concerns_same_work_item is False:
                continue

            if item.semantics.requests_followup is True:
                if "followup" not in item.semantics.negated_concepts:
                    facts.append(
                        ChronologicalFact(
                            evidence_id=item.evidence_id,
                            concept="followup",
                            polarity="positive",
                            occurred_at=when,
                            source_system=item.provenance.source_system,
                        )
                    )

            if "followup" in item.semantics.negated_concepts:
                facts.append(
                    ChronologicalFact(
                        evidence_id=item.evidence_id,
                        concept="followup",
                        polarity="negative",
                        occurred_at=when,
                        source_system=item.provenance.source_system,
                    )
                )

            if item.semantics.confirms_completion is True:
                if "completion" not in item.semantics.negated_concepts:
                    facts.append(
                        ChronologicalFact(
                            evidence_id=item.evidence_id,
                            concept="completion",
                            polarity="positive",
                            occurred_at=when,
                            source_system=item.provenance.source_system,
                        )
                    )

            if "completion" in item.semantics.negated_concepts:
                facts.append(
                    ChronologicalFact(
                        evidence_id=item.evidence_id,
                        concept="completion",
                        polarity="negative",
                        occurred_at=when,
                        source_system=item.provenance.source_system,
                    )
                )

            if item.semantics.requests_next_step is True:
                if "next_step" not in item.semantics.negated_concepts:
                    facts.append(
                        ChronologicalFact(
                            evidence_id=item.evidence_id,
                            concept="next_step",
                            polarity="positive",
                            occurred_at=when,
                            source_system=item.provenance.source_system,
                        )
                    )

            if "next_step" in item.semantics.negated_concepts:
                facts.append(
                    ChronologicalFact(
                        evidence_id=item.evidence_id,
                        concept="next_step",
                        polarity="negative",
                        occurred_at=when,
                        source_system=item.provenance.source_system,
                    )
                )

        return cls(
            facts=tuple(facts),
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


def test_chronology_orders_distinct_event_times():
    early = _extract(
        "EARLY",
        "crm",
        "The migration workshop is complete.",
        "2026-09-10T10:00:00Z",
    )

    late = _extract(
        "LATE",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T10:00:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (
            late,
            early,
        ),
    )

    assert [item.evidence_id for item in composition.ordered_facts] == [
        "EARLY",
        "LATE",
    ]


def test_earliest_and_latest_are_derived_from_event_time():
    early = _extract(
        "EARLY",
        "crm",
        "The migration workshop is complete.",
        "2026-09-10T10:00:00Z",
    )

    late = _extract(
        "LATE",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T10:00:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (
            early,
            late,
        ),
    )

    assert composition.earliest is not None
    assert composition.latest is not None

    assert composition.earliest.evidence_id == "EARLY"
    assert composition.latest.evidence_id == "LATE"


def test_chronology_preserves_semantic_polarity():
    earlier_positive = _extract(
        "POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    later_negative = _extract(
        "NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (
            earlier_positive,
            later_negative,
        ),
    )

    assert composition.earliest is not None
    assert composition.latest is not None

    assert composition.earliest.polarity == "positive"
    assert composition.latest.polarity == "negative"


def test_chronology_does_not_resolve_conflict():
    positive = _extract(
        "POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (
            positive,
            negative,
        ),
    )

    polarities = {
        item.polarity
        for item in composition.facts
        if item.concept == "followup"
    }

    assert polarities == {
        "positive",
        "negative",
    }


def test_same_timestamp_uses_deterministic_evidence_id_tiebreaker():
    first = _extract(
        "A",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    second = _extract(
        "B",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (
            second,
            first,
        ),
    )

    assert [
        item.evidence_id
        for item in composition.ordered_facts
    ] == [
        "A",
        "B",
    ]


def test_timezone_offsets_are_compared_as_instants():
    first = _extract(
        "FIRST",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T15:00:00+05:00",
    )

    second = _extract(
        "SECOND",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T10:30:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (
            first,
            second,
        ),
    )

    assert composition.earliest is not None
    assert composition.latest is not None

    # 15:00 at UTC+05:00 is 10:00 UTC.
    # 10:30 UTC is therefore later.
    assert composition.earliest.evidence_id == "FIRST"
    assert composition.latest.evidence_id == "SECOND"

def test_stale_events_do_not_participate_in_chronology():
    fresh = _extract(
        "FRESH",
        "crm",
        "The customer asks what comes next.",
        "2026-09-12T10:00:00Z",
    )

    stale = _extract(
        "STALE",
        "email",
        "The migration workshop is complete.",
        "2026-07-01T10:00:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (
            stale,
            fresh,
        ),
    )

    assert [
        item.evidence_id
        for item in composition.ordered_facts
    ] == ["FRESH"]


def test_wrong_identity_does_not_participate_in_chronology():
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

    composition = ChronologicalComposition.from_items(
        (
            valid,
            wrong_identity,
        ),
    )

    assert [
        item.evidence_id
        for item in composition.ordered_facts
    ] == ["VALID"]


def test_irrelevant_event_does_not_participate_in_chronology():
    valid = _extract(
        "VALID",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    irrelevant = _extract(
        "IRRELEVANT",
        "email",
        "The customer is discussing a separate store rollout "
        "and says nothing about this opportunity.",
        "2026-09-12T11:00:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (
            valid,
            irrelevant,
        ),
    )

    assert [
        item.evidence_id
        for item in composition.ordered_facts
    ] == ["VALID"]


def test_negated_event_remains_in_chronology_with_negative_polarity():
    negative = _extract(
        "NEGATIVE",
        "crm",
        "The migration workshop is not complete.",
        "2026-09-12T10:00:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (negative,),
    )

    assert len(composition.facts) == 1
    assert composition.facts[0].concept == "completion"
    assert composition.facts[0].polarity == "negative"


def test_three_events_produce_stable_chronological_sequence():
    first = _extract(
        "FIRST",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    second = _extract(
        "SECOND",
        "email",
        "The migration workshop is complete.",
        "2026-09-11T10:00:00Z",
    )

    third = _extract(
        "THIRD",
        "support",
        "The customer asks what comes next.",
        "2026-09-12T10:00:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (
            third,
            first,
            second,
        ),
    )

    assert [
        item.evidence_id
        for item in composition.ordered_facts
    ] == [
        "FIRST",
        "SECOND",
        "THIRD",
    ]


def test_chronology_preserves_source_system_per_event():
    crm = _extract(
        "CRM",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    email = _extract(
        "EMAIL",
        "email",
        "The customer asks what comes next.",
        "2026-09-12T10:00:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (
            crm,
            email,
        ),
    )

    by_id = {
        item.evidence_id: item
        for item in composition.facts
    }

    assert by_id["CRM"].source_system == "crm"
    assert by_id["EMAIL"].source_system == "email"


def test_chronology_does_not_mutate_original_evidence():
    evidence = _extract(
        "EVENT",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    semantics_before = evidence.semantics
    provenance_before = evidence.provenance

    composition = ChronologicalComposition.from_items(
        (evidence,),
    )

    assert composition.facts
    assert evidence.semantics == semantics_before
    assert evidence.provenance == provenance_before


def test_chronology_is_deterministic():
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

    first_result = ChronologicalComposition.from_items(
        (
            first,
            second,
        ),
    )

    second_result = ChronologicalComposition.from_items(
        (
            first,
            second,
        ),
    )

    assert first_result == second_result


def test_chronology_is_order_independent_for_same_event_set():
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

    forward = ChronologicalComposition.from_items(
        (
            first,
            second,
        ),
    )

    reverse = ChronologicalComposition.from_items(
        (
            second,
            first,
        ),
    )

    assert set(forward.facts) == set(reverse.facts)
    assert [
        item.evidence_id
        for item in forward.ordered_facts
    ] == [
        item.evidence_id
        for item in reverse.ordered_facts
    ]


def test_future_event_retains_its_chronological_position():
    past = _extract(
        "PAST",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    future = _extract(
        "FUTURE",
        "email",
        "The customer asks what comes next.",
        "2026-09-14T10:00:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (
            future,
            past,
        ),
    )

    assert [
        item.evidence_id
        for item in composition.ordered_facts
    ] == [
        "PAST",
        "FUTURE",
    ]


def test_chronological_composition_has_no_benchmark_policy():
    evidence = _extract(
        "EVENT",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    composition = ChronologicalComposition.from_items(
        (evidence,),
    )

    for fact in composition.facts:
        assert not hasattr(fact, "expected_direction")
        assert not hasattr(fact, "benchmark_family")
        assert not hasattr(fact, "winner")
        assert not hasattr(fact, "priority")
        