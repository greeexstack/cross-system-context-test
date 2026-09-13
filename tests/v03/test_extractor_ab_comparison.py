from __future__ import annotations

import pytest

from experiment.v03.extractor import RuleBasedSemanticExtractor
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


GENERALIZATION_CASES = (
    (
        "F01",
        "requests_followup",
        (
            "The customer is assessing the proposal and would like "
            "another discussion next week.",
            "The proposal is being considered by the customer, who "
            "requested another conversation next week.",
            "The customer is evaluating the offer and wants to arrange "
            "a further discussion in the coming week.",
        ),
    ),
    (
        "F02",
        "confirms_approval",
        (
            "The customer has budget approval for the quoted amount "
            "and says procurement is progressing.",
            "Budget has been authorized for the proposed amount, and "
            "the purchasing process is moving forward.",
            "The customer confirmed financial approval for the quote "
            "and indicated that procurement has begun advancing it.",
        ),
    ),
    (
        "F03",
        "expresses_rejection",
        (
            "The customer says the revised commercial terms are "
            "unacceptable and wants the proposal reconsidered.",
            "The customer rejected the revised commercial terms and "
            "wants the proposal reconsidered.",
            "The customer is not prepared to accept the revised terms "
            "and asked that the offer be reviewed again.",
        ),
    ),
    (
        "F04",
        "concerns_same_work_item",
        (
            "The customer is discussing a different store rollout and "
            "says nothing about this quoted opportunity.",
            "The conversation concerns another store rollout and "
            "contains no information about this proposal.",
            "The customer raised a separate rollout initiative without "
            "providing any update on the quoted opportunity.",
        ),
    ),
    (
        "F10",
        "requests_next_step",
        (
            "The customer confirms the migration workshop is finished "
            "and asks what happens in the following handoff.",
            "The migration session is complete, and the customer wants "
            "to know the next stage of the handoff.",
            "The customer says the workshop is finished and is asking "
            "what should happen in the subsequent transition.",
        ),
    ),
)


def _extract(extractor, text: str):
    return extractor.extract(
        evidence_id="AB",
        content=text,
        source_system="test",
        record_id="AB",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
    ).evidence.semantics


@pytest.mark.parametrize(
    "case_id,feature,texts",
    GENERALIZATION_CASES,
)
def test_candidate_beats_or_matches_baseline_on_generalization(
    case_id: str,
    feature: str,
    texts: tuple[str, ...],
) -> None:
    baseline = RuleBasedSemanticExtractor()
    candidate = LexicalNormalizationSemanticExtractor()

    baseline_hits = 0
    candidate_hits = 0

    for text in texts:
        baseline_value = getattr(_extract(baseline, text), feature)
        candidate_value = getattr(_extract(candidate, text), feature)

        expected = (
            False if feature == "concerns_same_work_item" else True
        )

        if baseline_value == expected:
            baseline_hits += 1

        if candidate_value == expected:
            candidate_hits += 1

    assert candidate_hits >= baseline_hits, (
        f"{case_id}: candidate regressed on {feature}: "
        f"baseline={baseline_hits}/3, candidate={candidate_hits}/3"
    )

    print(
        f"\n{case_id}: baseline={baseline_hits}/3, "
        f"candidate={candidate_hits}/3"
    )


def test_candidate_has_strict_improvement_somewhere() -> None:
    baseline = RuleBasedSemanticExtractor()
    candidate = LexicalNormalizationSemanticExtractor()

    improvements = 0

    for _, feature, texts in GENERALIZATION_CASES:
        expected = (
            False if feature == "concerns_same_work_item" else True
        )

        baseline_hits = sum(
            getattr(_extract(baseline, text), feature) == expected
            for text in texts
        )

        candidate_hits = sum(
            getattr(_extract(candidate, text), feature) == expected
            for text in texts
        )

        improvements += candidate_hits > baseline_hits

    assert improvements > 0, (
        "Candidate extractor did not improve over the baseline "
        "on any generalized semantic case."
    )