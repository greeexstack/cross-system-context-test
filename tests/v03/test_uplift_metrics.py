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
class UpliftObservation:
    case_id: str

    primary_interpretation: str
    enriched_interpretation: str

    primary_support: str
    enriched_support: str

    primary_strength: str
    enriched_strength: str

    primary_focus: str | None
    enriched_focus: str | None

    @property
    def interpretation_changed(self) -> bool:
        return (
            self.primary_interpretation
            != self.enriched_interpretation
        )

    @property
    def support_changed(self) -> bool:
        return self.primary_support != self.enriched_support

    @property
    def strength_changed(self) -> bool:
        return self.primary_strength != self.enriched_strength

    @property
    def focus_changed(self) -> bool:
        return self.primary_focus != self.enriched_focus

    @property
    def any_observable_change(self) -> bool:
        """
        True when any externally visible result field changed.

        This intentionally includes a transition such as:

            no_secondary_evidence -> primary_only

        even though that is NOT positive information gain.
        """
        return (
            self.interpretation_changed
            or self.support_changed
            or self.strength_changed
            or self.focus_changed
        )

    @property
    def positive_uplift(self) -> bool:
        """
        True only when secondary context produces a substantive
        improvement in interpretation, decision strength, or actionability.

        A change from no_secondary_evidence to primary_only is not uplift.
        """
        return (
            self.interpretation_changed
            or self.strength_increased
            or self.focus_changed
        )

    @property
    def strength_increased(self) -> bool:
        strength_order = {
            "weaker": 0,
            "moderate": 1,
            "stronger": 2,
        }

        primary_value = strength_order[self.primary_strength]
        enriched_value = strength_order[self.enriched_strength]

        return enriched_value > primary_value


@dataclass(frozen=True)
class UpliftSummary:
    total_cases: int

    cases_with_observable_change: int
    observable_change_rate: float

    cases_with_positive_uplift: int
    positive_uplift_rate: float

    interpretation_changes: int
    support_changes: int
    strength_changes: int
    focus_changes: int


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


def _condition(
    *items: SemanticEvidence,
) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=tuple(items),
    )


def _empty_condition() -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=(),
    )


def _observe(
    case_id: str,
    primary: PrimaryState,
    secondary: EvidenceCondition,
) -> UpliftObservation:
    reasoner = _reasoner()

    control = reasoner.evaluate(
        primary,
        _empty_condition(),
    )

    enriched = reasoner.evaluate(
        primary,
        secondary,
    )

    return UpliftObservation(
        case_id=case_id,
        primary_interpretation=control.interpretation_class,
        enriched_interpretation=enriched.interpretation_class,
        primary_support=control.support_level,
        enriched_support=enriched.support_level,
        primary_strength=control.decision_strength,
        enriched_strength=enriched.decision_strength,
        primary_focus=control.recommended_focus,
        enriched_focus=enriched.recommended_focus,
    )


def _summarize(
    observations: tuple[UpliftObservation, ...],
) -> UpliftSummary:
    total = len(observations)

    observable_changes = sum(
        observation.any_observable_change
        for observation in observations
    )

    positive_uplifts = sum(
        observation.positive_uplift
        for observation in observations
    )

    interpretation_changes = sum(
        observation.interpretation_changed
        for observation in observations
    )

    support_changes = sum(
        observation.support_changed
        for observation in observations
    )

    strength_changes = sum(
        observation.strength_changed
        for observation in observations
    )

    focus_changes = sum(
        observation.focus_changed
        for observation in observations
    )

    return UpliftSummary(
        total_cases=total,
        cases_with_observable_change=observable_changes,
        observable_change_rate=(
            observable_changes / total
            if total
            else 0.0
        ),
        cases_with_positive_uplift=positive_uplifts,
        positive_uplift_rate=(
            positive_uplifts / total
            if total
            else 0.0
        ),
        interpretation_changes=interpretation_changes,
        support_changes=support_changes,
        strength_changes=strength_changes,
        focus_changes=focus_changes,
    )


def test_followup_creates_positive_cross_system_uplift():
    observation = _observe(
        "FOLLOWUP",
        PrimaryState("quote_pending_decision"),
        _condition(
            _extract(
                "FOLLOWUP",
                "The customer wants another discussion about the proposal.",
            ),
        ),
    )

    assert observation.interpretation_changed is True
    assert observation.support_changed is True
    assert observation.any_observable_change is True
    assert observation.positive_uplift is True


def test_approval_creates_positive_cross_system_uplift():
    observation = _observe(
        "APPROVAL",
        PrimaryState("quote_pending_decision"),
        _condition(
            _extract(
                "APPROVAL",
                "The quoted amount has budget approval.",
            ),
        ),
    )

    assert observation.interpretation_changed is False
    assert observation.support_changed is True
    assert observation.strength_changed is True
    assert observation.any_observable_change is True
    assert observation.positive_uplift is True


def test_irrelevant_context_has_no_positive_uplift():
    observation = _observe(
        "IRRELEVANT",
        PrimaryState("quote_pending_decision"),
        _condition(
            _extract(
                "IRRELEVANT",
                "The customer is discussing a separate store rollout "
                "and says nothing about this opportunity.",
            ),
        ),
    )

    assert observation.any_observable_change is True
    assert observation.positive_uplift is False


def test_negated_context_has_no_positive_uplift():
    observation = _observe(
        "NEGATED",
        PrimaryState("quote_pending_decision"),
        _condition(
            _extract(
                "NEGATED",
                "The customer does not want another discussion "
                "about the proposal.",
            ),
        ),
    )

    assert observation.any_observable_change is True
    assert observation.positive_uplift is False


def test_wrong_identity_has_no_positive_uplift():
    observation = _observe(
        "WRONG_IDENTITY",
        PrimaryState("quote_pending_decision"),
        _condition(
            _extract(
                "WRONG_IDENTITY",
                "The customer wants another discussion about the proposal.",
                identity_quality=IdentityQuality.NO_MATCH,
            ),
        ),
    )

    assert observation.any_observable_change is True
    assert observation.positive_uplift is False


def test_multi_fact_enrichment_can_create_positive_uplift():
    observation = _observe(
        "FOLLOWUP_PLUS_APPROVAL",
        PrimaryState("quote_pending_decision"),
        _condition(
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

    assert observation.any_observable_change is True
    assert observation.support_changed is True
    assert observation.strength_changed is True
    assert observation.positive_uplift is True


def test_uplift_summary_separates_observable_change_from_positive_uplift():
    observations = (
        _observe(
            "FOLLOWUP",
            PrimaryState("quote_pending_decision"),
            _condition(
                _extract(
                    "FOLLOWUP",
                    "The customer wants another discussion about the proposal.",
                ),
            ),
        ),
        _observe(
            "APPROVAL",
            PrimaryState("quote_pending_decision"),
            _condition(
                _extract(
                    "APPROVAL",
                    "The quoted amount has budget approval.",
                ),
            ),
        ),
        _observe(
            "IRRELEVANT",
            PrimaryState("quote_pending_decision"),
            _condition(
                _extract(
                    "IRRELEVANT",
                    "The customer is discussing a separate store rollout "
                    "and says nothing about this opportunity.",
                ),
            ),
        ),
    )

    summary = _summarize(observations)

    assert summary.total_cases == 3

    # Every enriched case changes at least one visible output field.
    assert summary.cases_with_observable_change == 3
    assert summary.observable_change_rate == 1.0

    # Only the relevant contextual cases produce actual uplift.
    assert summary.cases_with_positive_uplift == 2
    assert summary.positive_uplift_rate == 2 / 3

    assert summary.interpretation_changes == 1
    assert summary.support_changes == 3
    assert summary.strength_changes == 1
    assert summary.focus_changes == 0


def test_uplift_summary_has_zero_positive_uplift_for_control_cases():
    observations = (
        _observe(
            "IRRELEVANT-1",
            PrimaryState("quote_pending_decision"),
            _condition(
                _extract(
                    "IRRELEVANT-1",
                    "The customer is discussing a separate store rollout "
                    "and says nothing about this opportunity.",
                ),
            ),
        ),
        _observe(
            "NEGATED-1",
            PrimaryState("quote_pending_decision"),
            _condition(
                _extract(
                    "NEGATED-1",
                    "The customer does not want another discussion "
                    "about the proposal.",
                ),
            ),
        ),
        _observe(
            "WRONG-IDENTITY-1",
            PrimaryState("quote_pending_decision"),
            _condition(
                _extract(
                    "WRONG-IDENTITY-1",
                    "The customer wants another discussion about the proposal.",
                    identity_quality=IdentityQuality.NO_MATCH,
                ),
            ),
        ),
    )

    summary = _summarize(observations)

    assert summary.total_cases == 3

    # These cases may produce an observable support-state transition
    # from "no secondary evidence" to "primary only", but that is not
    # positive cross-system uplift.
    assert summary.cases_with_positive_uplift == 0
    assert summary.positive_uplift_rate == 0.0


def test_uplift_measurement_keeps_control_and_enriched_results_distinct():
    observation = _observe(
        "FOLLOWUP",
        PrimaryState("quote_pending_decision"),
        _condition(
            _extract(
                "FOLLOWUP",
                "The customer wants another discussion about the proposal.",
            ),
        ),
    )

    assert observation.primary_interpretation == "quote_pending_decision"
    assert observation.enriched_interpretation == "quote_followup_pending"

    assert observation.primary_support == "no_secondary_evidence"
    assert observation.enriched_support == (
        "supported_by_secondary_context"
    )

    assert observation.primary_strength == "moderate"
    assert observation.enriched_strength == "moderate"

    assert observation.primary_focus is None
    assert observation.enriched_focus is None

    assert observation.any_observable_change is True
    assert observation.positive_uplift is True