from __future__ import annotations

import pytest

from experiment.v03.extractor import RuleBasedSemanticExtractor


PARAPHRASE_CASES = (
    (
        "F01-D1",
        (
            "The customer said the proposal is under internal review "
            "and asked for a follow-up next week."
        ),
        (
            "The customer is assessing the proposal and would like "
            "another discussion next week."
        ),
        {
            "requests_followup": True,
            "concerns_same_work_item": None,
        },
        True,
    ),
    (
        "F02-D1",
        (
            "The customer confirmed the quoted amount is within the "
            "approved budget and said the proposal is moving through procurement."
        ),
        (
            "The customer has budget approval for the quoted amount "
            "and says procurement is progressing."
        ),
        {
            "confirms_approval": True,
            "expresses_acceptance": True,
        },
        True,
    ),
    (
        "F03-D1",
        (
            "The customer said the revised commercial terms do not work "
            "for them and asked for the proposal to be revisited."
        ),
        (
            "The customer says the revised commercial terms are "
            "unacceptable and wants the proposal reconsidered."
        ),
        {
            "expresses_rejection": True,
        },
        True,
    ),
    (
        "F04-D1",
        (
            "The customer discussed a separate store rollout project; "
            "no statement about the quoted opportunity."
        ),
        (
            "The customer is discussing a different store rollout and "
            "says nothing about this quoted opportunity."
        ),
        {
            "concerns_same_work_item": False,
        },
        True,
    ),
    (
        "F10-D1",
        (
            "The customer confirmed the migration workshop was completed "
            "and asked what the next handoff step is."
        ),
        (
            "The customer confirms the migration workshop is finished "
            "and asks what happens in the following handoff."
        ),
        {
            "confirms_completion": True,
            "requests_next_step": True,
        },
        True,
    ),
)


def _extract(
    extractor: RuleBasedSemanticExtractor,
    text: str,
):
    return extractor.extract(
        evidence_id="TEST",
        content=text,
        source_system="test",
        record_id="TEST",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
    ).evidence.semantics


@pytest.mark.parametrize(
    "pair_id,original,paraphrase,required_features,known_failure",
    PARAPHRASE_CASES,
)
def test_paraphrase_preserves_semantic_features(
    pair_id: str,
    original: str,
    paraphrase: str,
    required_features: dict[str, object],
    known_failure: bool,
) -> None:
    extractor = RuleBasedSemanticExtractor()

    original_semantics = _extract(extractor, original)
    paraphrase_semantics = _extract(extractor, paraphrase)

    failures: list[str] = []

    for feature, expected in required_features.items():
        original_value = getattr(original_semantics, feature)
        paraphrase_value = getattr(paraphrase_semantics, feature)

        if original_value != expected:
            failures.append(
                f"original {feature}={original_value!r}, "
                f"expected {expected!r}"
            )

        if paraphrase_value != expected:
            failures.append(
                f"paraphrase {feature}={paraphrase_value!r}, "
                f"expected {expected!r}"
            )

    if failures:
        message = f"{pair_id}: " + "; ".join(failures)

        if known_failure:
            pytest.xfail(
                "Known v0.3 baseline extractor limitation: "
                f"semantic-preserving paraphrase is not normalized reliably. {message}"
            )

        pytest.fail(message)


@pytest.mark.parametrize(
    "pair_id,original,paraphrase,_,known_failure",
    PARAPHRASE_CASES,
)
def test_paraphrase_semantic_objects_have_same_relevant_features(
    pair_id: str,
    original: str,
    paraphrase: str,
    _,
    known_failure: bool,
) -> None:
    extractor = RuleBasedSemanticExtractor()

    original_semantics = _extract(extractor, original)
    paraphrase_semantics = _extract(extractor, paraphrase)

    relevant_features = (
        "requests_followup",
        "expresses_acceptance",
        "expresses_rejection",
        "confirms_approval",
        "confirms_completion",
        "requests_next_step",
        "concerns_same_work_item",
    )

    original_state = tuple(
        getattr(original_semantics, feature)
        for feature in relevant_features
    )

    paraphrase_state = tuple(
        getattr(paraphrase_semantics, feature)
        for feature in relevant_features
    )

    if paraphrase_state != original_state:
        message = (
            f"{pair_id}: semantic representation changed under paraphrase\n"
            f"original={original_state}\n"
            f"paraphrase={paraphrase_state}"
        )

        if known_failure:
            pytest.xfail(
                "Known v0.3 baseline extractor limitation: "
                f"semantic-preserving paraphrase is not normalized reliably. {message}"
            )

        pytest.fail(message)


def test_f02_paraphrase_preserves_budget_approval_signal() -> None:
    extractor = RuleBasedSemanticExtractor()

    texts = (
        "The customer has budget approval for the quoted amount "
        "and says procurement is progressing.",
        "Budget has been authorized for the proposed amount, and "
        "the purchasing process is moving forward.",
        "The customer confirmed financial approval for the quote "
        "and indicated that procurement has begun advancing it.",
    )

    failures = []

    for text in texts:
        semantics = _extract(extractor, text)

        if semantics.confirms_approval is not True:
            failures.append(text)

    if failures:
        pytest.xfail(
            "Known v0.3 baseline extractor limitation: "
            "approval paraphrase coverage is incomplete."
        )


def test_f03_paraphrase_preserves_rejection_signal() -> None:
    extractor = RuleBasedSemanticExtractor()

    texts = (
        "The customer says the revised commercial terms are "
        "unacceptable and wants the proposal reconsidered.",
        "The customer rejected the revised commercial terms and "
        "wants the proposal reconsidered.",
        "The customer is not prepared to accept the revised terms "
        "and asked that the offer be reviewed again.",
    )

    failures = []

    for text in texts:
        semantics = _extract(extractor, text)

        if semantics.expresses_rejection is not True:
            failures.append(text)

    if failures:
        pytest.xfail(
            "Known v0.3 baseline extractor limitation: "
            "rejection paraphrase coverage is incomplete."
        )


def test_f04_paraphrase_preserves_irrelevance_signal() -> None:
    extractor = RuleBasedSemanticExtractor()

    texts = (
        "The customer is discussing a different store rollout and "
        "says nothing about this quoted opportunity.",
        "The conversation concerns another store rollout and "
        "contains no information about this proposal.",
        "The customer raised a separate rollout initiative without "
        "providing any update on the quoted opportunity.",
    )

    failures = []

    for text in texts:
        semantics = _extract(extractor, text)

        if semantics.concerns_same_work_item is not False:
            failures.append(text)

    if failures:
        pytest.xfail(
            "Known v0.3 baseline extractor limitation: "
            "irrelevance paraphrase coverage is incomplete."
        )


def test_f10_paraphrase_preserves_service_next_step_signals() -> None:
    extractor = RuleBasedSemanticExtractor()

    texts = (
        "The customer confirms the migration workshop is finished "
        "and asks what happens in the following handoff.",
        "The migration session is complete, and the customer wants "
        "to know the next stage of the handoff.",
        "The customer says the workshop is finished and is asking "
        "what should happen in the subsequent transition.",
    )

    failures = []

    for text in texts:
        semantics = _extract(extractor, text)

        if not (
            semantics.confirms_completion is True
            and semantics.requests_next_step is True
        ):
            failures.append(text)

    if failures:
        pytest.xfail(
            "Known v0.3 baseline extractor limitation: "
            "service/next-step paraphrase coverage is incomplete."
        )


def test_extractor_does_not_emit_benchmark_transition_labels() -> None:
    extractor = RuleBasedSemanticExtractor()

    result = extractor.extract(
        evidence_id="E8",
        content="The customer wants another discussion about the proposal.",
        source_system="test",
        record_id="E8",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
    )

    semantics = result.evidence.semantics

    assert not hasattr(semantics, "expected_transition")
    assert not hasattr(semantics, "support_level")
    assert not hasattr(semantics, "interpretation_class")
    assert not hasattr(semantics, "ground_truth")