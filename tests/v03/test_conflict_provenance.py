from __future__ import annotations

from dataclasses import dataclass

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class ConflictContribution:
    concept: str
    polarity: str
    evidence_id: str


@dataclass(frozen=True)
class ProvenancedConflict:
    contributions: tuple[ConflictContribution, ...]

    @property
    def has_positive(self) -> bool:
        return any(
            contribution.polarity == "positive"
            for contribution in self.contributions
        )

    @property
    def has_negative(self) -> bool:
        return any(
            contribution.polarity == "negative"
            for contribution in self.contributions
        )

    @property
    def is_conflicted(self) -> bool:
        return self.has_positive and self.has_negative

    @classmethod
    def from_items(
        cls,
        items: tuple[SemanticEvidence, ...],
    ) -> "ProvenancedConflict":
        contributions: list[ConflictContribution] = []

        for item in items:
            if item.identity.quality != IdentityQuality.CONFIRMED:
                continue

            if item.semantics.requests_followup is True:
                contributions.append(
                    ConflictContribution(
                        concept="followup",
                        polarity="positive",
                        evidence_id=item.evidence_id,
                    )
                )

            if "followup" in item.semantics.negated_concepts:
                contributions.append(
                    ConflictContribution(
                        concept="followup",
                        polarity="negative",
                        evidence_id=item.evidence_id,
                    )
                )

            if item.semantics.confirms_approval is True:
                contributions.append(
                    ConflictContribution(
                        concept="approval",
                        polarity="positive",
                        evidence_id=item.evidence_id,
                    )
                )

            if "approval" in item.semantics.negated_concepts:
                contributions.append(
                    ConflictContribution(
                        concept="approval",
                        polarity="negative",
                        evidence_id=item.evidence_id,
                    )
                )

            if item.semantics.confirms_completion is True:
                contributions.append(
                    ConflictContribution(
                        concept="completion",
                        polarity="positive",
                        evidence_id=item.evidence_id,
                    )
                )

            if "completion" in item.semantics.negated_concepts:
                contributions.append(
                    ConflictContribution(
                        concept="completion",
                        polarity="negative",
                        evidence_id=item.evidence_id,
                    )
                )

        return cls(
            contributions=tuple(contributions),
        )


def _extract(
    evidence_id: str,
    text: str,
    *,
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system="secondary",
        record_id=evidence_id,
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
        identity_quality=identity_quality,
    ).evidence


def test_positive_followup_contribution_keeps_source():
    evidence = _extract(
        "POSITIVE-FOLLOWUP",
        "The customer wants another discussion about the proposal.",
    )

    conflict = ProvenancedConflict.from_items(
        (evidence,),
    )

    assert conflict.contributions == (
        ConflictContribution(
            concept="followup",
            polarity="positive",
            evidence_id="POSITIVE-FOLLOWUP",
        ),
    )

    assert conflict.is_conflicted is False


def test_negative_followup_contribution_keeps_source():
    evidence = _extract(
        "NEGATIVE-FOLLOWUP",
        "The customer does not want another discussion about the proposal.",
    )

    conflict = ProvenancedConflict.from_items(
        (evidence,),
    )

    assert conflict.contributions == (
        ConflictContribution(
            concept="followup",
            polarity="negative",
            evidence_id="NEGATIVE-FOLLOWUP",
        ),
    )

    assert conflict.is_conflicted is False


def test_conflicting_followup_keeps_both_contributors():
    positive = _extract(
        "CRM-POSITIVE",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "EMAIL-NEGATIVE",
        "The customer does not want another discussion about the proposal.",
    )

    conflict = ProvenancedConflict.from_items(
        (
            positive,
            negative,
        ),
    )

    assert conflict.is_conflicted is True

    assert set(conflict.contributions) == {
        ConflictContribution(
            concept="followup",
            polarity="positive",
            evidence_id="CRM-POSITIVE",
        ),
        ConflictContribution(
            concept="followup",
            polarity="negative",
            evidence_id="EMAIL-NEGATIVE",
        ),
    }


def test_conflicting_approval_keeps_both_contributors():
    positive = _extract(
        "FINANCE-APPROVED",
        "The quoted amount has budget approval.",
    )

    negative = _extract(
        "FINANCE-DENIED",
        "The customer does not have budget approval for the quoted amount.",
    )

    conflict = ProvenancedConflict.from_items(
        (
            positive,
            negative,
        ),
    )

    assert conflict.is_conflicted is True

    assert set(conflict.contributions) == {
        ConflictContribution(
            concept="approval",
            polarity="positive",
            evidence_id="FINANCE-APPROVED",
        ),
        ConflictContribution(
            concept="approval",
            polarity="negative",
            evidence_id="FINANCE-DENIED",
        ),
    }


def test_negated_completion_is_recorded_as_negative_contribution():
    evidence = _extract(
        "NEGATED-COMPLETION",
        "The migration workshop is not complete.",
    )

    conflict = ProvenancedConflict.from_items(
        (evidence,),
    )

    assert conflict.contributions == (
        ConflictContribution(
            concept="completion",
            polarity="negative",
            evidence_id="NEGATED-COMPLETION",
        ),
    )


def test_valid_and_invalid_sources_do_not_mix_in_conflict_provenance():
    positive = _extract(
        "VALID-POSITIVE",
        "The customer wants another discussion about the proposal.",
    )

    wrong_identity = _extract(
        "WRONG-IDENTITY",
        "The customer does not want another discussion about the proposal.",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    conflict = ProvenancedConflict.from_items(
        (
            positive,
            wrong_identity,
        ),
    )

    assert conflict.is_conflicted is False

    assert conflict.contributions == (
        ConflictContribution(
            concept="followup",
            polarity="positive",
            evidence_id="VALID-POSITIVE",
        ),
    )


def test_same_concept_multiple_positive_sources_remains_traceable():
    first = _extract(
        "CRM",
        "The customer wants another discussion about the proposal.",
    )

    second = _extract(
        "EMAIL",
        "The customer wants another discussion about the proposal.",
    )

    conflict = ProvenancedConflict.from_items(
        (
            first,
            second,
        ),
    )

    assert conflict.is_conflicted is False

    assert set(conflict.contributions) == {
        ConflictContribution(
            concept="followup",
            polarity="positive",
            evidence_id="CRM",
        ),
        ConflictContribution(
            concept="followup",
            polarity="positive",
            evidence_id="EMAIL",
        ),
    }


def test_three_way_conflict_retains_all_positive_and_negative_sources():
    positive_1 = _extract(
        "POSITIVE-1",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
    )

    positive_2 = _extract(
        "POSITIVE-2",
        "The customer wants another discussion about the proposal.",
    )

    conflict = ProvenancedConflict.from_items(
        (
            positive_1,
            negative,
            positive_2,
        ),
    )

    assert conflict.is_conflicted is True

    assert set(conflict.contributions) == {
        ConflictContribution(
            concept="followup",
            polarity="positive",
            evidence_id="POSITIVE-1",
        ),
        ConflictContribution(
            concept="followup",
            polarity="negative",
            evidence_id="NEGATIVE",
        ),
        ConflictContribution(
            concept="followup",
            polarity="positive",
            evidence_id="POSITIVE-2",
        ),
    }


def test_conflict_provenance_does_not_mutate_original_semantics():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
    )

    positive_before = positive.semantics
    negative_before = negative.semantics

    conflict = ProvenancedConflict.from_items(
        (
            positive,
            negative,
        ),
    )

    assert conflict.is_conflicted is True

    assert positive.semantics == positive_before
    assert negative.semantics == negative_before


def test_conflict_provenance_is_deterministic():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
    )

    first = ProvenancedConflict.from_items(
        (
            positive,
            negative,
        ),
    )

    second = ProvenancedConflict.from_items(
        (
            positive,
            negative,
        ),
    )

    assert first == second


def test_reversing_input_order_preserves_conflict_semantics():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
    )

    first = ProvenancedConflict.from_items(
        (
            positive,
            negative,
        ),
    )

    second = ProvenancedConflict.from_items(
        (
            negative,
            positive,
        ),
    )

    assert first.has_positive == second.has_positive
    assert first.has_negative == second.has_negative
    assert first.is_conflicted == second.is_conflicted

    assert set(first.contributions) == set(second.contributions)


def test_conflict_provenance_does_not_choose_a_winner():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
    )

    conflict = ProvenancedConflict.from_items(
        (
            positive,
            negative,
        ),
    )

    positive_ids = {
        contribution.evidence_id
        for contribution in conflict.contributions
        if contribution.polarity == "positive"
    }

    negative_ids = {
        contribution.evidence_id
        for contribution in conflict.contributions
        if contribution.polarity == "negative"
    }

    assert positive_ids == {"POSITIVE"}
    assert negative_ids == {"NEGATIVE"}

    # The test-layer conflict representation records disagreement.
    # It does not collapse the disagreement into a winner.
    assert positive_ids
    assert negative_ids


def test_conflict_provenance_remains_benchmark_independent():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
    )

    conflict = ProvenancedConflict.from_items(
        (
            positive,
            negative,
        ),
    )

    assert all(
        contribution.concept in {
            "followup",
            "approval",
            "completion",
        }
        for contribution in conflict.contributions
    )

    assert not any(
        hasattr(contribution, "expected_direction")
        for contribution in conflict.contributions
    )