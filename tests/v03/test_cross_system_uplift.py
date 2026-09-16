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
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)


@dataclass(frozen=True)
class PairedCase:
    case_id: str
    primary: PrimaryState
    secondary_text: str


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


def _condition(text: str) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=(
            _extract("SECONDARY", text),
        ),
    )


def test_primary_only_is_the_control_condition():
    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.support_level == "no_secondary_evidence"
    assert result.decision_strength == "moderate"
    assert result.recommended_focus is None


def test_relevant_secondary_context_changes_the_interpretation():
    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            "The customer wants another discussion about the proposal."
        ),
    )

    assert result.interpretation_class == "quote_followup_pending"

    control = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    assert control.interpretation_class == "quote_pending_decision"
    assert result.interpretation_class != control.interpretation_class


def test_secondary_context_can_increase_decision_strength_without_changing_class():
    control = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    enriched = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            "Funding for the proposed price has been authorized."
        ),
    )

    assert control.interpretation_class == "quote_pending_decision"
    assert enriched.interpretation_class == "quote_pending_decision"

    assert control.decision_strength == "moderate"
    assert enriched.decision_strength == "stronger"


def test_irrelevant_secondary_context_does_not_create_cross_system_uplift():
    control = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    enriched = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            "The customer is discussing a separate store rollout "
            "and says nothing about this opportunity."
        ),
    )

    assert enriched.interpretation_class == control.interpretation_class
    assert enriched.decision_strength == control.decision_strength


def test_wrong_identity_does_not_create_cross_system_uplift():
    extractor = LexicalNormalizationSemanticExtractor()

    wrong_identity = extractor.extract(
        evidence_id="WRONG-CUSTOMER",
        content=(
            "The customer wants another discussion about the proposal."
        ),
        source_system="secondary",
        record_id="WRONG-CUSTOMER",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    ).evidence

    control = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    enriched = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(wrong_identity,),
        ),
    )

    assert enriched.interpretation_class == control.interpretation_class
    assert enriched.decision_strength == control.decision_strength
    assert enriched.recommended_focus == control.recommended_focus


def test_cross_system_uplift_has_to_be_directionally_meaningful():
    cases = (
        PairedCase(
            case_id="UPLIFT-FOLLOWUP",
            primary=PrimaryState("quote_pending_decision"),
            secondary_text=(
                "The customer wants another discussion about the proposal."
            ),
        ),
        PairedCase(
            case_id="UPLIFT-APPROVAL",
            primary=PrimaryState("quote_pending_decision"),
            secondary_text=(
                "Funding for the proposed price has been authorized."
            ),
        ),
        PairedCase(
            case_id="UPLIFT-NEXT-STEP",
            primary=PrimaryState(
                "service_completed_next_step_unrecorded"
            ),
            secondary_text=(
                "The migration workshop is complete and the customer "
                "asks what comes next."
            ),
        ),
    )

    reasoner = _reasoner()

    for case in cases:
        control = reasoner.evaluate(
            case.primary,
            EvidenceCondition(
                availability="available",
                items=(),
            ),
        )

        enriched = reasoner.evaluate(
            case.primary,
            _condition(case.secondary_text),
        )

        assert enriched.interpretation_class is not None
        assert enriched.support_level is not None
        assert enriched.decision_strength is not None

        assert (
            enriched.interpretation_class != control.interpretation_class
            or enriched.support_level != control.support_level
            or enriched.decision_strength != control.decision_strength
            or enriched.recommended_focus != control.recommended_focus
        )


def test_unsupported_secondary_context_has_zero_expected_uplift():
    control = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    cases = (
        (
            "The customer does not want another discussion about "
            "the proposal."
        ),
        (
            "The customer is discussing a separate store rollout "
            "and says nothing about this opportunity."
        ),
        (
            "The migration workshop is not complete and the customer "
            "asks what comes next."
        ),
    )

    for text in cases:
        enriched = _reasoner().evaluate(
            PrimaryState("quote_pending_decision"),
            _condition(text),
        )

        assert (
            enriched.interpretation_class == control.interpretation_class
            or enriched.decision_strength == control.decision_strength
        )