from __future__ import annotations

from dataclasses import dataclass

from .runner import TransitionMeasurement, TransitionSummary


@dataclass(frozen=True)
class CaseReport:
    case_id: str
    expected_direction: str
    directional_correct: bool

    base_interpretation: str
    base_support_level: str
    base_decision_strength: str
    base_recommended_focus: str | None

    variant_interpretation: str
    variant_support_level: str
    variant_decision_strength: str
    variant_recommended_focus: str | None


@dataclass(frozen=True)
class ExperimentReport:
    total_cases: int
    directional_correct: int
    directional_correctness_rate: float
    unsupported_change_rate: float
    cases: tuple[CaseReport, ...]


def _case_report(
    measurement: TransitionMeasurement,
) -> CaseReport:
    base = measurement.observation.base
    variant = measurement.observation.variant

    return CaseReport(
        case_id=measurement.case_id,
        expected_direction=measurement.expected_direction.value,
        directional_correct=measurement.directional_correct,
        base_interpretation=base.interpretation_class,
        base_support_level=base.support_level,
        base_decision_strength=base.decision_strength,
        base_recommended_focus=base.recommended_focus,
        variant_interpretation=variant.interpretation_class,
        variant_support_level=variant.support_level,
        variant_decision_strength=variant.decision_strength,
        variant_recommended_focus=variant.recommended_focus,
    )


def build_experiment_report(
    summary: TransitionSummary,
) -> ExperimentReport:
    return ExperimentReport(
        total_cases=summary.directional_correctness.total,
        directional_correct=summary.directional_correctness.correct,
        directional_correctness_rate=(
            summary.directional_correctness.rate
        ),
        unsupported_change_rate=summary.unsupported_change_rate,
        cases=tuple(
            _case_report(measurement)
            for measurement in summary.measurements
        ),
    )