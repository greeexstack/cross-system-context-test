from __future__ import annotations

import pytest

from experiment.v03.evidence import AssertionPolarity
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


def _extract(text: str):
    return LexicalNormalizationSemanticExtractor().extract(
        evidence_id="ADVERSARIAL",
        content=text,
        source_system="test",
        record_id="ADVERSARIAL",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
    ).evidence.semantics


# ---------------------------------------------------------------------------
# Negative propositions
#
# These tests establish that explicit negation is represented at the
# concept level rather than incorrectly treating the entire observation
# as globally negative.
# ---------------------------------------------------------------------------

def test_negative_propositions_record_negated_concepts():
    negative_cases = (
        (
            "The customer does not want another discussion about the proposal.",
            "followup",
        ),
        (
            "The migration workshop is not complete.",
            "completion",
        ),
        (
            "The customer does not have budget approval for the quoted amount.",
            "approval",
        ),
    )

    for text, expected_concept in negative_cases:
        semantics = _extract(text)

        assert expected_concept in semantics.negated_concepts


def test_mixed_proposition_preserves_unnegated_fact():
    semantics = _extract(
        "The migration workshop is not complete and the customer "
        "asks what comes next."
    )

    assert "completion" in semantics.negated_concepts
    assert semantics.confirms_completion is not True
    assert semantics.requests_next_step is True


# ---------------------------------------------------------------------------
# Equivalent meaning / different wording
#
# These are expected to produce the same relevant semantic representation.
# Failures identify lexical-generalization gaps.
# ---------------------------------------------------------------------------

EQUIVALENT_PAIRS = (
    (
        "The customer wants another discussion about the proposal.",
        "The customer would like to speak about the offer again.",
    ),
    (
        "The quoted amount has budget approval.",
        "Funding for the proposed price has been authorized.",
    ),
    (
        "The customer rejects the revised commercial terms.",
        "The customer is unwilling to accept the updated terms.",
    ),
    (
        "The migration workshop is complete and the customer asks "
        "what comes next.",
        "The migration session has finished and the customer wants "
        "to know the next stage.",
    ),
)


@pytest.mark.parametrize("left,right", EQUIVALENT_PAIRS)
def test_equivalent_wording_produces_same_relevant_semantics(
    left: str,
    right: str,
) -> None:
    left_semantics = _extract(left)
    right_semantics = _extract(right)

    assert (
        left_semantics.requests_followup,
        left_semantics.expresses_acceptance,
        left_semantics.expresses_rejection,
        left_semantics.confirms_approval,
        left_semantics.confirms_completion,
        left_semantics.requests_next_step,
        left_semantics.concerns_same_work_item,
    ) == (
        right_semantics.requests_followup,
        right_semantics.expresses_acceptance,
        right_semantics.expresses_rejection,
        right_semantics.confirms_approval,
        right_semantics.confirms_completion,
        right_semantics.requests_next_step,
        right_semantics.concerns_same_work_item,
    )


# ---------------------------------------------------------------------------
# Opposite propositions
#
# These must not collapse into the same positive fact.
# ---------------------------------------------------------------------------

NEGATION_CASES = (
    (
        "The customer wants another discussion about the proposal.",
        "The customer does not want another discussion about the proposal.",
        "requests_followup",
    ),
    (
        "The migration workshop is complete and the customer asks "
        "what comes next.",
        "The migration workshop is not complete and the customer asks "
        "what comes next.",
        "confirms_completion",
    ),
    (
        "The customer has budget approval for the quoted amount.",
        "The customer does not have budget approval for the quoted amount.",
        "confirms_approval",
    ),
)


@pytest.mark.parametrize(
    "positive,negative,feature",
    NEGATION_CASES,
)
def test_negation_must_not_preserve_positive_fact(
    positive: str,
    negative: str,
    feature: str,
) -> None:
    positive_semantics = _extract(positive)
    negative_semantics = _extract(negative)

    assert getattr(positive_semantics, feature) is True
    assert getattr(negative_semantics, feature) is not True


def test_acceptance_and_rejection_are_distinct():
    accepted = _extract(
        "The customer accepted the revised commercial terms."
    )

    rejected = _extract(
        "The customer rejected the revised commercial terms."
    )

    assert accepted.expresses_acceptance is True
    assert accepted.expresses_rejection is not True

    assert rejected.expresses_rejection is True
    assert rejected.expresses_acceptance is not True


# ---------------------------------------------------------------------------
# Polarity field is retained for compatibility with the current model.
#
# The authoritative signal for mixed propositions is negated_concepts.
# ---------------------------------------------------------------------------

def test_default_positive_polarity_is_preserved_for_non_negated_text():
    semantics = _extract(
        "The customer wants another discussion about the proposal."
    )

    assert semantics.polarity == AssertionPolarity.POSITIVE