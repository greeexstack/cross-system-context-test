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
class AcceptedEvidence:
    evidence_id: str
    source_system: str
    timestamp: datetime
    semantics: object


@dataclass(frozen=True)
class EndToEndComposition:
    confirms_completion: bool = False
    requests_next_step: bool = False
    requests_followup: bool = False
    confirms_approval: bool = False
    expresses_acceptance: bool = False
    expresses_rejection: bool = False

    accepted_evidence_ids: tuple[str, ...] = ()

    @classmethod
    def from_items(
        cls,
        items: tuple[SemanticEvidence, ...],
    ) -> "EndToEndComposition":
        accepted: list[AcceptedEvidence] = []

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

            accepted.append(
                AcceptedEvidence(
                    evidence_id=item.evidence_id,
                    source_system=item.provenance.source_system,
                    timestamp=when,
                    semantics=item.semantics,
                )
            )

        return cls(
            confirms_completion=any(
                item.semantics.confirms_completion is True
                and "completion"
                not in item.semantics.negated_concepts
                for item in accepted
            ),
            requests_next_step=any(
                item.semantics.requests_next_step is True
                and "next_step"
                not in item.semantics.negated_concepts
                for item in accepted
            ),
            requests_followup=any(
                item.semantics.requests_followup is True
                and "followup"
                not in item.semantics.negated_concepts
                for item in accepted
            ),
            confirms_approval=any(
                item.semantics.confirms_approval is True
                and "approval"
                not in item.semantics.negated_concepts
                for item in accepted
            ),
            expresses_acceptance=any(
                item.semantics.expresses_acceptance is True
                for item in accepted
            ),
            expresses_rejection=any(
                item.semantics.expresses_rejection is True
                for item in accepted
            ),
            accepted_evidence_ids=tuple(
                item.evidence_id
                for item in accepted
            ),
        )


def _extract(
    evidence_id: str,
    source_system: str,
    text: str,
    *,
    occurred_at: str = "2026-09-12T10:00:00Z",
    customer_id: str = "C001",
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
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


def test_clean_two_system_pipeline_composes_valid_facts():
    completion = _extract(
        "CRM-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "EMAIL-NEXT-STEP",
        "email",
        "The customer asks what comes next.",
    )

    composed = EndToEndComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True

    assert set(composed.accepted_evidence_ids) == {
        "CRM-COMPLETION",
        "EMAIL-NEXT-STEP",
    }


def test_wrong_identity_is_removed_before_composition():
    completion = _extract(
        "VALID-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    wrong_next_step = _extract(
        "WRONG-NEXT-STEP",
        "email",
        "The customer asks what comes next.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    composed = EndToEndComposition.from_items(
        (
            completion,
            wrong_next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False

    assert composed.accepted_evidence_ids == (
        "VALID-COMPLETION",
    )


def test_ambiguous_identity_is_removed_before_composition():
    completion = _extract(
        "VALID-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    ambiguous_next_step = _extract(
        "AMBIGUOUS-NEXT-STEP",
        "email",
        "The customer asks what comes next.",
        identity_quality=IdentityQuality.AMBIGUOUS,
    )

    composed = EndToEndComposition.from_items(
        (
            completion,
            ambiguous_next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False

    assert composed.accepted_evidence_ids == (
        "VALID-COMPLETION",
    )


def test_stale_evidence_is_removed_before_composition():
    fresh_completion = _extract(
        "FRESH-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    stale_next_step = _extract(
        "STALE-NEXT-STEP",
        "email",
        "The customer asks what comes next.",
        occurred_at="2026-07-01T10:00:00Z",
    )

    composed = EndToEndComposition.from_items(
        (
            fresh_completion,
            stale_next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False

    assert composed.accepted_evidence_ids == (
        "FRESH-COMPLETION",
    )


def test_irrelevant_evidence_is_removed_before_composition():
    completion = _extract(
        "VALID-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    irrelevant = _extract(
        "IRRELEVANT",
        "email",
        "The customer is discussing a separate store rollout "
        "and says nothing about this opportunity.",
    )

    composed = EndToEndComposition.from_items(
        (
            completion,
            irrelevant,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False

    assert composed.accepted_evidence_ids == (
        "VALID-COMPLETION",
    )


def test_negation_is_preserved_through_the_pipeline():
    negated_completion = _extract(
        "NEGATED-COMPLETION",
        "crm",
        "The migration workshop is not complete.",
    )

    next_step = _extract(
        "VALID-NEXT-STEP",
        "email",
        "The customer asks what comes next.",
    )

    composed = EndToEndComposition.from_items(
        (
            negated_completion,
            next_step,
        ),
    )

    assert composed.confirms_completion is False
    assert composed.requests_next_step is True

    assert set(composed.accepted_evidence_ids) == {
        "NEGATED-COMPLETION",
        "VALID-NEXT-STEP",
    }


def test_negated_next_step_is_not_composed_as_positive():
    completion = _extract(
        "VALID-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    negated_next_step = _extract(
        "NEGATED-NEXT",
        "email",
        "The customer does not want to discuss what comes next.",
    )

    composed = EndToEndComposition.from_items(
        (
            completion,
            negated_next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False


def test_mixed_adversarial_population_cannot_create_false_joint_signal():
    valid_completion = _extract(
        "VALID-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    valid_next_step = _extract(
        "VALID-NEXT-STEP",
        "email",
        "The customer asks what comes next.",
    )

    wrong_identity = _extract(
        "WRONG-IDENTITY",
        "support",
        "The customer does not want to discuss what comes next.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    stale_completion = _extract(
        "STALE-COMPLETION",
        "legacy",
        "The migration workshop is complete.",
        occurred_at="2026-07-01T10:00:00Z",
    )

    negated_completion = _extract(
        "NEGATED-COMPLETION",
        "notes",
        "The migration workshop is not complete.",
    )

    irrelevant = _extract(
        "IRRELEVANT",
        "crm",
        "The customer is discussing a separate store rollout "
        "and says nothing about this opportunity.",
    )

    composed = EndToEndComposition.from_items(
        (
            valid_completion,
            valid_next_step,
            wrong_identity,
            stale_completion,
            negated_completion,
            irrelevant,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True

    # Valid, fresh, relevant records remain eligible even when their
    # semantic polarity is negative.
    assert set(composed.accepted_evidence_ids) == {
        "VALID-COMPLETION",
        "VALID-NEXT-STEP",
        "NEGATED-COMPLETION",
    }

    # These records must be excluded before composition.
    assert "WRONG-IDENTITY" not in composed.accepted_evidence_ids
    assert "STALE-COMPLETION" not in composed.accepted_evidence_ids
    assert "IRRELEVANT" not in composed.accepted_evidence_ids

def test_only_valid_fresh_relevant_records_are_eligible():
    valid = _extract(
        "VALID",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    wrong_identity = _extract(
        "WRONG",
        "email",
        "The customer wants another discussion about the proposal.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    ambiguous = _extract(
        "AMBIGUOUS",
        "support",
        "The customer wants another discussion about the proposal.",
        identity_quality=IdentityQuality.AMBIGUOUS,
    )

    stale = _extract(
        "STALE",
        "legacy",
        "The customer wants another discussion about the proposal.",
        occurred_at="2026-07-01T10:00:00Z",
    )

    irrelevant = _extract(
        "IRRELEVANT",
        "crm",
        "The customer is discussing a separate store rollout "
        "and says nothing about this opportunity.",
    )

    composed = EndToEndComposition.from_items(
        (
            valid,
            wrong_identity,
            ambiguous,
            stale,
            irrelevant,
        ),
    )

    assert composed.accepted_evidence_ids == (
        "VALID",
    )


def test_cross_system_composition_retains_source_diversity():
    completion = _extract(
        "CRM-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "EMAIL-NEXT",
        "email",
        "The customer asks what comes next.",
    )

    composed = EndToEndComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert set(composed.accepted_evidence_ids) == {
        "CRM-COMPLETION",
        "EMAIL-NEXT",
    }

    source_systems = {
        item.provenance.source_system
        for item in (
            completion,
            next_step,
        )
    }

    assert source_systems == {
        "crm",
        "email",
    }


def test_provenance_and_semantic_composition_remain_separate():
    completion = _extract(
        "CRM-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "EMAIL-NEXT",
        "email",
        "The customer asks what comes next.",
    )

    composed = EndToEndComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True

    assert completion.provenance.source_system == "crm"
    assert next_step.provenance.source_system == "email"

    assert completion.provenance.record_id == "CRM-COMPLETION"
    assert next_step.provenance.record_id == "EMAIL-NEXT"


def test_order_of_records_does_not_change_composed_truth():
    completion = _extract(
        "COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT",
        "email",
        "The customer asks what comes next.",
    )

    forward = EndToEndComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    reverse = EndToEndComposition.from_items(
        (
            next_step,
            completion,
        ),
    )

    assert forward.confirms_completion == (
        reverse.confirms_completion
    )
    assert forward.requests_next_step == (
        reverse.requests_next_step
    )

    assert set(forward.accepted_evidence_ids) == set(
        reverse.accepted_evidence_ids
    )


def test_composition_is_deterministic():
    completion = _extract(
        "COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT",
        "email",
        "The customer asks what comes next.",
    )

    first = EndToEndComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    second = EndToEndComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert first == second


def test_original_evidence_is_not_mutated():
    completion = _extract(
        "COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT",
        "email",
        "The customer asks what comes next.",
    )

    completion_semantics = completion.semantics
    next_step_semantics = next_step.semantics

    completion_provenance = completion.provenance
    next_step_provenance = next_step.provenance

    composed = EndToEndComposition.from_items(
        (
            completion,
            next_step,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True

    assert completion.semantics == completion_semantics
    assert next_step.semantics == next_step_semantics

    assert completion.provenance == completion_provenance
    assert next_step.provenance == next_step_provenance


def test_end_to_end_pipeline_does_not_assign_policy_winner():
    positive = _extract(
        "POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
    )

    composed = EndToEndComposition.from_items(
        (
            positive,
            negative,
        ),
    )

    # Both valid contributors remain represented.
    assert set(composed.accepted_evidence_ids) == {
        "POSITIVE",
        "NEGATIVE",
    }

    # The composition layer does not invent a conflict-resolution winner.
    assert positive.semantics.requests_followup is True
    assert "followup" in negative.semantics.negated_concepts


def test_full_adversarial_pipeline_keeps_negative_fact_negative():
    completion = _extract(
        "COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    next_step_negative = _extract(
        "NEXT-NEGATIVE",
        "email",
        "The customer does not want to discuss what comes next.",
    )

    wrong_identity_positive = _extract(
        "WRONG-POSITIVE",
        "support",
        "The customer asks what comes next.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    stale_positive = _extract(
        "STALE-POSITIVE",
        "legacy",
        "The customer asks what comes next.",
        occurred_at="2026-07-01T10:00:00Z",
    )

    composed = EndToEndComposition.from_items(
        (
            completion,
            next_step_negative,
            wrong_identity_positive,
            stale_positive,
        ),
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False

    assert set(composed.accepted_evidence_ids) == {
        "COMPLETION",
        "NEXT-NEGATIVE",
    }