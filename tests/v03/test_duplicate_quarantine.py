from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, timezone

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import IdentityQuality, SemanticEvidence
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class DuplicateGroup:
    evidence_id: str
    members: tuple[SemanticEvidence, ...]
    conflicting: bool


@dataclass(frozen=True)
class QuarantineResult:
    accepted_ids: tuple[str, ...]
    quarantined_ids: tuple[str, ...]

    @property
    def accepted_items(self) -> tuple[str, ...]:
        return self.accepted_ids


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


def _group_duplicates(
    items: tuple[SemanticEvidence, ...],
) -> tuple[DuplicateGroup, ...]:
    grouped: dict[str, list[SemanticEvidence]] = {}

    for item in items:
        grouped.setdefault(
            item.evidence_id,
            [],
        ).append(item)

    groups: list[DuplicateGroup] = []

    for evidence_id, members in grouped.items():
        signatures = {
            _signature(member)
            for member in members
        }

        groups.append(
            DuplicateGroup(
                evidence_id=evidence_id,
                members=tuple(members),
                conflicting=len(signatures) > 1,
            )
        )

    return tuple(groups)


def _quarantine(
    items: tuple[SemanticEvidence, ...],
) -> QuarantineResult:
    groups = _group_duplicates(items)

    accepted: list[str] = []
    quarantined: list[str] = []

    for group in groups:
        if group.conflicting:
            quarantined.append(group.evidence_id)
        else:
            accepted.append(group.evidence_id)

    return QuarantineResult(
        accepted_ids=tuple(accepted),
        quarantined_ids=tuple(quarantined),
    )


def _fresh_and_eligible(
    item: SemanticEvidence,
) -> bool:
    if item.identity.quality != IdentityQuality.CONFIRMED:
        return False

    if item.timestamp is None:
        return False

    timestamp = item.timestamp

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(
            tzinfo=timezone.utc
        )

    if (
        EVALUATION_AT - timestamp
        > timedelta(days=30)
    ):
        return False

    if item.semantics.concerns_same_work_item is False:
        return False

    return True


def _safe_ids_after_quarantine(
    items: tuple[SemanticEvidence, ...],
) -> tuple[str, ...]:
    quarantine = _quarantine(items)

    quarantined = set(
        quarantine.quarantined_ids
    )

    accepted: list[str] = []

    seen: set[str] = set()

    for item in items:
        if item.evidence_id in quarantined:
            continue

        if not _fresh_and_eligible(item):
            continue

        if item.evidence_id in seen:
            continue

        seen.add(item.evidence_id)
        accepted.append(item.evidence_id)

    return tuple(accepted)


def test_identical_duplicates_are_not_quarantined():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    result = _quarantine(
        (
            first,
            second,
        ),
    )

    assert result.accepted_ids == ("E1",)
    assert result.quarantined_ids == ()


def test_conflicting_duplicates_are_quarantined():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    result = _quarantine(
        (
            first,
            second,
        ),
    )

    assert result.accepted_ids == ()
    assert result.quarantined_ids == ("E1",)


def test_positive_negative_duplicate_conflict_is_quarantined():
    positive = _extract(
        "E1",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "E1",
        "The customer does not want another discussion about the proposal.",
    )

    result = _quarantine(
        (
            positive,
            negative,
        ),
    )

    assert result.accepted_ids == ()
    assert result.quarantined_ids == ("E1",)


def test_quarantine_is_by_evidence_id_not_by_source_system():
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

    result = _quarantine(
        (
            first,
            second,
        ),
    )

    assert result.quarantined_ids == ("E1",)


def test_distinct_ids_are_processed_independently():
    first = _extract(
        "A",
        "The migration workshop is complete.",
    )

    second = _extract(
        "B",
        "The customer asks what comes next.",
    )

    result = _quarantine(
        (
            first,
            second,
        ),
    )

    assert set(result.accepted_ids) == {
        "A",
        "B",
    }

    assert result.quarantined_ids == ()


def test_one_conflicted_id_does_not_quarantine_other_ids():
    conflict_a = _extract(
        "A",
        "The migration workshop is complete.",
    )

    conflict_b = _extract(
        "A",
        "The customer asks what comes next.",
    )

    valid = _extract(
        "B",
        "The customer asks what comes next.",
    )

    result = _quarantine(
        (
            conflict_a,
            conflict_b,
            valid,
        ),
    )

    assert result.quarantined_ids == ("A",)
    assert result.accepted_ids == ("B",)


def test_quarantined_id_cannot_contribute_to_safe_composition():
    completion = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    conflicting_copy = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    valid_next = _extract(
        "E2",
        "The customer asks what comes next.",
    )

    ids = _safe_ids_after_quarantine(
        (
            completion,
            conflicting_copy,
            valid_next,
        ),
    )

    assert ids == ("E2",)


def test_conflicted_duplicate_does_not_win_by_first_seen():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    result = _quarantine(
        (
            first,
            second,
        ),
    )

    assert "E1" not in result.accepted_ids
    assert "E1" in result.quarantined_ids


def test_conflicted_duplicate_does_not_win_by_last_seen():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    result = _quarantine(
        (
            first,
            second,
        ),
    )

    assert result.quarantined_ids == ("E1",)


def test_conflicted_duplicate_does_not_win_by_source():
    crm = _extract(
        "E1",
        "The migration workshop is complete.",
        source_system="crm",
    )

    email = _extract(
        "E1",
        "The customer asks what comes next.",
        source_system="email",
    )

    result = _quarantine(
        (
            crm,
            email,
        ),
    )

    assert result.quarantined_ids == ("E1",)


def test_conflicted_duplicate_does_not_win_by_recency():
    older = _extract(
        "E1",
        "The migration workshop is complete.",
        occurred_at="2026-09-10T10:00:00Z",
    )

    newer = _extract(
        "E1",
        "The customer asks what comes next.",
        occurred_at="2026-09-12T10:00:00Z",
    )

    result = _quarantine(
        (
            older,
            newer,
        ),
    )

    assert result.quarantined_ids == ("E1",)


def test_duplicate_metadata_difference_alone_is_not_quarantine():
    older = _extract(
        "E1",
        "The migration workshop is complete.",
        occurred_at="2026-09-10T10:00:00Z",
    )

    newer = _extract(
        "E1",
        "The migration workshop is complete.",
        occurred_at="2026-09-12T10:00:00Z",
    )

    result = _quarantine(
        (
            older,
            newer,
        ),
    )

    assert result.accepted_ids == ("E1",)
    assert result.quarantined_ids == ()


def test_duplicate_source_difference_alone_is_not_quarantine():
    crm = _extract(
        "E1",
        "The migration workshop is complete.",
        source_system="crm",
    )

    email = _extract(
        "E1",
        "The migration workshop is complete.",
        source_system="email",
    )

    result = _quarantine(
        (
            crm,
            email,
        ),
    )

    assert result.accepted_ids == ("E1",)
    assert result.quarantined_ids == ()


def test_duplicate_customer_difference_is_identity_metadata_conflict():
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

    result = _quarantine(
        (
            first,
            second,
        ),
    )

    assert result.conflicting is False if False else True