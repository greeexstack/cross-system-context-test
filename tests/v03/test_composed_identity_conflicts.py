from __future__ import annotations

from dataclasses import dataclass

from experiment.v03.evidence import (
    EvidenceIdentity,
    IdentityQuality,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class IdentityContribution:
    evidence_id: str
    customer_id: str | None
    quality: IdentityQuality


@dataclass(frozen=True)
class IdentityConflict:
    contributors: tuple[IdentityContribution, ...]
    resolved_customer_id: str | None
    resolved_quality: IdentityQuality

    @classmethod
    def from_items(
        cls,
        items,
    ) -> "IdentityConflict":
        contributors = tuple(
            IdentityContribution(
                evidence_id=item.evidence_id,
                customer_id=item.identity.customer_id,
                quality=item.identity.quality,
            )
            for item in items
        )

        confirmed_ids = {
            item.identity.customer_id
            for item in items
            if (
                item.identity.quality == IdentityQuality.CONFIRMED
                and item.identity.customer_id is not None
            )
        }

        if len(confirmed_ids) == 1:
            customer_id = next(iter(confirmed_ids))
            quality = IdentityQuality.CONFIRMED
        elif len(confirmed_ids) > 1:
            customer_id = None
            quality = IdentityQuality.AMBIGUOUS
        else:
            customer_id = None
            quality = IdentityQuality.AMBIGUOUS

        return cls(
            contributors=contributors,
            resolved_customer_id=customer_id,
            resolved_quality=quality,
        )


def _extract(
    evidence_id: str,
    customer_id: str | None,
    quality: IdentityQuality,
):
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content="The customer wants another discussion about the proposal.",
        source_system="test",
        record_id=evidence_id,
        occurred_at="2026-09-12T10:00:00Z",
        customer_id=customer_id,
        identity_quality=quality,
    ).evidence


def test_single_confirmed_identity_remains_confirmed():
    evidence = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    result = IdentityConflict.from_items(
        (evidence,),
    )

    assert result.resolved_customer_id == "C001"
    assert result.resolved_quality == IdentityQuality.CONFIRMED


def test_same_confirmed_identity_from_two_sources_remains_confirmed():
    first = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    second = _extract(
        "B",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    result = IdentityConflict.from_items(
        (
            first,
            second,
        ),
    )

    assert result.resolved_customer_id == "C001"
    assert result.resolved_quality == IdentityQuality.CONFIRMED


def test_different_confirmed_customer_ids_create_identity_conflict():
    first = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    second = _extract(
        "B",
        "C002",
        IdentityQuality.CONFIRMED,
    )

    result = IdentityConflict.from_items(
        (
            first,
            second,
        ),
    )

    assert result.resolved_customer_id is None
    assert result.resolved_quality == IdentityQuality.AMBIGUOUS


def test_identity_conflict_retains_both_customer_ids():
    first = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    second = _extract(
        "B",
        "C002",
        IdentityQuality.CONFIRMED,
    )

    result = IdentityConflict.from_items(
        (
            first,
            second,
        ),
    )

    assert {
        contributor.customer_id
        for contributor in result.contributors
    } == {
        "C001",
        "C002",
    }


def test_ambiguous_contributor_does_not_override_confirmed_identity():
    confirmed = _extract(
        "CONFIRMED",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    ambiguous = _extract(
        "AMBIGUOUS",
        "C001",
        IdentityQuality.AMBIGUOUS,
    )

    result = IdentityConflict.from_items(
        (
            confirmed,
            ambiguous,
        ),
    )

    assert result.resolved_customer_id == "C001"
    assert result.resolved_quality == IdentityQuality.CONFIRMED


def test_no_match_contributor_does_not_override_confirmed_identity():
    confirmed = _extract(
        "CONFIRMED",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    no_match = _extract(
        "NO-MATCH",
        "C999",
        IdentityQuality.NO_MATCH,
    )

    result = IdentityConflict.from_items(
        (
            confirmed,
            no_match,
        ),
    )

    assert result.resolved_customer_id == "C001"
    assert result.resolved_quality == IdentityQuality.CONFIRMED


def test_only_ambiguous_identity_does_not_create_confirmed_identity():
    ambiguous = _extract(
        "AMBIGUOUS",
        "C001",
        IdentityQuality.AMBIGUOUS,
    )

    result = IdentityConflict.from_items(
        (ambiguous,),
    )

    assert result.resolved_customer_id is None
    assert result.resolved_quality == IdentityQuality.AMBIGUOUS


def test_only_no_match_identity_does_not_create_confirmed_identity():
    no_match = _extract(
        "NO-MATCH",
        "C999",
        IdentityQuality.NO_MATCH,
    )

    result = IdentityConflict.from_items(
        (no_match,),
    )

    assert result.resolved_customer_id is None
    assert result.resolved_quality == IdentityQuality.AMBIGUOUS


def test_confirmed_and_ambiguous_different_customer_ids_remain_confirmed():
    confirmed = _extract(
        "CONFIRMED",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    ambiguous = _extract(
        "AMBIGUOUS",
        "C002",
        IdentityQuality.AMBIGUOUS,
    )

    result = IdentityConflict.from_items(
        (
            confirmed,
            ambiguous,
        ),
    )

    # The ambiguous record does not establish a competing confirmed
    # identity, so it must not manufacture a conflict.
    assert result.resolved_customer_id == "C001"
    assert result.resolved_quality == IdentityQuality.CONFIRMED


def test_two_confirmed_same_customer_preserve_contributor_traceability():
    first = _extract(
        "CRM",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    second = _extract(
        "EMAIL",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    result = IdentityConflict.from_items(
        (
            first,
            second,
        ),
    )

    assert result.contributors == (
        IdentityContribution(
            evidence_id="CRM",
            customer_id="C001",
            quality=IdentityQuality.CONFIRMED,
        ),
        IdentityContribution(
            evidence_id="EMAIL",
            customer_id="C001",
            quality=IdentityQuality.CONFIRMED,
        ),
    )


def test_conflicting_confirmed_identities_preserve_contributor_quality():
    first = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    second = _extract(
        "B",
        "C002",
        IdentityQuality.CONFIRMED,
    )

    result = IdentityConflict.from_items(
        (
            first,
            second,
        ),
    )

    assert {
        contributor.quality
        for contributor in result.contributors
    } == {
        IdentityQuality.CONFIRMED,
    }


def test_identity_conflict_does_not_select_first_customer():
    first = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    second = _extract(
        "B",
        "C002",
        IdentityQuality.CONFIRMED,
    )

    result = IdentityConflict.from_items(
        (
            first,
            second,
        ),
    )

    assert result.resolved_customer_id != "C001"
    assert result.resolved_customer_id != "C002"


def test_identity_conflict_does_not_select_last_customer():
    first = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    second = _extract(
        "B",
        "C002",
        IdentityQuality.CONFIRMED,
    )

    result = IdentityConflict.from_items(
        (
            first,
            second,
        ),
    )

    assert result.resolved_customer_id != "C002"


def test_identity_conflict_is_symmetric_to_input_order():
    first = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    second = _extract(
        "B",
        "C002",
        IdentityQuality.CONFIRMED,
    )

    forward = IdentityConflict.from_items(
        (
            first,
            second,
        ),
    )

    reverse = IdentityConflict.from_items(
        (
            second,
            first,
        ),
    )

    assert forward.resolved_customer_id == (
        reverse.resolved_customer_id
    )

    assert forward.resolved_quality == (
        reverse.resolved_quality
    )

    assert {
        contributor.customer_id
        for contributor in forward.contributors
    } == {
        contributor.customer_id
        for contributor in reverse.contributors
    }


def test_identity_conflict_is_deterministic():
    first = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    second = _extract(
        "B",
        "C002",
        IdentityQuality.CONFIRMED,
    )

    first_result = IdentityConflict.from_items(
        (
            first,
            second,
        ),
    )

    second_result = IdentityConflict.from_items(
        (
            first,
            second,
        ),
    )

    assert first_result == second_result


def test_identity_conflict_does_not_mutate_source_identity():
    first = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    second = _extract(
        "B",
        "C002",
        IdentityQuality.CONFIRMED,
    )

    first_identity = first.identity
    second_identity = second.identity

    result = IdentityConflict.from_items(
        (
            first,
            second,
        ),
    )

    assert result.resolved_quality == IdentityQuality.AMBIGUOUS

    assert first.identity == first_identity
    assert second.identity == second_identity


def test_identity_conflict_has_no_benchmark_policy():
    first = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    second = _extract(
        "B",
        "C002",
        IdentityQuality.CONFIRMED,
    )

    result = IdentityConflict.from_items(
        (
            first,
            second,
        ),
    )

    assert not hasattr(
        result,
        "winner",
    )

    assert not hasattr(
        result,
        "priority",
    )

    assert not hasattr(
        result,
        "expected_direction",
    )


def test_identity_conflict_representation_is_separate_from_semantics():
    first = _extract(
        "A",
        "C001",
        IdentityQuality.CONFIRMED,
    )

    result = IdentityConflict.from_items(
        (first,),
    )

    assert result.resolved_customer_id == "C001"
    assert result.contributors[0].evidence_id == "A"