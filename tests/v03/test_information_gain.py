from __future__ import annotations

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
from experiment.v03.battery import EVALUATION_AT


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
) -> object:
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


def _available(*items) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=tuple(items),
    )


def _empty() -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=(),
    )


def test_redundant_followup_evidence_does_not_create_a_different_interpretation():
    reasoner = _reasoner()

    control = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _empty(),
    )

    one_source = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _available(
            _extract(
                "FOLLOWUP-1",
                "The customer wants another discussion about the proposal.",
            ),
        ),
    )

    duplicate_source = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _available(
            _extract(
                "FOLLOWUP-1",
                "The customer wants another discussion about the proposal.",
            ),
            _extract(
                "FOLLOWUP-2",
                "The customer wants another discussion about the proposal.",
            ),
        ),
    )

    assert control.interpretation_class == "quote_pending_decision"
    assert one_source.interpretation_class == "quote_followup_pending"
    assert duplicate_source.interpretation_class == (
        one_source.interpretation_class
    )

    assert duplicate_source.decision_strength == (
        one_source.decision_strength
    )


def test_redundant_approval_evidence_does_not_double_count_strength():
    reasoner = _reasoner()

    one_source = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _available(
            _extract(
                "APPROVAL-1",
                "The quoted amount has budget approval.",
            ),
        ),
    )

    duplicate_source = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _available(
            _extract(
                "APPROVAL-1",
                "The quoted amount has budget approval.",
            ),
            _extract(
                "APPROVAL-2",
                "The quoted amount has budget approval.",
            ),
        ),
    )

    assert one_source.interpretation_class == (
        duplicate_source.interpretation_class
    )

    assert one_source.decision_strength == "stronger"
    assert duplicate_source.decision_strength == "stronger"


def test_different_secondary_facts_can_add_information():
    reasoner = _reasoner()

    followup_only = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _available(
            _extract(
                "FOLLOWUP",
                "The customer wants another discussion about the proposal.",
            ),
        ),
    )

    followup_plus_approval = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _available(
            _extract(
                "FOLLOWUP",
                "The customer wants another discussion about the proposal.",
            ),
            _extract(
                "APPROVAL",
                "The quoted amount has budget approval.",
            ),
        ),
    )

    assert followup_only.interpretation_class == "quote_followup_pending"
    assert followup_only.decision_strength == "moderate"

    # Current reasoner precedence gives approval/acceptance priority
    # over follow-up when both are present.
    assert followup_plus_approval.interpretation_class == (
        "quote_pending_decision"
    )
    assert followup_plus_approval.decision_strength == "stronger"
    assert followup_plus_approval.support_level == "secondary_supported"
def test_irrelevant_context_does_not_count_as_information_gain():
    reasoner = _reasoner()

    control = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _empty(),
    )

    irrelevant = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _available(
            _extract(
                "IRRELEVANT",
                "The customer is discussing a separate store rollout "
                "and says nothing about this opportunity.",
            ),
        ),
    )

    assert irrelevant.interpretation_class == control.interpretation_class
    assert irrelevant.decision_strength == control.decision_strength
    assert irrelevant.recommended_focus == control.recommended_focus


def test_negated_context_does_not_count_as_positive_information_gain():
    reasoner = _reasoner()

    control = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _empty(),
    )

    negated = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _available(
            _extract(
                "NEGATED",
                "The customer does not want another discussion "
                "about the proposal.",
            ),
        ),
    )

    assert negated.interpretation_class == control.interpretation_class
    assert negated.decision_strength == control.decision_strength
    assert negated.recommended_focus == control.recommended_focus


def test_identity_rejected_context_does_not_count_as_information_gain():
    extractor = LexicalNormalizationSemanticExtractor()

    wrong_identity = extractor.extract(
        evidence_id="WRONG-ID",
        content=(
            "The customer wants another discussion about the proposal."
        ),
        source_system="secondary",
        record_id="WRONG-ID",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    ).evidence

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _available(wrong_identity),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.decision_strength == "moderate"
    assert result.support_level == "primary_only"


def test_two_distinct_facts_are_kept_as_distinct_evidence_items():
    followup = _extract(
        "FOLLOWUP",
        "The customer wants another discussion about the proposal.",
    )

    approval = _extract(
        "APPROVAL",
        "The quoted amount has budget approval.",
    )

    condition = _available(
        followup,
        approval,
    )

    assert len(condition.items) == 2

    assert condition.items[0].evidence_id == "FOLLOWUP"
    assert condition.items[1].evidence_id == "APPROVAL"

    assert condition.items[0].semantics.requests_followup is True
    assert condition.items[1].semantics.confirms_approval is True


def test_information_gain_is_not_just_number_of_records():
    reasoner = _reasoner()

    duplicate = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _available(
            _extract(
                "DUPLICATE-1",
                "The customer wants another discussion about the proposal.",
            ),
            _extract(
                "DUPLICATE-2",
                "The customer wants another discussion about the proposal.",
            ),
            _extract(
                "DUPLICATE-3",
                "The customer wants another discussion about the proposal.",
            ),
        ),
    )

    distinct = reasoner.evaluate(
        PrimaryState("quote_pending_decision"),
        _available(
            _extract(
                "DISTINCT-1",
                "The customer wants another discussion about the proposal.",
            ),
            _extract(
                "DISTINCT-2",
                "The quoted amount has budget approval.",
            ),
        ),
    )

    assert duplicate.interpretation_class == "quote_followup_pending"
    assert duplicate.decision_strength == "moderate"

    # Distinct approval evidence triggers the current approval branch
    # and therefore produces a stronger result.
    assert distinct.interpretation_class == "quote_pending_decision"
    assert distinct.decision_strength == "stronger"
    assert distinct.support_level == "secondary_supported"

    # The point of this experiment is that record count alone does not
    # determine the resulting state.
    assert duplicate.decision_strength != distinct.decision_strength