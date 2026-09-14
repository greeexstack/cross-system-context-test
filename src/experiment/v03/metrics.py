from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .transition_metrics import (
    TransitionDirection,
    TransitionExpectation,
    TransitionObservation,
)


@dataclass(frozen=True)
class MetricSummary:
    total: int
    correct: int
    rate: float


def directional_correctness_summary(
    values: Iterable[bool],
) -> MetricSummary:
    values = tuple(values)

    total = len(values)
    correct = sum(values)

    return MetricSummary(
        total=total,
        correct=correct,
        rate=(correct / total) if total else 0.0,
    )


def unsupported_change(
    observation: TransitionObservation,
    expectation: TransitionExpectation,
) -> bool:
    """
    Return True when a preservation trial materially changes the
    observable primary state.

    This metric is only meaningful for preservation expectations.
    """

    if expectation.direction != TransitionDirection.PRESERVE:
        raise ValueError(
            "unsupported_change requires a PRESERVE expectation"
        )

    return (
        observation.interpretation_changed
        or observation.strength_changed
    )


def unsupported_change_rate(
    observations: Iterable[
        tuple[TransitionObservation, TransitionExpectation]
    ],
) -> float:
    """
    Calculate unsupported-change rate over preservation trials.

    Non-preservation trials are excluded from the denominator.
    """

    preservation_observations = tuple(
        (
            observation,
            expectation,
        )
        for observation, expectation in observations
        if expectation.direction == TransitionDirection.PRESERVE
    )

    if not preservation_observations:
        return 0.0

    return sum(
        unsupported_change(observation, expectation)
        for observation, expectation in preservation_observations
    ) / len(preservation_observations)
    """
    Calculate unsupported-change rate only over preservation trials.

    A preservation trial is one whose expected relation is PRESERVE.

    The expectation is evaluator-side metadata and does not enter the
    system-under-test reasoning path.
    """

    preservation_observations = tuple(
        observation
        for observation, expectation in observations
        if expectation.direction == TransitionDirection.PRESERVE
    )

    if not preservation_observations:
        return 0.0

    return sum(
        unsupported_change(observation)
        for observation in preservation_observations
    ) / len(preservation_observations)