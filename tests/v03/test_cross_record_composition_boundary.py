from __future__ import annotations

from dataclasses import dataclass

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    EvidenceCondition,
    EvidenceSemantics,
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
class ComposedSemantics:
    """
    Test-layer composition of factual semantic attributes.

    This deliberately does not modify EvidenceSemantics or the production
    reasoner. It exists only to measure what would become possible if
    compatible facts from separate evidence records were composed before
    reasoning.
    """

    confirms_completion: bool = False
    requests_next_step: bool = False
    requests_followup: bool = False
    confirms_approval: bool = False
    expresses_acceptance: bool = False
    expresses_rejection: bool = False

    @classmethod
    def from_items(
        cls,
        items: tuple[SemanticEvidence, ...],
    ) -> "ComposedSemantics":
        return cls(
            confirms_completion=any(
                item.confirms_completion is True
                for item in items
            ),
            requests_next_step=any(
                item.requests_next_step is True
                for item in items
            ),
            requests_followup=any(
                item.requests_followup is True
                for item in items
            ),
            confirms_approval=any(
                item.confirms_approval is True
                for item in items
            ),
            expresses_acceptance=any(
                item.expresses_acceptance is True
                for item in items
            ),
            expresses_rejection=any(
                item.expresses_rejection is True
                for item in items
            ),
        )


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _extract(
    evidence_id: str,
    text: str,
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system="secondary",
        record_id=evidence_id,
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    ).evidence


def _condition(
    *items: SemanticEvidence,
) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=tuple(items),
    )


def test_current_reasoner_does_not_compose_completion_across_records():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    result = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            completion,
            next_step,
        ),
    )

    assert completion.semantics.confirms_completion is True
    assert completion.semantics.requests_next_step is None

    assert next_step.semantics.confirms_completion is None
    assert next_step.semantics.requests_next_step is True

    assert result.support_level == "primary_only"
    assert result.recommended_focus is None


def test_test_layer_can_compose_completion_and_next_step():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed = ComposedSemantics.from_items(
        (
            completion.semantics,
            next_step.semantics,
        )
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True


def test_composed_semantics_reconstruct_the_joint_fact():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed = ComposedSemantics.from_items(
        (
            completion.semantics,
            next_step.semantics,
        )
    )

    assert (
        composed.confirms_completion
        and composed.requests_next_step
    )


def test_single_multi_fact_record_matches_composed_separate_records():
    combined_record = _extract(
        "COMBINED",
        "The migration workshop is complete and the customer "
        "asks what comes next.",
    )

    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed = ComposedSemantics.from_items(
        (
            completion.semantics,
            next_step.semantics,
        )
    )

    assert combined_record.semantics.confirms_completion is True
    assert combined_record.semantics.requests_next_step is True

    assert composed.confirms_completion is True
    assert composed.requests_next_step is True


def test_negated_fact_is_not_composed_as_positive_completion():
    negated_completion = _extract(
        "NEGATED-COMPLETION",
        "The migration workshop is not complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed = ComposedSemantics.from_items(
        (
            negated_completion.semantics,
            next_step.semantics,
        )
    )

    assert "completion" in (
        negated_completion.semantics.negated_concepts
    )

    assert composed.confirms_completion is False
    assert composed.requests_next_step is True


def test_negated_followup_is_not_composed_as_positive_followup():
    positive_approval = _extract(
        "APPROVAL",
        "The quoted amount has budget approval.",
    )

    negated_followup = _extract(
        "NEGATED-FOLLOWUP",
        "The customer does not want another discussion "
        "about the proposal.",
    )

    composed = ComposedSemantics.from_items(
        (
            positive_approval.semantics,
            negated_followup.semantics,
        )
    )

    assert positive_approval.semantics.confirms_approval is True

    assert "followup" in (
        negated_followup.semantics.negated_concepts
    )

    assert composed.confirms_approval is True
    assert composed.requests_followup is False


def test_wrong_identity_must_be_filtered_before_test_composition():
    valid_completion = _extract(
        "VALID-COMPLETION",
        "The migration workshop is complete.",
    )

    extractor = LexicalNormalizationSemanticExtractor()

    wrong_identity = extractor.extract(
        evidence_id="WRONG-NEXT-STEP",
        content="The customer asks what comes next.",
        source_system="secondary",
        record_id="WRONG-NEXT-STEP",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    ).evidence

    valid_items = tuple(
        item
        for item in (
            valid_completion,
            wrong_identity,
        )
        if item.identity.quality == IdentityQuality.CONFIRMED
    )

    composed = ComposedSemantics.from_items(
        tuple(
            item.semantics
            for item in valid_items
        )
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False


def test_ambiguous_identity_must_be_filtered_before_test_composition():
    valid_completion = _extract(
        "VALID-COMPLETION",
        "The migration workshop is complete.",
    )

    extractor = LexicalNormalizationSemanticExtractor()

    ambiguous_next_step = extractor.extract(
        evidence_id="AMBIGUOUS-NEXT-STEP",
        content="The customer asks what comes next.",
        source_system="secondary",
        record_id="AMBIGUOUS-NEXT-STEP",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
        identity_quality=IdentityQuality.AMBIGUOUS,
    ).evidence

    valid_items = tuple(
        item
        for item in (
            valid_completion,
            ambiguous_next_step,
        )
        if item.identity.quality == IdentityQuality.CONFIRMED
    )

    composed = ComposedSemantics.from_items(
        tuple(
            item.semantics
            for item in valid_items
        )
    )

    assert composed.confirms_completion is True
    assert composed.requests_next_step is False


def test_composition_preserves_evidence_boundaries():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    condition = _condition(
        completion,
        next_step,
    )

    assert len(condition.items) == 2

    assert condition.items[0].evidence_id == "COMPLETION"
    assert condition.items[1].evidence_id == "NEXT-STEP"

    assert condition.items[0].semantics.confirms_completion is True
    assert condition.items[0].semantics.requests_next_step is None

    assert condition.items[1].semantics.confirms_completion is None
    assert condition.items[1].semantics.requests_next_step is True


def test_composition_is_deterministic():
    items = (
        _extract(
            "COMPLETION",
            "The migration workshop is complete.",
        ),
        _extract(
            "NEXT-STEP",
            "The customer asks what comes next.",
        ),
    )

    first = ComposedSemantics.from_items(
        tuple(item.semantics for item in items)
    )

    second = ComposedSemantics.from_items(
        tuple(item.semantics for item in items)
    )

    assert first == second


def test_existing_reasoner_remains_unchanged_by_test_composition():
    completion = _extract(
        "COMPLETION",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT-STEP",
        "The customer asks what comes next.",
    )

    composed = ComposedSemantics.from_items(
        (
            completion.semantics,
            next_step.semantics,
        )
    )

    result = _reasoner().evaluate(
        PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        _condition(
            completion,
            next_step,
        ),
    )

    # The test-layer adapter demonstrates that the facts can be composed,
    # while the production reasoner continues to behave exactly as it did
    # before composition existed.
    assert composed.confirms_completion is True
    assert composed.requests_next_step is True

    assert result.support_level == "primary_only"
    assert result.recommended_focus is None