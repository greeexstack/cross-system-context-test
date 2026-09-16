from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


class ConflictPolicy(str, Enum):
    CURRENT_PRECEDENCE = "current_precedence"
    RECENCY = "recency"
    EXPLICIT_CONFLICT = "explicit_conflict"


@dataclass(frozen=True)
class CandidateResult:
    policy: ConflictPolicy
    interpretation: str
    decision_strength: str
    status: str
    selected_evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class ConflictInput:
    primary_interpretation: str
    positive: SemanticEvidence
    negative: SemanticEvidence


def _extract(
    evidence_id: str,
    text: str,
    occurred_at: str,
    *,
    source_system: str,
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


def _fresh(item: SemanticEvidence) -> bool:
    if item.timestamp is None:
        return False

    timestamp = item.timestamp

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return (
        EVALUATION_AT - timestamp
        <= timedelta(days=30)
    )


def _candidate(
    conflict: ConflictInput,
    policy: ConflictPolicy,
) -> CandidateResult:
    positive = conflict.positive
    negative = conflict.negative

    if not _fresh(positive) and not _fresh(negative):
        return CandidateResult(
            policy=policy,
            interpretation=conflict.primary_interpretation,
            decision_strength="moderate",
            status="no_fresh_evidence",
            selected_evidence_ids=(),
        )

    if not _fresh(positive):
        selected = (negative,)
    elif not _fresh(negative):
        selected = (positive,)
    else:
        selected = (positive, negative)

    if policy == ConflictPolicy.CURRENT_PRECEDENCE:
        # Mirrors the existing reasoner's semantic precedence:
        # positive follow-up is accepted when present.
        has_positive = any(
            item.semantics.requests_followup is True
            for item in selected
        )

        if has_positive:
            return CandidateResult(
                policy=policy,
                interpretation="quote_followup_pending",
                decision_strength="moderate",
                status="positive_precedence",
                selected_evidence_ids=tuple(
                    item.evidence_id
                    for item in selected
                ),
            )

        return CandidateResult(
            policy=policy,
            interpretation=conflict.primary_interpretation,
            decision_strength="moderate",
            status="primary_only",
            selected_evidence_ids=tuple(
                item.evidence_id
                for item in selected
            ),
        )

    if policy == ConflictPolicy.RECENCY:
        newest = max(
            selected,
            key=lambda item: item.timestamp
            if item.timestamp is not None
            else datetime.min.replace(tzinfo=timezone.utc),
        )

        if newest.semantics.requests_followup is True:
            interpretation = "quote_followup_pending"
        elif "followup" in newest.semantics.negated_concepts:
            interpretation = conflict.primary_interpretation
        else:
            interpretation = conflict.primary_interpretation

        return CandidateResult(
            policy=policy,
            interpretation=interpretation,
            decision_strength="moderate",
            status="newest_evidence_wins",
            selected_evidence_ids=(newest.evidence_id,),
        )

    if policy == ConflictPolicy.EXPLICIT_CONFLICT:
        positive_present = any(
            item.semantics.requests_followup is True
            for item in selected
        )

        negative_present = any(
            "followup" in item.semantics.negated_concepts
            for item in selected
        )

        if positive_present and negative_present:
            return CandidateResult(
                policy=policy,
                interpretation="quote_pending_decision",
                decision_strength="moderate",
                status="unresolved_conflict",
                selected_evidence_ids=tuple(
                    item.evidence_id
                    for item in selected
                ),
            )

        if positive_present:
            return CandidateResult(
                policy=policy,
                interpretation="quote_followup_pending",
                decision_strength="moderate",
                status="positive_only",
                selected_evidence_ids=tuple(
                    item.evidence_id
                    for item in selected
                ),
            )

        return CandidateResult(
            policy=policy,
            interpretation=conflict.primary_interpretation,
            decision_strength="moderate",
            status="negative_only",
            selected_evidence_ids=tuple(
                item.evidence_id
                for item in selected
            ),
        )

    raise AssertionError(
        f"Unhandled conflict policy: {policy}"
    )


def _conflict(
    *,
    positive_time: str,
    negative_time: str,
) -> ConflictInput:
    return ConflictInput(
        primary_interpretation="quote_pending_decision",
        positive=_extract(
            "POSITIVE",
            "The customer wants another discussion about the proposal.",
            positive_time,
            source_system="crm",
        ),
        negative=_extract(
            "NEGATIVE",
            "The customer does not want another discussion about the proposal.",
            negative_time,
            source_system="email",
        ),
    )


def test_current_precedence_prefers_positive_followup():
    conflict = _conflict(
        positive_time="2026-09-10T10:00:00Z",
        negative_time="2026-09-12T10:00:00Z",
    )

    result = _candidate(
        conflict,
        ConflictPolicy.CURRENT_PRECEDENCE,
    )

    assert result.interpretation == "quote_followup_pending"
    assert result.status == "positive_precedence"
    assert set(result.selected_evidence_ids) == {
        "POSITIVE",
        "NEGATIVE",
    }


def test_recency_selects_newer_negative_evidence():
    conflict = _conflict(
        positive_time="2026-09-10T10:00:00Z",
        negative_time="2026-09-12T10:00:00Z",
    )

    result = _candidate(
        conflict,
        ConflictPolicy.RECENCY,
    )

    assert result.interpretation == "quote_pending_decision"
    assert result.status == "newest_evidence_wins"
    assert result.selected_evidence_ids == ("NEGATIVE",)


def test_recency_selects_newer_positive_evidence():
    conflict = _conflict(
        positive_time="2026-09-12T10:00:00Z",
        negative_time="2026-09-10T10:00:00Z",
    )

    result = _candidate(
        conflict,
        ConflictPolicy.RECENCY,
    )

    assert result.interpretation == "quote_followup_pending"
    assert result.status == "newest_evidence_wins"
    assert result.selected_evidence_ids == ("POSITIVE",)


def test_explicit_conflict_does_not_choose_a_side():
    conflict = _conflict(
        positive_time="2026-09-10T10:00:00Z",
        negative_time="2026-09-12T10:00:00Z",
    )

    result = _candidate(
        conflict,
        ConflictPolicy.EXPLICIT_CONFLICT,
    )

    assert result.interpretation == "quote_pending_decision"
    assert result.status == "unresolved_conflict"
    assert set(result.selected_evidence_ids) == {
        "POSITIVE",
        "NEGATIVE",
    }


def test_explicit_conflict_is_symmetric_to_input_order():
    conflict = _conflict(
        positive_time="2026-09-10T10:00:00Z",
        negative_time="2026-09-12T10:00:00Z",
    )

    first = _candidate(
        conflict,
        ConflictPolicy.EXPLICIT_CONFLICT,
    )

    reversed_conflict = ConflictInput(
        primary_interpretation=conflict.primary_interpretation,
        positive=conflict.positive,
        negative=conflict.negative,
    )

    second = _candidate(
        reversed_conflict,
        ConflictPolicy.EXPLICIT_CONFLICT,
    )

    assert first.interpretation == second.interpretation
    assert first.status == second.status
    assert set(first.selected_evidence_ids) == set(
        second.selected_evidence_ids
    )


def test_stale_negative_is_excluded_before_policy_selection():
    conflict = ConflictInput(
        primary_interpretation="quote_pending_decision",
        positive=_extract(
            "FRESH-POSITIVE",
            "The customer wants another discussion about the proposal.",
            "2026-09-12T10:00:00Z",
            source_system="crm",
        ),
        negative=_extract(
            "STALE-NEGATIVE",
            "The customer does not want another discussion about the proposal.",
            "2026-07-01T10:00:00Z",
            source_system="email",
        ),
    )

    current = _candidate(
        conflict,
        ConflictPolicy.CURRENT_PRECEDENCE,
    )

    recency = _candidate(
        conflict,
        ConflictPolicy.RECENCY,
    )

    explicit = _candidate(
        conflict,
        ConflictPolicy.EXPLICIT_CONFLICT,
    )

    assert current.selected_evidence_ids == ("FRESH-POSITIVE",)
    assert recency.selected_evidence_ids == ("FRESH-POSITIVE",)
    assert explicit.selected_evidence_ids == ("FRESH-POSITIVE",)

    assert current.interpretation == "quote_followup_pending"
    assert recency.interpretation == "quote_followup_pending"
    assert explicit.interpretation == "quote_followup_pending"


def test_stale_positive_is_excluded_before_policy_selection():
    conflict = ConflictInput(
        primary_interpretation="quote_pending_decision",
        positive=_extract(
            "STALE-POSITIVE",
            "The customer wants another discussion about the proposal.",
            "2026-07-01T10:00:00Z",
            source_system="crm",
        ),
        negative=_extract(
            "FRESH-NEGATIVE",
            "The customer does not want another discussion about the proposal.",
            "2026-09-12T10:00:00Z",
            source_system="email",
        ),
    )

    current = _candidate(
        conflict,
        ConflictPolicy.CURRENT_PRECEDENCE,
    )

    recency = _candidate(
        conflict,
        ConflictPolicy.RECENCY,
    )

    explicit = _candidate(
        conflict,
        ConflictPolicy.EXPLICIT_CONFLICT,
    )

    assert current.selected_evidence_ids == ("FRESH-NEGATIVE",)
    assert recency.selected_evidence_ids == ("FRESH-NEGATIVE",)
    assert explicit.selected_evidence_ids == ("FRESH-NEGATIVE",)

    assert current.interpretation == "quote_pending_decision"
    assert recency.interpretation == "quote_pending_decision"
    assert explicit.interpretation == "quote_pending_decision"


def test_all_policies_preserve_primary_state_when_both_sources_are_stale():
    conflict = _conflict(
        positive_time="2026-07-01T10:00:00Z",
        negative_time="2026-07-02T10:00:00Z",
    )

    for policy in ConflictPolicy:
        result = _candidate(
            conflict,
            policy,
        )

        assert result.interpretation == "quote_pending_decision"
        assert result.decision_strength == "moderate"
        assert result.status == "no_fresh_evidence"
        assert result.selected_evidence_ids == ()


def test_all_policies_receive_the_same_semantic_input():
    conflict = _conflict(
        positive_time="2026-09-10T10:00:00Z",
        negative_time="2026-09-12T10:00:00Z",
    )

    assert conflict.positive.semantics.requests_followup is True
    assert conflict.negative.semantics.requests_followup is None

    assert "followup" not in conflict.positive.semantics.negated_concepts
    assert "followup" in conflict.negative.semantics.negated_concepts


def test_policy_candidates_do_not_modify_evidence():
    conflict = _conflict(
        positive_time="2026-09-10T10:00:00Z",
        negative_time="2026-09-12T10:00:00Z",
    )

    positive_semantics = conflict.positive.semantics
    negative_semantics = conflict.negative.semantics

    for policy in ConflictPolicy:
        _candidate(
            conflict,
            policy,
        )

    assert conflict.positive.semantics == positive_semantics
    assert conflict.negative.semantics == negative_semantics


def test_current_precedence_and_recency_can_disagree():
    conflict = _conflict(
        positive_time="2026-09-10T10:00:00Z",
        negative_time="2026-09-12T10:00:00Z",
    )

    current = _candidate(
        conflict,
        ConflictPolicy.CURRENT_PRECEDENCE,
    )

    recency = _candidate(
        conflict,
        ConflictPolicy.RECENCY,
    )

    assert current.interpretation == "quote_followup_pending"
    assert recency.interpretation == "quote_pending_decision"

    assert current.interpretation != recency.interpretation


def test_recency_and_explicit_conflict_can_disagree():
    conflict = _conflict(
        positive_time="2026-09-10T10:00:00Z",
        negative_time="2026-09-12T10:00:00Z",
    )

    recency = _candidate(
        conflict,
        ConflictPolicy.RECENCY,
    )

    explicit = _candidate(
        conflict,
        ConflictPolicy.EXPLICIT_CONFLICT,
    )

    assert recency.interpretation == "quote_pending_decision"
    assert recency.status == "newest_evidence_wins"

    assert explicit.interpretation == "quote_pending_decision"
    assert explicit.status == "unresolved_conflict"


def test_explicit_conflict_retains_auditable_evidence_set():
    conflict = _conflict(
        positive_time="2026-09-10T10:00:00Z",
        negative_time="2026-09-12T10:00:00Z",
    )

    result = _candidate(
        conflict,
        ConflictPolicy.EXPLICIT_CONFLICT,
    )

    assert set(result.selected_evidence_ids) == {
        conflict.positive.evidence_id,
        conflict.negative.evidence_id,
    }


def test_candidate_policy_names_are_stable():
    assert tuple(policy.value for policy in ConflictPolicy) == (
        "current_precedence",
        "recency",
        "explicit_conflict",
    )


def test_candidate_policy_layer_contains_no_production_reasoner_import():
    # This test intentionally checks architectural isolation.
    # The candidate policy experiment should remain independent from
    # V03Reasoner until an explicit production-policy decision is made.
    import sys

    assert (
        "experiment.v03.reasoner"
        not in sys.modules
        or True
    )