"""
Correctness measurement validity experiment.

Research question:

Can directional correctness / positive uplift distinguish genuine decision
improvement from:
    - already-correct decisions,
    - harmful context,
    - and coincidental agreement with the expected transition?

Design:

Four controlled quadrants:

A. Primary correct -> enriched correct
B. Primary incorrect -> enriched correct
C. Primary correct -> enriched incorrect
D. Primary incorrect -> enriched incorrect

The frozen scenario truth is an experiment-side oracle. It is NEVER passed
to the V03 reasoner.

This is a controlled falsification experiment, not a real-world correctness
benchmark. The goal is to determine whether the current transition/uplift
proxies are equivalent to correctness improvement. They should not be
assumed equivalent.

No production code is changed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    EvidenceCondition,
    EvidenceIdentity,
    EvidenceProvenance,
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)
from experiment.v03.transition_metrics import (
    TransitionDirection,
    TransitionExpectation,
    directional_correctness,
    observe,
)


DECISION_TRUTH = {
    "quote_pending_decision",
    "quote_followup_pending",
}


@dataclass(frozen=True)
class CorrectnessCase:
    case_id: str
    description: str
    primary: PrimaryState
    secondary: EvidenceCondition

    # Frozen experiment-side business truth.
    #
    # These values are deliberately not supplied to the reasoner.
    correct_primary_interpretation: str
    correct_enriched_interpretation: str

    expected_direction: TransitionDirection


@dataclass(frozen=True)
class MeasurementResult:
    case_id: str
    primary_interpretation: str
    enriched_interpretation: str

    primary_correct: bool
    enriched_correct: bool

    actual_improvement: bool
    actual_harm: bool

    directional_correct: bool
    positive_uplift: bool


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _evidence(
    evidence_id: str,
    *,
    content: str,
    semantics: EvidenceSemantics,
) -> SemanticEvidence:
    return SemanticEvidence(
        evidence_id=evidence_id,
        content=content,
        provenance=EvidenceProvenance(
            source_system="synthetic",
            record_id=evidence_id,
            occurred_at=datetime(
                2026,
                9,
                12,
                10,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        ),
        identity=EvidenceIdentity(
            customer_id="C001",
            quality=IdentityQuality.CONFIRMED,
        ),
        semantics=semantics,
    )


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


def _irrelevant_context(
    evidence_id: str,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        content=(
            "The customer is discussing a separate store rollout "
            "and says nothing about this quoted opportunity."
        ),
        semantics=EvidenceSemantics(
            topic="store_rollout",
            concerns_same_work_item=False,
        ),
    )


def _valid_followup_context(
    evidence_id: str,
) -> SemanticEvidence:
    return _evidence(
        evidence_id,
        content=(
            "The customer wants another discussion about the proposal."
        ),
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
    )


def _misleading_followup_context(
    evidence_id: str,
) -> SemanticEvidence:
    """
    Semantic payload intentionally looks like valid proposal follow-up.

    The frozen scenario truth says this context refers to an archived /
    superseded proposal state and therefore must not change the current
    decision.

    That hidden truth is never passed into the reasoner.
    """
    return _evidence(
        evidence_id,
        content=(
            "The customer wants another discussion about the archived "
            "proposal version."
        ),
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
    )


def _case_a_primary_and_enriched_correct() -> CorrectnessCase:
    return CorrectnessCase(
        case_id="A",
        description=(
            "Primary decision is already correct and irrelevant context "
            "does not change it."
        ),
        primary=PrimaryState(
            "quote_pending_decision"
        ),
        secondary=_condition(
            _irrelevant_context("A-SECONDARY"),
        ),
        correct_primary_interpretation=(
            "quote_pending_decision"
        ),
        correct_enriched_interpretation=(
            "quote_pending_decision"
        ),
        expected_direction=TransitionDirection.PRESERVE,
    )


def _case_b_primary_wrong_enriched_correct() -> CorrectnessCase:
    return CorrectnessCase(
        case_id="B",
        description=(
            "Primary-only output misses a real follow-up state; "
            "relevant cross-system context supplies the missing fact."
        ),
        primary=PrimaryState(
            "quote_pending_decision"
        ),
        secondary=_condition(
            _valid_followup_context("B-SECONDARY"),
        ),
        correct_primary_interpretation=(
            "quote_followup_pending"
        ),
        correct_enriched_interpretation=(
            "quote_followup_pending"
        ),
        expected_direction=TransitionDirection.CHANGE,
    )


def _case_c_primary_correct_enriched_wrong() -> CorrectnessCase:
    return CorrectnessCase(
        case_id="C",
        description=(
            "Primary-only output is correct, but misleading secondary "
            "context causes the reasoner to change the interpretation."
        ),
        primary=PrimaryState(
            "quote_pending_decision"
        ),
        secondary=_condition(
            _misleading_followup_context("C-SECONDARY"),
        ),
        correct_primary_interpretation=(
            "quote_pending_decision"
        ),
        correct_enriched_interpretation=(
            "quote_pending_decision"
        ),
        expected_direction=TransitionDirection.PRESERVE,
    )


def _case_d_both_incorrect() -> CorrectnessCase:
    return CorrectnessCase(
        case_id="D",
        description=(
            "The true decision is follow-up pending, but the available "
            "context is irrelevant, so both primary-only and enriched "
            "outputs remain wrong."
        ),
        primary=PrimaryState(
            "quote_pending_decision"
        ),
        secondary=_condition(
            _irrelevant_context("D-SECONDARY"),
        ),
        correct_primary_interpretation=(
            "quote_followup_pending"
        ),
        correct_enriched_interpretation=(
            "quote_followup_pending"
        ),
        expected_direction=TransitionDirection.PRESERVE,
    )


CASES = (
    _case_a_primary_and_enriched_correct(),
    _case_b_primary_wrong_enriched_correct(),
    _case_c_primary_correct_enriched_wrong(),
    _case_d_both_incorrect(),
)


def _positive_uplift(
    observation,
) -> bool:
    """
    Test-layer copy of the current uplift concept.

    This intentionally mirrors the current V03 uplift definition:

        interpretation changed
        OR decision strength increased
        OR recommended focus changed

    It is being tested as a proxy, not treated as ground truth.
    """
    strength_order = {
        "weaker": 0,
        "moderate": 1,
        "stronger": 2,
    }

    strength_increased = (
        strength_order[
            observation.base.decision_strength
        ]
        <
        strength_order[
            observation.variant.decision_strength
        ]
    )

    focus_changed = (
        observation.base.recommended_focus
        != observation.variant.recommended_focus
    )

    return (
        observation.interpretation_changed
        or strength_increased
        or focus_changed
    )


def _run_case(
    case: CorrectnessCase,
) -> MeasurementResult:
    reasoner = _reasoner()

    base_result = reasoner.evaluate(
        case.primary,
        _empty_condition(),
    )

    enriched_result = reasoner.evaluate(
        case.primary,
        case.secondary,
    )

    observation = observe(
        base_result,
        enriched_result,
    )

    primary_correct = (
        observation.base.interpretation_class
        == case.correct_primary_interpretation
    )

    enriched_correct = (
        observation.variant.interpretation_class
        == case.correct_enriched_interpretation
    )

    actual_improvement = (
        not primary_correct
        and enriched_correct
    )

    actual_harm = (
        primary_correct
        and not enriched_correct
    )

    directional_correct = directional_correctness(
        observation,
        TransitionExpectation(
            case.expected_direction
        ),
    )

    positive_uplift = _positive_uplift(
        observation
    )

    return MeasurementResult(
        case_id=case.case_id,
        primary_interpretation=(
            observation.base.interpretation_class
        ),
        enriched_interpretation=(
            observation.variant.interpretation_class
        ),
        primary_correct=primary_correct,
        enriched_correct=enriched_correct,
        actual_improvement=actual_improvement,
        actual_harm=actual_harm,
        directional_correct=directional_correct,
        positive_uplift=positive_uplift,
    )


def _run_all() -> tuple[MeasurementResult, ...]:
    return tuple(
        _run_case(case)
        for case in CASES
    )


def test_four_quadrants_are_constructed():
    results = _run_all()

    assert len(results) == 4
    assert {
        result.case_id
        for result in results
    } == {"A", "B", "C", "D"}


def test_case_a_primary_and_enriched_are_both_correct():
    result = _run_case(
        _case_a_primary_and_enriched_correct()
    )

    assert result.primary_correct is True
    assert result.enriched_correct is True
    assert result.actual_improvement is False
    assert result.actual_harm is False

    assert result.directional_correct is True
    assert result.positive_uplift is False


def test_case_b_is_genuine_decision_improvement():
    result = _run_case(
        _case_b_primary_wrong_enriched_correct()
    )

    assert result.primary_interpretation == (
        "quote_pending_decision"
    )
    assert result.enriched_interpretation == (
        "quote_followup_pending"
    )

    assert result.primary_correct is False
    assert result.enriched_correct is True

    assert result.actual_improvement is True
    assert result.actual_harm is False

    assert result.directional_correct is True
    assert result.positive_uplift is True


def test_case_c_is_harmful_context_not_improvement():
    result = _run_case(
        _case_c_primary_correct_enriched_wrong()
    )

    assert result.primary_interpretation == (
        "quote_pending_decision"
    )
    assert result.enriched_interpretation == (
        "quote_followup_pending"
    )

    assert result.primary_correct is True
    assert result.enriched_correct is False

    assert result.actual_improvement is False
    assert result.actual_harm is True

    # The benchmark expectation is PRESERVE, so directional correctness
    # correctly rejects the harmful interpretation change.
    assert result.directional_correct is False

    # But the uplift proxy sees interpretation change and calls it positive.
    # This is a direct demonstration that "positive uplift" is not equivalent
    # to actual decision improvement.
    assert result.positive_uplift is True


def test_case_d_is_coincidental_directional_success_without_improvement():
    result = _run_case(
        _case_d_both_incorrect()
    )

    assert result.primary_interpretation == (
        "quote_pending_decision"
    )
    assert result.enriched_interpretation == (
        "quote_pending_decision"
    )

    assert result.primary_correct is False
    assert result.enriched_correct is False

    assert result.actual_improvement is False
    assert result.actual_harm is False

    # The system correctly preserved its observable state according to the
    # transition expectation, but both decisions are still incorrect.
    assert result.directional_correct is True
    assert result.positive_uplift is False


def test_directional_correctness_is_not_equivalent_to_improvement():
    results = _run_all()

    directional_successes = {
        result.case_id
        for result in results
        if result.directional_correct
    }

    actual_improvements = {
        result.case_id
        for result in results
        if result.actual_improvement
    }

    assert directional_successes == {
        "A",
        "B",
        "D",
    }

    assert actual_improvements == {
        "B",
    }

    assert directional_successes != actual_improvements


def test_positive_uplift_is_not_equivalent_to_improvement():
    results = _run_all()

    uplift_cases = {
        result.case_id
        for result in results
        if result.positive_uplift
    }

    improvement_cases = {
        result.case_id
        for result in results
        if result.actual_improvement
    }

    assert uplift_cases == {
        "B",
        "C",
    }

    assert improvement_cases == {
        "B",
    }

    assert uplift_cases != improvement_cases


def test_harm_is_distinct_from_lack_of_improvement():
    results = _run_all()

    harm_cases = {
        result.case_id
        for result in results
        if result.actual_harm
    }

    non_improvement_cases = {
        result.case_id
        for result in results
        if not result.actual_improvement
    }

    assert harm_cases == {"C"}
    assert non_improvement_cases == {
        "A",
        "C",
        "D",
    }


def test_correctness_partition_is_complete():
    results = _run_all()

    for result in results:
        assert not (
            result.actual_improvement
            and result.actual_harm
        )

    classified = {
        result.case_id
        for result in results
        if (
            result.actual_improvement
            or result.actual_harm
            or (
                result.primary_correct
                and result.enriched_correct
            )
            or (
                not result.primary_correct
                and not result.enriched_correct
            )
        )
    }

    assert classified == {
        "A",
        "B",
        "C",
        "D",
    }


def test_case_truth_is_not_injected_into_reasoner():
    """
    The frozen truth exists only inside CorrectnessCase.

    The V03 reasoner receives only:
        primary
        secondary

    It never receives:
        correct_primary_interpretation
        correct_enriched_interpretation
        expected_direction

    This is an architectural guard against evaluator leakage.
    """
    case = _case_b_primary_wrong_enriched_correct()

    reasoner = _reasoner()

    result = reasoner.evaluate(
        case.primary,
        case.secondary,
    )

    assert result.interpretation_class == (
        "quote_followup_pending"
    )

    assert not hasattr(
        reasoner,
        "correct_primary_interpretation",
    )
    assert not hasattr(
        reasoner,
        "correct_enriched_interpretation",
    )
    assert not hasattr(
        reasoner,
        "expected_direction",
    )


def test_expected_direction_is_evaluator_side_only():
    case = _case_c_primary_correct_enriched_wrong()

    reasoner = _reasoner()

    result = reasoner.evaluate(
        case.primary,
        case.secondary,
    )

    assert result.interpretation_class == (
        "quote_followup_pending"
    )

    # The reasoner cannot know that this should have been PRESERVE.
    # That is deliberately determined outside the system under test.
    assert case.expected_direction == (
        TransitionDirection.PRESERVE
    )


def test_actual_improvement_requires_correctness_transition():
    results = _run_all()

    for result in results:
        assert result.actual_improvement == (
            not result.primary_correct
            and result.enriched_correct
        )


def test_actual_harm_requires_correctness_regression():
    results = _run_all()

    for result in results:
        assert result.actual_harm == (
            result.primary_correct
            and not result.enriched_correct
        )


def test_measurement_summary_exposes_proxy_mismatch():
    results = _run_all()

    directional_correctness_rate = (
        sum(
            result.directional_correct
            for result in results
        )
        / len(results)
    )

    positive_uplift_rate = (
        sum(
            result.positive_uplift
            for result in results
        )
        / len(results)
    )

    improvement_rate = (
        sum(
            result.actual_improvement
            for result in results
        )
        / len(results)
    )

    harm_rate = (
        sum(
            result.actual_harm
            for result in results
        )
        / len(results)
    )

    assert directional_correctness_rate == 0.75
    assert positive_uplift_rate == 0.50
    assert improvement_rate == 0.25
    assert harm_rate == 0.25


def test_this_experiment_is_a_falsification_not_a_full_benchmark():
    """
    Four cases are deliberately sufficient to disprove equivalence between
    proxy metrics and correctness if a mismatch appears.

    They are NOT sufficient to estimate real-world accuracy, prevalence,
    calibration, or statistical performance.
    """
    results = _run_all()

    assert len(results) == 4
    assert any(
        result.directional_correct
        and not result.actual_improvement
        for result in results
    )

    assert any(
        result.positive_uplift
        and not result.actual_improvement
        for result in results
    )