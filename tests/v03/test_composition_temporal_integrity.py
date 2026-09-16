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
class TemporalContribution:
    evidence_id: str
    concept: str
    polarity: str
    occurred_at: datetime


@dataclass(frozen=True)
class TemporalComposition:
    contributions: tuple[TemporalContribution, ...]

    @classmethod
    def from_items(
        cls,
        items: tuple[SemanticEvidence, ...],
    ) -> "TemporalComposition":
        contributions: list[TemporalContribution] = []

        for item in items:
            if item.identity.quality != IdentityQuality.CONFIRMED:
                continue

            if item.timestamp is None:
                continue

            timestamp = item.timestamp

            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(
                    tzinfo=timezone.utc
                )

            if (
                EVALUATION_AT - timestamp
                > timedelta(days=30)
            ):
                continue

            if item.semantics.concerns_same_work_item is False:
                continue

            if (
                item.semantics.requests_followup is True
                and "followup"
                not in item.semantics.negated_concepts
            ):
                contributions.append(
                    TemporalContribution(
                        evidence_id=item.evidence_id,
                        concept="followup",
                        polarity="positive",
                        occurred_at=timestamp,
                    )
                )

            if "followup" in item.semantics.negated_concepts:
                contributions.append(
                    TemporalContribution(
                        evidence_id=item.evidence_id,
                        concept="followup",
                        polarity="negative",
                        occurred_at=timestamp,
                    )
                )

            if (
                item.semantics.confirms_completion is True
                and "completion"
                not in item.semantics.negated_concepts
            ):
                contributions.append(
                    TemporalContribution(
                        evidence_id=item.evidence_id,
                        concept="completion",
                        polarity="positive",
                        occurred_at=timestamp,
                    )
                )

            if "completion" in item.semantics.negated_concepts:
                contributions.append(
                    TemporalContribution(
                        evidence_id=item.evidence_id,
                        concept="completion",
                        polarity="negative",
                        occurred_at=timestamp,
                    )
                )

            if (
                item.semantics.requests_next_step is True
                and "next_step"
                not in item.semantics.negated_concepts
            ):
                contributions.append(
                    TemporalContribution(
                        evidence_id=item.evidence_id,
                        concept="next_step",
                        polarity="positive",
                        occurred_at=timestamp,
                    )
                )

            if "next_step" in item.semantics.negated_concepts:
                contributions.append(
                    TemporalContribution(
                        evidence_id=item.evidence_id,
                        concept="next_step",
                        polarity="negative",
                        occurred_at=timestamp,
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
    customer_id: str = "C001",
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


def test_composition_retains_each_event_timestamp():
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

    composed = TemporalComposition.from_items(
        (
            early,
            late,
        ),
    )

    by_id = {
        item.evidence_id: item
        for item in composed.contributions
    }

    assert by_id["EARLY"].occurred_at == datetime(
        2026,
        9,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    assert by_id["LATE"].occurred_at == datetime(
        2026,
        9,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )


def test_composition_does_not_replace_event_time_with_evaluation_time():
    evidence = _extract(
        "EVENT",
        "crm",
        "The migration workshop is complete.",
        "2026-09-10T10:00:00Z",
    )

    composed = TemporalComposition.from_items(
        (evidence,),
    )

    assert composed.contributions[0].occurred_at != EVALUATION_AT
    assert composed.contributions[0].occurred_at == evidence.timestamp


def test_earlier_and_later_valid_records_keep_chronological_distinction():
    earlier = _extract(
        "EARLIER",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    later = _extract(
        "LATER",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    composed = TemporalComposition.from_items(
        (
            earlier,
            later,
        ),
    )

    positive = next(
        item
        for item in composed.contributions
        if item.evidence_id == "EARLIER"
    )

    negative = next(
        item
        for item in composed.contributions
        if item.evidence_id == "LATER"
    )

    assert positive.occurred_at < negative.occurred_at
    assert positive.polarity == "positive"
    assert negative.polarity == "negative"


def test_same_timestamp_conflict_remains_distinguishable():
    positive = _extract(
        "POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    composed = TemporalComposition.from_items(
        (
            positive,
            negative,
        ),
    )

    assert len(composed.contributions) == 2

    assert {
        item.occurred_at
        for item in composed.contributions
    } == {
        datetime(
            2026,
            9,
            12,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    }

    assert {
        item.polarity
        for item in composed.contributions
    } == {
        "positive",
        "negative",
    }


def test_stale_event_is_excluded_using_event_time():
    stale = _extract(
        "STALE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-07-01T10:00:00Z",
    )

    composed = TemporalComposition.from_items(
        (stale,),
    )

    assert composed.contributions == ()


def test_boundary_fresh_event_is_retained():
    boundary = _extract(
        "BOUNDARY",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-08-14T12:00:00Z",
    )

    assert boundary.timestamp is not None

    age = EVALUATION_AT - boundary.timestamp

    assert age == timedelta(days=30)

    composed = TemporalComposition.from_items(
        (boundary,),
    )

    assert len(composed.contributions) == 1
    assert composed.contributions[0].evidence_id == "BOUNDARY"


def test_just_over_boundary_event_is_excluded():
    stale = _extract(
        "STALE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-08-14T11:59:59Z",
    )

    assert stale.timestamp is not None

    age = EVALUATION_AT - stale.timestamp

    assert age > timedelta(days=30)

    composed = TemporalComposition.from_items(
        (stale,),
    )

    assert composed.contributions == ()


def test_future_event_is_retained_by_current_temporal_rule():
    future = _extract(
        "FUTURE",
        "email",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
    )

    assert future.timestamp is not None
    assert future.timestamp > EVALUATION_AT

    composed = TemporalComposition.from_items(
        (future,),
    )

    # Record current behavior explicitly. The current freshness rule
    # only rejects evidence older than stale_after_days; it does not
    # reject future timestamps.
    assert len(composed.contributions) == 1
    assert composed.contributions[0].evidence_id == "FUTURE"


def test_timestamp_timezone_information_is_preserved():
    evidence = _extract(
        "OFFSET",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T15:00:00+05:00",
    )

    composed = TemporalComposition.from_items(
        (evidence,),
    )

    assert len(composed.contributions) == 1

    contribution = composed.contributions[0]

    assert contribution.occurred_at.astimezone(
        timezone.utc
    ) == datetime(
        2026,
        9,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )


def test_multiple_event_times_remain_attached_to_their_records():
    first = _extract(
        "FIRST",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    second = _extract(
        "SECOND",
        "email",
        "The customer wants another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    third = _extract(
        "THIRD",
        "support",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    composed = TemporalComposition.from_items(
        (
            first,
            second,
            third,
        ),
    )

    times_by_id = {
        item.evidence_id: item.occurred_at
        for item in composed.contributions
    }

    assert times_by_id["FIRST"] < times_by_id["SECOND"]
    assert times_by_id["SECOND"] < times_by_id["THIRD"]


def test_temporal_composition_is_order_independent_as_a_set():
    early = _extract(
        "EARLY",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    late = _extract(
        "LATE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    forward = TemporalComposition.from_items(
        (
            early,
            late,
        ),
    )

    reverse = TemporalComposition.from_items(
        (
            late,
            early,
        ),
    )

    assert set(forward.contributions) == set(
        reverse.contributions
    )


def test_temporal_composition_is_deterministic():
    evidence = _extract(
        "EVENT",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    first = TemporalComposition.from_items(
        (evidence,),
    )

    second = TemporalComposition.from_items(
        (evidence,),
    )

    assert first == second


def test_temporal_composition_does_not_mutate_original_provenance():
    evidence = _extract(
        "EVENT",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    before = evidence.provenance

    composed = TemporalComposition.from_items(
        (evidence,),
    )

    assert composed.contributions
    assert evidence.provenance == before


def test_timestamp_does_not_become_a_hidden_priority_score():
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

    composed = TemporalComposition.from_items(
        (
            positive,
            negative,
        ),
    )

    assert len(composed.contributions) == 2

    assert {
        item.polarity
        for item in composed.contributions
    } == {
        "positive",
        "negative",
    }

    assert {
        item.evidence_id
        for item in composed.contributions
    } == {
        "POSITIVE",
        "NEGATIVE",
    }


def test_temporal_metadata_remains_separate_from_semantics():
    evidence = _extract(
        "EVENT",
        "crm",
        "The migration workshop is complete.",
        "2026-09-12T10:00:00Z",
    )

    composed = TemporalComposition.from_items(
        (evidence,),
    )

    contribution = composed.contributions[0]

    assert contribution.concept == "completion"
    assert contribution.polarity == "positive"
    assert contribution.occurred_at == evidence.timestamp

    assert not hasattr(
        contribution,
        "expected_direction",
    )

    assert not hasattr(
        contribution,
        "benchmark_family",
    )

    assert not hasattr(
        contribution,
        "priority",
    )