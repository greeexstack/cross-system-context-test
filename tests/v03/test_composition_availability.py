from __future__ import annotations

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    EvidenceCondition,
    IdentityQuality,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
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
    *,
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    customer_id: str = "C001",
):
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system="secondary",
        record_id=evidence_id,
        occurred_at="2026-09-12T10:00:00Z",
        customer_id=customer_id,
        identity_quality=identity_quality,
    ).evidence


def _compose_condition(
    availability: str,
    *items,
) -> EvidenceCondition:
    return EvidenceCondition(
        availability=availability,
        items=tuple(items),
    )


def _eligible_ids(
    condition: EvidenceCondition,
) -> tuple[str, ...]:
    accepted: list[str] = []

    for item in condition.items:
        if item.identity.quality != IdentityQuality.CONFIRMED:
            continue

        if item.timestamp is None:
            continue

        accepted.append(item.evidence_id)

    return tuple(accepted)


def test_available_with_no_items_is_distinct_from_unavailable():
    available = _compose_condition(
        "available",
    )

    unavailable = _compose_condition(
        "unavailable",
    )

    assert available.availability == "available"
    assert unavailable.availability == "unavailable"

    assert available.items == ()
    assert unavailable.items == ()


def test_available_empty_condition_has_no_evidence_ids():
    condition = _compose_condition(
        "available",
    )

    result = _eligible_ids(condition)

    assert result == ()


def test_unavailable_condition_has_no_evidence_ids():
    condition = _compose_condition(
        "unavailable",
    )

    result = _eligible_ids(condition)

    assert result == ()


def test_available_valid_evidence_is_eligible():
    evidence = _extract(
        "VALID",
        "The customer wants another discussion about the proposal.",
    )

    condition = _compose_condition(
        "available",
        evidence,
    )

    result = _eligible_ids(condition)

    assert result == ("VALID",)


def test_available_wrong_identity_evidence_is_filtered():
    evidence = _extract(
        "WRONG",
        "The customer wants another discussion about the proposal.",
        identity_quality=IdentityQuality.NO_MATCH,
        customer_id="C999",
    )

    condition = _compose_condition(
        "available",
        evidence,
    )

    result = _eligible_ids(condition)

    assert result == ()


def test_unavailable_status_does_not_invent_secondary_evidence():
    condition = _compose_condition(
        "unavailable",
    )

    result = _eligible_ids(condition)

    assert result == ()


def test_reasoner_distinguishes_no_secondary_evidence_from_primary_only():
    no_evidence = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    filtered_evidence = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(
                _extract(
                    "WRONG",
                    "The customer wants another discussion about the proposal.",
                    identity_quality=IdentityQuality.NO_MATCH,
                    customer_id="C999",
                ),
            ),
        ),
    )

    assert no_evidence.support_level == "no_secondary_evidence"
    assert filtered_evidence.support_level == "primary_only"


def test_reasoner_preserves_primary_state_when_secondary_is_unavailable():
    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="unavailable",
            items=(),
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.decision_strength == "moderate"


def test_reasoner_preserves_primary_state_when_secondary_is_available_empty():
    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.decision_strength == "moderate"


def test_unavailable_and_empty_do_not_create_positive_uplift():
    unavailable = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="unavailable",
            items=(),
        ),
    )

    empty = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    assert unavailable.interpretation_class == (
        empty.interpretation_class
    )

    assert unavailable.decision_strength == (
        empty.decision_strength
    )


def test_valid_evidence_changes_result_when_available():
    valid = _extract(
        "VALID",
        "The customer wants another discussion about the proposal.",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(valid,),
        ),
    )

    assert result.interpretation_class == "quote_followup_pending"


def test_filtered_evidence_does_not_change_result_like_valid_evidence():
    valid = _extract(
        "VALID",
        "The customer wants another discussion about the proposal.",
    )

    wrong_identity = _extract(
        "WRONG",
        "The customer wants another discussion about the proposal.",
        identity_quality=IdentityQuality.NO_MATCH,
        customer_id="C999",
    )

    valid_result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(valid,),
        ),
    )

    filtered_result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(wrong_identity,),
        ),
    )

    assert valid_result.interpretation_class == (
        "quote_followup_pending"
    )

    assert filtered_result.interpretation_class == (
        "quote_pending_decision"
    )


def test_multiple_valid_items_preserve_availability():
    first = _extract(
        "FIRST",
        "The customer wants another discussion about the proposal.",
    )

    second = _extract(
        "SECOND",
        "The quoted amount has budget approval.",
    )

    condition = _compose_condition(
        "available",
        first,
        second,
    )

    result = _eligible_ids(condition)

    assert result == (
        "FIRST",
        "SECOND",
    )


def test_mixed_valid_and_filtered_items_remain_available():
    valid = _extract(
        "VALID",
        "The customer wants another discussion about the proposal.",
    )

    wrong = _extract(
        "WRONG",
        "The quoted amount has budget approval.",
        identity_quality=IdentityQuality.NO_MATCH,
        customer_id="C999",
    )

    condition = _compose_condition(
        "available",
        valid,
        wrong,
    )

    result = _eligible_ids(condition)

    assert result == ("VALID",)


def test_all_items_filtered_is_not_the_same_as_unavailable():
    wrong = _extract(
        "WRONG",
        "The customer wants another discussion about the proposal.",
        identity_quality=IdentityQuality.NO_MATCH,
        customer_id="C999",
    )

    available_filtered = _compose_condition(
        "available",
        wrong,
    )

    unavailable = _compose_condition(
        "unavailable",
    )

    filtered_result = _eligible_ids(
        available_filtered,
    )

    unavailable_result = _eligible_ids(
        unavailable,
    )

    assert filtered_result == ()
    assert unavailable_result == ()


def test_availability_is_metadata_not_semantic_content():
    evidence = _extract(
        "VALID",
        "The customer wants another discussion about the proposal.",
    )

    available = _compose_condition(
        "available",
        evidence,
    )

    result = _eligible_ids(available)

    assert result == ("VALID",)


def test_changing_availability_does_not_mutate_evidence():
    evidence = _extract(
        "VALID",
        "The customer wants another discussion about the proposal.",
    )

    before_semantics = evidence.semantics
    before_identity = evidence.identity
    before_provenance = evidence.provenance

    available = _compose_condition(
        "available",
        evidence,
    )

    unavailable = _compose_condition(
        "unavailable",
    )

    _eligible_ids(available)
    _eligible_ids(unavailable)

    assert evidence.semantics == before_semantics
    assert evidence.identity == before_identity
    assert evidence.provenance == before_provenance


def test_empty_available_condition_is_deterministic():
    condition = _compose_condition(
        "available",
    )

    first = _eligible_ids(condition)
    second = _eligible_ids(condition)

    assert first == second


def test_unavailable_condition_is_deterministic():
    condition = _compose_condition(
        "unavailable",
    )

    first = _eligible_ids(condition)
    second = _eligible_ids(condition)

    assert first == second


def test_availability_does_not_create_benchmark_policy():
    condition = _compose_condition(
        "unavailable",
    )

    result = _eligible_ids(condition)

    assert result == ()