from __future__ import annotations

from dataclasses import dataclass

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    EvidenceCondition,
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class FactContribution:
    concept: str
    evidence_id: str


@dataclass(frozen=True)
class ProvenancedComposition:
    confirms_completion: bool
    requests_next_step: bool
    contributions: tuple[FactContribution, ...]

    @classmethod
    def from_items(
        cls,
        items: tuple[SemanticEvidence, ...],
    ) -> "ProvenancedComposition":
        eligible = tuple(
            item
            for item in items
            if item.identity.quality == IdentityQuality.CONFIRMED
            and item.timestamp is not None
            and _is_fresh(item)
            and item.semantics.concerns_same_work_item is not False
        )

        contributions: list[FactContribution] = []

        completion_items = tuple(
            item
            for item in eligible
            if (
                item.semantics.confirms_completion is True
                and "completion"
                not in item.semantics.negated_concepts
            )
        )

        next_step_items = tuple(
            item
            for item in eligible
            if (
                item.semantics.requests_next_step is True
                and "next_step"
                not in item.semantics.negated_concepts
            )
        )

        for item in completion_items:
            contributions.append(
                FactContribution(
                    concept="completion",
                    evidence_id=item.evidence_id,
                )
            )

        for item in next_step_items:
            contributions.append(
                FactContribution(
                    concept="next_step",
                    evidence_id=item.evidence_id,
                )
            )

        return cls(
            confirms_completion=bool(completion_items),
            requests_next_step=bool(next_step_items),
            contributions=tuple(contributions),
        )


def _is_fresh(item: SemanticEvidence) -> bool:
    timestamp = item.timestamp

    if timestamp is None:
        return False

    when = timestamp

    if when.tzinfo is None:
        from datetime import timezone

        when = when.replace(tzinfo=timezone.utc)

    from datetime import timedelta

    return (
        EVALUATION_AT - when
        <= timedelta(days=30)
    )


def _extract(
    evidence_id: str,
    text: str,
    *,
    occurred_at: str = "2026-09-12T10:00:00Z",
    customer_id: str | None = "C001",
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


def test_completion_contribution_identifies_source_record():
    completion = _extract(
        "CRM-COMPLETION",
        "The migration workshop is complete.",
    )

    composed = ProvenancedComposition.from_items(
        (completion,),
    )

    assert composed.confirms_completion is True

    assert composed.contributions == (
        FactContribution(
            concept="completion",
            evidence_id="CRM-COMPLETION",
        ),
    )


def test_next_step_contribution_identifies_source_record():
    next_step = _extract(
        "EMAIL-NEXT",
        "The customer asks what comes next.",
    )

    composed = ProvenancedComposition.from_items(
        (next_step,),
    )

    assert composed.requests_next_step is True

    assert composed.contributions == (
        FactContribution(
            concept="next_step",
            evidence_id="EMAIL-NEXT",
        ),
    )


def test_cross_record_composition_retains_both_contributors():
    completion = _extract(
        "CRM-COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "EMAIL-NEXT",
        "The customer asks what comes next.",
    )

    composed = ProvenancedComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True

    assert set(composed.contributions) == {
        FactContribution(
            concept="completion",
            evidence_id="CRM-COMPLETION",
        ),
        FactContribution(
            concept="next_step",
            evidence_id="EMAIL-NEXT",
        ),
    }


def test_duplicate_contributors_remain_traceable():
    first = _extract(
        "CRM-COMPLETION",
        "The migration workshop is complete.",
    )

    second = _extract(
        "EMAIL-COMPLETION",
        "The migration workshop is complete.",
    )

    composed = ProvenancedComposition.from_items(
        (
            first,
            second,
        ),
    )

    assert composed.confirms_completion is True

    completion_contributors = tuple(
        contribution.evidence_id
        for contribution in composed.contributions
        if contribution.concept == "completion"
    )

    assert set(completion_contributors) == {
        "CRM-COMPLETION",
        "EMAIL-COMPLETION",
    }


def test_wrong_identity_has_no_contribution_provenance():
    valid_completion = _extract(
        "VALID-COMPLETION",
        "The migration workshop is complete.",
    )

    wrong_identity_next = _extract(
        "WRONG-NEXT",
        "The customer asks what comes next.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    composed = ProvenancedComposition.from_items(
        (
            valid_completion,
            wrong_identity_next,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False

    assert composed.contributions == (
        FactContribution(
            concept="completion",
            evidence_id="VALID-COMPLETION",
        ),
    )


def test_stale_evidence_has_no_contribution_provenance():
    valid_next = _extract(
        "VALID-NEXT",
        "The customer asks what comes next.",
    )

    stale_completion = _extract(
        "STALE-COMPLETION",
        "The migration workshop is complete.",
        occurred_at="2026-07-01T10:00:00Z",
    )

    composed = ProvenancedComposition.from_items(
        (
            valid_next,
            stale_completion,
        ),
    )

    assert composed.confirms_completion is False
    assert composed.requests_next_step is True

    assert composed.contributions == (
        FactContribution(
            concept="next_step",
            evidence_id="VALID-NEXT",
        ),
    )


def test_negated_fact_has_no_positive_contribution_provenance():
    negated_completion = _extract(
        "NEGATED-COMPLETION",
        "The migration workshop is not complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed = ProvenancedComposition.from_items(
        (
            negated_completion,
            next_step,
        ),
    )

    assert composed.confirms_completion is False
    assert composed.requests_next_step is True

    assert composed.contributions == (
        FactContribution(
            concept="next_step",
            evidence_id="NEXT-STEP",
        ),
    )


def test_irrelevant_evidence_has_no_contribution_provenance():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    irrelevant = _extract(
        "IRRELEVANT",
        "The customer is discussing a separate store rollout "
        "and says nothing about this opportunity.",
    )

    composed = ProvenancedComposition.from_items(
        (
            completion,
            irrelevant,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False

    assert composed.contributions == (
        FactContribution(
            concept="completion",
            evidence_id="COMPLETION",
        ),
    )


def test_contributor_order_is_deterministic_for_same_input_order():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    first = ProvenancedComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    second = ProvenancedComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert first == second


def test_reversing_input_order_preserves_the_same_contributor_set():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    first = ProvenancedComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    second = ProvenancedComposition.from_items(
        (
            next_step,
            completion,
        ),
    )

    assert first.confirms_completion == second.confirms_completion
    assert first.requests_next_step == second.requests_next_step

    assert set(first.contributions) == set(second.contributions)


def test_provenance_does_not_mutate_original_evidence():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    completion_before = completion.semantics
    next_before = next_step.semantics

    composed = ProvenancedComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True

    assert completion.semantics == completion_before
    assert next_step.semantics == next_before


def test_provenance_does_not_change_factual_semantics():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed = ProvenancedComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert completion.semantics.confirms_completion is True
    assert completion.semantics.requests_next_step is None

    assert next_step.semantics.confirms_completion is None
    assert next_step.semantics.requests_next_step is True

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True


def test_evidence_condition_still_preserves_original_records():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    condition = EvidenceCondition(
        availability="available",
        items=(
            completion,
            next_step,
        ),
    )

    composed = ProvenancedComposition.from_items(
        condition.items,
    )

    assert len(condition.items) == 2
    assert condition.items[0].evidence_id == "COMPLETION"
    assert condition.items[1].evidence_id == "NEXT-STEP"

    assert set(composed.contributions) == {
        FactContribution(
            concept="completion",
            evidence_id="COMPLETION",
        ),
        FactContribution(
            concept="next_step",
            evidence_id="NEXT-STEP",
        ),
    }


def test_composition_provenance_is_benchmark_independent():
    completion = _extract(
        "SOURCE-A",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "SOURCE-B",
        "The customer asks what comes next.",
    )

    composed = ProvenancedComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert all(
        contribution.concept in {
            "completion",
            "next_step",
        }
        for contribution in composed.contributions
    )

    assert not any(
        hasattr(contribution, "expected_direction")
        for contribution in composed.contributions
    )

    assert not any(
        hasattr(contribution, "benchmark_family")
        for contribution in composed.contributions
    )