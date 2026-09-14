from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .evidence import EvidenceCondition
from .metrics import (
    MetricSummary,
    directional_correctness_summary,
    unsupported_change_rate,
)
from .reasoner import PrimaryState
from .transition_metrics import (
    TransitionDirection,
    TransitionExpectation,
    TransitionObservation,
    directional_correctness,
    observe,
)


@dataclass(frozen=True)
class TransitionCase:
    """
    One paired-state experimental trial.

    The expected direction is evaluator-side metadata and must never be
    passed into the system under test.
    """

    case_id: str
    primary: PrimaryState
    secondary: EvidenceCondition
    expected_direction: TransitionDirection


@dataclass(frozen=True)
class TransitionMeasurement:
    case_id: str
    observation: TransitionObservation
    expected_direction: TransitionDirection
    directional_correct: bool


@dataclass(frozen=True)
class TransitionSummary:
    measurements: tuple[TransitionMeasurement, ...]
    directional_correctness: MetricSummary
    unsupported_change_rate: float


class V03TransitionRunner:
    """
    Minimal black-box transition measurement harness.

    The runner supplies primary and secondary evidence to the reasoner,
    observes the resulting states, and applies evaluator-side expectations.

    Expected relations never enter the reasoner.
    """

    def __init__(
        self,
        reasoner,
        *,
        evaluator: Callable[
            [TransitionObservation, TransitionExpectation],
            bool
        ] = directional_correctness,
    ) -> None:
        self.reasoner = reasoner
        self.evaluator = evaluator

    def run_case(self, case: TransitionCase) -> TransitionMeasurement:
        base = self.reasoner.evaluate(
            case.primary,
            EvidenceCondition(
                availability="available",
                items=(),
            ),
        )

        variant = self.reasoner.evaluate(
            case.primary,
            case.secondary,
        )

        observation = observe(base, variant)

        passed = self.evaluator(
            observation,
            TransitionExpectation(case.expected_direction),
        )

        return TransitionMeasurement(
            case_id=case.case_id,
            observation=observation,
            expected_direction=case.expected_direction,
            directional_correct=passed,
        )

    def run(
        self,
        cases: Iterable[TransitionCase],
    ) -> TransitionSummary:
        measurements = tuple(
            self.run_case(case)
            for case in cases
        )

        directional_results = tuple(
            measurement.directional_correct
            for measurement in measurements
        )

        metric_inputs = tuple(
            (
                measurement.observation,
                TransitionExpectation(
                    measurement.expected_direction
                ),
            )
            for measurement in measurements
        )

        return TransitionSummary(
            measurements=measurements,
            directional_correctness=(
                directional_correctness_summary(
                    directional_results
                )
            ),
            unsupported_change_rate=(
                unsupported_change_rate(metric_inputs)
            ),
        )