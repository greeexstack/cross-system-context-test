from __future__ import annotations

from types import SimpleNamespace

from experiment.v03.report import build_experiment_report
from experiment.v03.runner import TransitionMeasurement, TransitionSummary
from experiment.v03.transition_metrics import (
    TransitionDirection,
    ObservableState,
    TransitionObservation,
)
from experiment.v03.metrics import MetricSummary


def _measurement(
    case_id: str,
    *,
    correct: bool,
) -> TransitionMeasurement:
    return TransitionMeasurement(
        case_id=case_id,
        observation=TransitionObservation(
            base=ObservableState(
                "quote_pending_decision",
                "no_secondary_evidence",
                "moderate",
            ),
            variant=ObservableState(
                "quote_pending_decision",
                "primary_only",
                "moderate",
            ),
        ),
        expected_direction=TransitionDirection.PRESERVE,
        directional_correct=correct,
    )


def test_report_preserves_summary_metrics():
    summary = TransitionSummary(
        measurements=(
            _measurement("MR4", correct=True),
            _measurement("MR5", correct=False),
        ),
        directional_correctness=MetricSummary(
            total=2,
            correct=1,
            rate=0.5,
        ),
        unsupported_change_rate=0.5,
    )

    report = build_experiment_report(summary)

    assert report.total_cases == 2
    assert report.directional_correct == 1
    assert report.directional_correctness_rate == 0.5
    assert report.unsupported_change_rate == 0.5


def test_report_contains_case_level_observations():
    summary = TransitionSummary(
        measurements=(
            _measurement("MR4", correct=True),
        ),
        directional_correctness=MetricSummary(
            total=1,
            correct=1,
            rate=1.0,
        ),
        unsupported_change_rate=0.0,
    )

    report = build_experiment_report(summary)

    assert len(report.cases) == 1

    case = report.cases[0]

    assert case.case_id == "MR4"
    assert case.expected_direction == "preserve"
    assert case.directional_correct is True

    assert case.base_interpretation == "quote_pending_decision"
    assert case.base_support_level == "no_secondary_evidence"
    assert case.variant_support_level == "primary_only"