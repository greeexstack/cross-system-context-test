from __future__ import annotations

from dataclasses import dataclass

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import EvidenceCondition, IdentityQuality
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)


@dataclass(frozen=True)
class UpliftCase:
    case_id: str
    primary: PrimaryState
    secondary_text: str
    identity_quality: IdentityQuality
    expected_positive_uplift: bool


@dataclass(frozen=True)
class UpliftResult:
    case_id: str
    positive_uplift_observed: bool
    interpretation_changed: bool
    strength_increased: bool
    support_changed: bool
    focus_changed: bool


@dataclass(frozen=True)
class UpliftBatterySummary:
    total_cases: int
    positive_uplift_cases: int
    positive_uplift_rate: float
    interpretation_changes: int
    strength_increases: int
    support_changes: int
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
):
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


def _condition(item) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=(item,),
    )


def _empty_condition() -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=(),
    )


def _positive_uplift(
    control,
    enriched,
) -> bool:
    strength_order = {
        "weaker": 0,
        "moderate": 1,
        "stronger": 2,
    }

    strength_increased = (
        strength_order[enriched.decision_strength]
        > strength_order[control.decision_strength]
    )

    interpretation_changed = (
        enriched.interpretation_class
        != control.interpretation_class
    )

    focus_changed = (
        enriched.recommended_focus
        != control.recommended_focus
    )

    return (
        interpretation_changed
        or strength_increased
        or focus_changed
    )


def _run_case(case: UpliftCase) -> UpliftResult:
    reasoner = _reasoner()

    control = reasoner.evaluate(
        case.primary,
        _empty_condition(),
    )

    evidence = _extract(
        case.case_id,
        case.secondary_text,
        identity_quality=case.identity_quality,
    )

    enriched = reasoner.evaluate(
        case.primary,
        _condition(evidence),
    )

    strength_order = {
        "weaker": 0,
        "moderate": 1,
        "stronger": 2,
    }

    return UpliftResult(
        case_id=case.case_id,
        positive_uplift_observed=_positive_uplift(
            control,
            enriched,
        ),
        interpretation_changed=(
            enriched.interpretation_class
            != control.interpretation_class
        ),
        strength_increased=(
            strength_order[enriched.decision_strength]
            > strength_order[control.decision_strength]
        ),
        support_changed=(
            enriched.support_level
            != control.support_level
        ),
        focus_changed=(
            enriched.recommended_focus
            != control.recommended_focus
        ),
    )


def _summarize(
    cases: tuple[UpliftCase, ...],
    results: tuple[UpliftResult, ...],
) -> UpliftBatterySummary:
    total = len(results)

    positive_uplift_cases = sum(
        result.positive_uplift_observed
        for result in results
    )

    interpretation_changes = sum(
        result.interpretation_changed
        for result in results
    )

    strength_increases = sum(
        result.strength_increased
        for result in results
    )

    support_changes = sum(
        result.support_changed
        for result in results
    )

    focus_changes = sum(
        result.focus_changed
        for result in results
    )

    return UpliftBatterySummary(
        total_cases=total,
        positive_uplift_cases=positive_uplift_cases,
        positive_uplift_rate=(
            positive_uplift_cases / total
            if total
            else 0.0
        ),
        interpretation_changes=interpretation_changes,
        strength_increases=strength_increases,
        support_changes=support_changes,
        focus_changes=focus_changes,
    )


CASES = (
    UpliftCase(
        case_id="FOLLOWUP",
        primary=PrimaryState("quote_pending_decision"),
        secondary_text=(
            "The customer wants another discussion about the proposal."
        ),
        identity_quality=IdentityQuality.CONFIRMED,
        expected_positive_uplift=True,
    ),
    UpliftCase(
        case_id="APPROVAL",
        primary=PrimaryState("quote_pending_decision"),
        secondary_text=(
            "The quoted amount has budget approval."
        ),
        identity_quality=IdentityQuality.CONFIRMED,
        expected_positive_uplift=True,
    ),
    UpliftCase(
        case_id="COMPLETION-NEXT-STEP",
        primary=PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        secondary_text=(
            "The migration workshop is complete and the customer "
            "asks what comes next."
        ),
        identity_quality=IdentityQuality.CONFIRMED,
        expected_positive_uplift=True,
    ),
    UpliftCase(
        case_id="IRRELEVANT",
        primary=PrimaryState("quote_pending_decision"),
        secondary_text=(
            "The customer is discussing a separate store rollout "
            "and says nothing about this opportunity."
        ),
        identity_quality=IdentityQuality.CONFIRMED,
        expected_positive_uplift=False,
    ),
    UpliftCase(
        case_id="NEGATED",
        primary=PrimaryState("quote_pending_decision"),
        secondary_text=(
            "The customer does not want another discussion "
            "about the proposal."
        ),
        identity_quality=IdentityQuality.CONFIRMED,
        expected_positive_uplift=False,
    ),
    UpliftCase(
        case_id="WRONG-IDENTITY",
        primary=PrimaryState("quote_pending_decision"),
        secondary_text=(
            "The customer wants another discussion about the proposal."
        ),
        identity_quality=IdentityQuality.NO_MATCH,
        expected_positive_uplift=False,
    ),
)


def test_uplift_battery_matches_expected_case_directions():
    results = tuple(
        _run_case(case)
        for case in CASES
    )

    for case, result in zip(CASES, results):
        assert result.positive_uplift_observed == (
            case.expected_positive_uplift
        )


def test_uplift_battery_has_three_positive_and_three_control_cases():
    results = tuple(
        _run_case(case)
        for case in CASES
    )

    summary = _summarize(
        CASES,
        results,
    )

    assert summary.total_cases == 6
    assert summary.positive_uplift_cases == 3
    assert summary.positive_uplift_rate == 0.5


def test_uplift_battery_detects_expected_interpretation_changes():
    results = tuple(
        _run_case(case)
        for case in CASES
    )

    summary = _summarize(
        CASES,
        results,
    )

    assert summary.interpretation_changes == 1


def test_uplift_battery_detects_expected_strength_increases():
    results = tuple(
        _run_case(case)
        for case in CASES
    )

    summary = _summarize(
        CASES,
        results,
    )

    assert summary.strength_increases == 1


def test_control_cases_have_no_positive_uplift():
    control_cases = tuple(
        case
        for case in CASES
        if not case.expected_positive_uplift
    )

    results = tuple(
        _run_case(case)
        for case in control_cases
    )

    assert all(
        not result.positive_uplift_observed
        for result in results
    )


def test_positive_cases_have_positive_uplift():
    positive_cases = tuple(
        case
        for case in CASES
        if case.expected_positive_uplift
    )

    results = tuple(
        _run_case(case)
        for case in positive_cases
    )

    assert all(
        result.positive_uplift_observed
        for result in results
    )


def test_wrong_identity_is_not_counted_as_positive_uplift():
    case = next(
        case
        for case in CASES
        if case.case_id == "WRONG-IDENTITY"
    )

    result = _run_case(case)

    assert result.positive_uplift_observed is False
    assert result.strength_increased is False
    assert result.focus_changed is False


def test_negation_is_not_counted_as_positive_uplift():
    case = next(
        case
        for case in CASES
        if case.case_id == "NEGATED"
    )

    result = _run_case(case)

    assert result.positive_uplift_observed is False
    assert result.strength_increased is False
    assert result.focus_changed is False


def test_irrelevance_is_not_counted_as_positive_uplift():
    case = next(
        case
        for case in CASES
        if case.case_id == "IRRELEVANT"
    )

    result = _run_case(case)

    assert result.positive_uplift_observed is False
    assert result.strength_increased is False
    assert result.focus_changed is False


def test_uplift_battery_summary_is_deterministic():
    first_results = tuple(
        _run_case(case)
        for case in CASES
    )

    second_results = tuple(
        _run_case(case)
        for case in CASES
    )

    first_summary = _summarize(
        CASES,
        first_results,
    )

    second_summary = _summarize(
        CASES,
        second_results,
    )

    assert first_summary == second_summary
    assert first_results == second_results