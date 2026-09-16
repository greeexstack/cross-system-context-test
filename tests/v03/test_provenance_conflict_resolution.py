from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)


@dataclass(frozen=True)
class ConflictContribution:
    concept: str
    polarity: str
    evidence_id: str
    source_system: str
    occurred_at: datetime


@dataclass(frozen=True)
class ConflictRecord:
    contributions: tuple[ConflictContribution, ...]

    @property
    def positive_followup_ids(self) -> frozenset[str]:
        return frozenset(
            item.evidence_id
            for item in self.contributions
            if (
                item.concept == "followup"
                and item.polarity == "positive"
            )
        )

    @property
    def negative_followup_ids(self) -> frozenset[str]:
        return frozenset(
            item.evidence_id
            for item in self.contributions
            if (
                item.concept == "followup"
                and item.polarity == "negative"
            )
        )

    @property
    def has_followup_conflict(self) -> bool:
        return bool(
            self.positive_followup_ids
            and self.negative_followup_ids
        )

    @classmethod
    def from_items(
        cls,
        items: tuple[SemanticEvidence, ...],
    ) -> "ConflictRecord":
        contributions: list[ConflictContribution] = []

        for item in items:
            if item.identity.quality != IdentityQuality.CONFIRMED:
                continue

            timestamp = item.timestamp

            if timestamp is None:
                continue

            if not _is_fresh(timestamp):
                continue

            if item.semantics.concerns_same_work_item is False:
                continue

            if (
                item.semantics.requests_followup is True
                and "followup"
                not in item.semantics.negated_concepts
            ):
                contributions.append(
                    ConflictContribution(
                        concept="followup",
                        polarity="positive",
                        evidence_id=item.evidence_id,
                        source_system=item.provenance.source_system,
                        occurred_at=timestamp,
                    )
                )

            if "followup" in item.semantics.negated_concepts:
                contributions.append(
                    ConflictContribution(
                        concept="followup",
                        polarity="negative",
                        evidence_id=item.evidence_id,
                        source_system=item.provenance.source_system,
                        occurred_at=timestamp,
                    )
                )

        return cls(
            contributions=tuple(contributions),
        )


def _is_fresh(timestamp: datetime) -> bool:
    when = timestamp

    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)

    return (
        EVALUATION_AT - when
        <= timedelta(days=30)
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


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _condition(
    *items: SemanticEvidence,
):
    from experiment.v03.evidence import EvidenceCondition

    return EvidenceCondition(
        availability="available",
        items=tuple(items),
    )


def test_conflicting_sources_keep_both_contributors():
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

    conflict = ConflictRecord.from_items(
        (
            positive,
            negative,
        ),
    )

    assert conflict.has_followup_conflict is True

    assert conflict.positive_followup_ids == {
        "CRM-POSITIVE",
    }

    assert conflict.negative_followup_ids == {
        "EMAIL-NEGATIVE",
    }


def test_conflict_provenance_preserves_source_systems():
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

    conflict = ConflictRecord.from_items(
        (
            positive,
            negative,
        ),
    )

    assert {
        contribution.source_system
        for contribution in conflict.contributions
    } == {
        "crm",
        "email",
    }


def test_conflict_provenance_preserves_timestamps():
    positive = _extract(
        "OLDER-POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    negative = _extract(
        "NEWER-NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    conflict = ConflictRecord.from_items(
        (
            positive,
            negative,
        ),
    )

    by_id = {
        contribution.evidence_id: contribution
        for contribution in conflict.contributions
    }

    assert by_id["OLDER-POSITIVE"].occurred_at == datetime(
        2026,
        9,
        10,
        10,
        0,
        tzinfo=timezone.utc,
    )

    assert by_id["NEWER-NEGATIVE"].occurred_at == datetime(
        2026,
        9,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )


def test_provenance_records_disagreement_without_selecting_winner():
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

    conflict = ConflictRecord.from_items(
        (
            positive,
            negative,
        ),
    )

    assert conflict.has_followup_conflict is True
    assert len(conflict.positive_followup_ids) == 1
    assert len(conflict.negative_followup_ids) == 1


def test_existing_reasoner_still_uses_current_followup_precedence():
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

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            positive,
            negative,
        ),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_newer_negative_does_not_change_current_reasoner_precedence():
    newer_negative = _extract(
        "NEWER-NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    older_positive = _extract(
        "OLDER-POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            newer_negative,
            older_positive,
        ),
    )

    assert result.interpretation_class == "quote_followup_pending"


def test_stale_contributor_is_absent_from_conflict_provenance():
    fresh_positive = _extract(
        "FRESH-POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    stale_negative = _extract(
        "STALE-NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-07-01T10:00:00Z",
    )

    conflict = ConflictRecord.from_items(
        (
            fresh_positive,
            stale_negative,
        ),
    )

    assert conflict.has_followup_conflict is False

    assert conflict.contributions == (
        ConflictContribution(
            concept="followup",
            polarity="positive",
            evidence_id="FRESH-POSITIVE",
            source_system="crm",
            occurred_at=fresh_positive.timestamp,
        ),
    )


def test_wrong_identity_is_absent_from_conflict_provenance():
    valid_positive = _extract(
        "VALID-POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    wrong_identity_negative = _extract(
        "WRONG-IDENTITY-NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T11:00:00Z",
        identity_quality=IdentityQuality.NO_MATCH,
        customer_id="C999",
    )

    conflict = ConflictRecord.from_items(
        (
            valid_positive,
            wrong_identity_negative,
        ),
    )

    assert conflict.has_followup_conflict is False

    assert conflict.contributions == (
        ConflictContribution(
            concept="followup",
            polarity="positive",
            evidence_id="VALID-POSITIVE",
            source_system="crm",
            occurred_at=valid_positive.timestamp,
        ),
    )


def test_ambiguous_identity_is_absent_from_conflict_provenance():
    valid_negative = _extract(
        "VALID-NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    ambiguous_positive = _extract(
        "AMBIGUOUS-POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T11:00:00Z",
        identity_quality=IdentityQuality.AMBIGUOUS,
    )

    conflict = ConflictRecord.from_items(
        (
            valid_negative,
            ambiguous_positive,
        ),
    )

    assert conflict.has_followup_conflict is False

    assert conflict.contributions == (
        ConflictContribution(
            concept="followup",
            polarity="negative",
            evidence_id="VALID-NEGATIVE",
            source_system="email",
            occurred_at=valid_negative.timestamp,
        ),
    )


def test_irrelevant_contributor_is_absent_from_conflict_provenance():
    valid_positive = _extract(
        "VALID-POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    irrelevant = _extract(
        "IRRELEVANT",
        "email",
        "The customer is discussing a separate store rollout "
        "and says nothing about this opportunity.",
        "2026-09-12T11:00:00Z",
    )

    conflict = ConflictRecord.from_items(
        (
            valid_positive,
            irrelevant,
        ),
    )

    assert conflict.has_followup_conflict is False

    assert {
        contribution.evidence_id
        for contribution in conflict.contributions
    } == {"VALID-POSITIVE"}


def test_negated_followup_is_recorded_as_negative_contribution():
    negative = _extract(
        "NEGATIVE-FOLLOWUP",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    conflict = ConflictRecord.from_items(
        (negative,),
    )

    assert conflict.contributions == (
        ConflictContribution(
            concept="followup",
            polarity="negative",
            evidence_id="NEGATIVE-FOLLOWUP",
            source_system="email",
            occurred_at=negative.timestamp,
        ),
    )


def test_three_way_conflict_retains_all_provenance():
    positive_1 = _extract(
        "POSITIVE-1",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    positive_2 = _extract(
        "POSITIVE-2",
        "support",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    conflict = ConflictRecord.from_items(
        (
            positive_1,
            negative,
            positive_2,
        ),
    )

    assert conflict.has_followup_conflict is True

    assert conflict.positive_followup_ids == {
        "POSITIVE-1",
        "POSITIVE-2",
    }

    assert conflict.negative_followup_ids == {
        "NEGATIVE",
    }

    assert {
        contribution.source_system
        for contribution in conflict.contributions
    } == {
        "crm",
        "email",
        "support",
    }


def test_input_order_does_not_change_conflict_membership():
    positive = _extract(
        "POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    forward = ConflictRecord.from_items(
        (
            positive,
            negative,
        ),
    )

    reverse = ConflictRecord.from_items(
        (
            negative,
            positive,
        ),
    )

    assert forward.has_followup_conflict == reverse.has_followup_conflict
    assert forward.positive_followup_ids == reverse.positive_followup_ids
    assert forward.negative_followup_ids == reverse.negative_followup_ids


def test_conflict_provenance_is_deterministic():
    positive = _extract(
        "POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    first = ConflictRecord.from_items(
        (
            positive,
            negative,
        ),
    )

    second = ConflictRecord.from_items(
        (
            positive,
            negative,
        ),
    )

    assert first == second


def test_conflict_record_does_not_mutate_source_evidence():
    positive = _extract(
        "POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    positive_before = positive.semantics
    negative_before = negative.semantics
    positive_provenance = positive.provenance
    negative_provenance = negative.provenance

    conflict = ConflictRecord.from_items(
        (
            positive,
            negative,
        ),
    )

    assert conflict.has_followup_conflict is True

    assert positive.semantics == positive_before
    assert negative.semantics == negative_before
    assert positive.provenance == positive_provenance
    assert negative.provenance == negative_provenance


def test_conflict_provenance_has_no_benchmark_policy():
    positive = _extract(
        "POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
        "2026-09-11T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    conflict = ConflictRecord.from_items(
        (
            positive,
            negative,
        ),
    )

    for contribution in conflict.contributions:
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
            "winner",
        )

        assert not hasattr(
            contribution,
            "priority",
        )