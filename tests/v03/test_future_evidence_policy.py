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
class TemporalPolicyResult:
    accepted: bool
    evidence_id: str


class FutureEvidencePolicy:
    """
    Test-layer policy candidates for future-dated evidence.

    The production reasoner is intentionally not modified here.
    """

    @staticmethod
    def current_behavior(
        item: SemanticEvidence,
    ) -> TemporalPolicyResult:
        if item.timestamp is None:
            return TemporalPolicyResult(
                accepted=False,
                evidence_id=item.evidence_id,
            )

        when = item.timestamp

        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)

        if (
            EVALUATION_AT - when
            > timedelta(days=30)
        ):
            return TemporalPolicyResult(
                accepted=False,
                evidence_id=item.evidence_id,
            )

        return TemporalPolicyResult(
            accepted=True,
            evidence_id=item.evidence_id,
        )

    @staticmethod
    def strict_no_future(
        item: SemanticEvidence,
    ) -> TemporalPolicyResult:
        if item.timestamp is None:
            return TemporalPolicyResult(
                accepted=False,
                evidence_id=item.evidence_id,
            )

        when = item.timestamp

        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)

        if when > EVALUATION_AT:
            return TemporalPolicyResult(
                accepted=False,
                evidence_id=item.evidence_id,
            )

        if (
            EVALUATION_AT - when
            > timedelta(days=30)
        ):
            return TemporalPolicyResult(
                accepted=False,
                evidence_id=item.evidence_id,
            )

        return TemporalPolicyResult(
            accepted=True,
            evidence_id=item.evidence_id,
        )


def _extract(
    evidence_id: str,
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
        source_system="secondary",
        record_id=evidence_id,
        occurred_at=occurred_at,
        customer_id=customer_id,
        identity_quality=identity_quality,
    ).evidence


def test_current_policy_accepts_future_evidence():
    future = _extract(
        "FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
    )

    result = FutureEvidencePolicy.current_behavior(
        future,
    )

    assert future.timestamp is not None
    assert future.timestamp > EVALUATION_AT
    assert result.accepted is True


def test_strict_policy_rejects_future_evidence():
    future = _extract(
        "FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
    )

    result = FutureEvidencePolicy.strict_no_future(
        future,
    )

    assert future.timestamp is not None
    assert future.timestamp > EVALUATION_AT
    assert result.accepted is False


def test_current_and_strict_policies_agree_on_past_fresh_evidence():
    past = _extract(
        "PAST",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    current = FutureEvidencePolicy.current_behavior(
        past,
    )

    strict = FutureEvidencePolicy.strict_no_future(
        past,
    )

    assert current.accepted is True
    assert strict.accepted is True


def test_current_and_strict_policies_agree_on_stale_evidence():
    stale = _extract(
        "STALE",
        "The customer wants another discussion about the proposal.",
        "2026-07-01T10:00:00Z",
    )

    current = FutureEvidencePolicy.current_behavior(
        stale,
    )

    strict = FutureEvidencePolicy.strict_no_future(
        stale,
    )

    assert current.accepted is False
    assert strict.accepted is False


def test_exact_evaluation_timestamp_is_not_future():
    current_time = _extract(
        "CURRENT",
        "The customer wants another discussion about the proposal.",
        "2026-09-13T12:00:00Z",
    )

    current = FutureEvidencePolicy.current_behavior(
        current_time,
    )

    strict = FutureEvidencePolicy.strict_no_future(
        current_time,
    )

    assert current_time.timestamp == EVALUATION_AT
    assert current.accepted is True
    assert strict.accepted is True


def test_one_second_future_is_distinguished_from_current_time():
    future = _extract(
        "ONE-SECOND-FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-13T12:00:01Z",
    )

    assert future.timestamp is not None
    assert future.timestamp > EVALUATION_AT

    current = FutureEvidencePolicy.current_behavior(
        future,
    )

    strict = FutureEvidencePolicy.strict_no_future(
        future,
    )

    assert current.accepted is True
    assert strict.accepted is False


def test_future_event_time_is_preserved_without_rewriting():
    future = _extract(
        "FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
    )

    assert future.timestamp == datetime(
        2026,
        9,
        14,
        10,
        0,
        tzinfo=timezone.utc,
    )

    assert future.timestamp > EVALUATION_AT


def test_future_policy_does_not_modify_semantics():
    future = _extract(
        "FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
    )

    before = future.semantics

    FutureEvidencePolicy.current_behavior(
        future,
    )

    FutureEvidencePolicy.strict_no_future(
        future,
    )

    assert future.semantics == before


def test_future_policy_does_not_modify_provenance():
    future = _extract(
        "FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
    )

    before = future.provenance

    FutureEvidencePolicy.current_behavior(
        future,
    )

    FutureEvidencePolicy.strict_no_future(
        future,
    )

    assert future.provenance == before


def test_future_evidence_remains_traceable_under_both_policies():
    future = _extract(
        "FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
    )

    current = FutureEvidencePolicy.current_behavior(
        future,
    )

    strict = FutureEvidencePolicy.strict_no_future(
        future,
    )

    assert current.evidence_id == "FUTURE"
    assert strict.evidence_id == "FUTURE"


def test_future_policy_is_independent_of_source_system():
    crm = _extract(
        "CRM-FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
    )

    email = _extract(
        "EMAIL-FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
    )

    assert (
        FutureEvidencePolicy.strict_no_future(crm).accepted
        is False
    )

    assert (
        FutureEvidencePolicy.strict_no_future(email).accepted
        is False
    )


def test_future_policy_is_independent_of_identity_when_testing_time_rule():
    future_confirmed = _extract(
        "CONFIRMED-FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
        identity_quality=IdentityQuality.CONFIRMED,
    )

    future_ambiguous = _extract(
        "AMBIGUOUS-FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
        identity_quality=IdentityQuality.AMBIGUOUS,
    )

    assert (
        FutureEvidencePolicy.strict_no_future(
            future_confirmed
        ).accepted
        is False
    )

    assert (
        FutureEvidencePolicy.strict_no_future(
            future_ambiguous
        ).accepted
        is False
    )


def test_future_policy_does_not_resolve_semantic_conflict():
    future_positive = _extract(
        "FUTURE-POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
    )

    past_negative = _extract(
        "PAST-NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    current_positive = FutureEvidencePolicy.current_behavior(
        future_positive,
    )

    strict_positive = FutureEvidencePolicy.strict_no_future(
        future_positive,
    )

    past_result = FutureEvidencePolicy.strict_no_future(
        past_negative,
    )

    assert current_positive.accepted is True
    assert strict_positive.accepted is False
    assert past_result.accepted is True

    # Temporal eligibility is deliberately kept separate from
    # semantic conflict resolution.
    assert future_positive.semantics.requests_followup is True
    assert "followup" in past_negative.semantics.negated_concepts


def test_future_policy_candidates_are_deterministic():
    future = _extract(
        "FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
    )

    first = FutureEvidencePolicy.strict_no_future(
        future,
    )

    second = FutureEvidencePolicy.strict_no_future(
        future,
    )

    assert first == second


def test_future_policy_candidates_have_no_benchmark_logic():
    future = _extract(
        "FUTURE",
        "The customer wants another discussion about the proposal.",
        "2026-09-14T10:00:00Z",
    )

    result = FutureEvidencePolicy.strict_no_future(
        future,
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


def test_future_policy_boundary_is_explicitly_measurable():
    timestamps = (
        "2026-09-13T11:59:59Z",
        "2026-09-13T12:00:00Z",
        "2026-09-13T12:00:01Z",
    )

    results = tuple(
        FutureEvidencePolicy.strict_no_future(
            _extract(
                timestamp.replace(":", "-"),
                "The customer wants another discussion about the proposal.",
                timestamp,
            )
        ).accepted
        for timestamp in timestamps
    )

    assert results == (
        True,
        True,
        False,
    )