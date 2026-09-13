from __future__ import annotations

import pytest

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


def _extract(
    extractor: LexicalNormalizationSemanticExtractor,
    text: str,
):
    return extractor.extract(
        evidence_id="GENERALIZATION",
        content=text,
        source_system="test",
        record_id="GENERALIZATION",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
    ).evidence.semantics


@pytest.mark.parametrize(
    "case_id,feature,texts",
    GENERALIZATION_CASES,
)
def test_candidate_handles_independently_worded_variants(
    case_id: str,
    feature: str,
    texts: tuple[str, ...],
) -> None:
    extractor = LexicalNormalizationSemanticExtractor()

    for text in texts:
        semantics = _extract(extractor, text)

        assert getattr(semantics, feature) is True or (
            feature == "concerns_same_work_item"
            and getattr(semantics, feature) is False
        ), (
            f"{case_id}: expected {feature} in independently worded "
            f"variant; got {getattr(semantics, feature)!r}\n"
            f"text={text!r}"
        )


def test_candidate_preserves_f04_irrelevance_across_variants() -> None:
    extractor = LexicalNormalizationSemanticExtractor()

    texts = GENERALIZATION_CASES[3][2]

    for text in texts:
        semantics = _extract(extractor, text)

        assert semantics.concerns_same_work_item is False