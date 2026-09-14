from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TransitionDirection(str, Enum):
    PRESERVE = "preserve"
    STRENGTHEN = "strengthen"
    WEAKEN = "weaken"
    CHANGE = "change"


@dataclass(frozen=True)
class ObservableState:
    interpretation_class: str
    support_level: str
    decision_strength: str
    recommended_focus: str | None = None


@dataclass(frozen=True)
class TransitionObservation:
    base: ObservableState
    variant: ObservableState

    @property
    def interpretation_changed(self) -> bool:
        return (
            self.base.interpretation_class
            != self.variant.interpretation_class
        )

    @property
    def support_changed(self) -> bool:
        return self.base.support_level != self.variant.support_level

    @property
    def strength_changed(self) -> bool:
        return (
            self.base.decision_strength
            != self.variant.decision_strength
        )


@dataclass(frozen=True)
class TransitionExpectation:
    direction: TransitionDirection


def observe(
    base_result,
    variant_result,
) -> TransitionObservation:
    return TransitionObservation(
        base=ObservableState(
            interpretation_class=base_result.interpretation_class,
            support_level=base_result.support_level,
            decision_strength=base_result.decision_strength,
            recommended_focus=base_result.recommended_focus,
        ),
        variant=ObservableState(
            interpretation_class=variant_result.interpretation_class,
            support_level=variant_result.support_level,
            decision_strength=variant_result.decision_strength,
            recommended_focus=variant_result.recommended_focus,
        ),
    )


def directional_correctness(
    observation: TransitionObservation,
    expectation: TransitionExpectation,
) -> bool:
    """
    Evaluate whether an observed paired-state transition moves in the
    expected direction.

    Direction is evaluated from observable state changes rather than from
    benchmark-specific semantic labels.
    """

    direction = expectation.direction

    if direction == TransitionDirection.PRESERVE:
        return (
            not observation.interpretation_changed
            and not observation.strength_changed
        )

    if direction == TransitionDirection.STRENGTHEN:
        return (
            observation.variant.decision_strength == "stronger"
            or (
                observation.base.support_level
                not in {
                    "secondary_supported",
                    "supported_by_secondary_context",
                }
                and observation.variant.support_level
                in {
                    "secondary_supported",
                    "supported_by_secondary_context",
                }
            )
        )

    if direction == TransitionDirection.WEAKEN:
        return (
            observation.variant.decision_strength == "weaker"
            or (
                observation.base.support_level
                != "weakened_by_secondary_context"
                and observation.variant.support_level
                == "weakened_by_secondary_context"
            )
        )

    if direction == TransitionDirection.CHANGE:
        return observation.interpretation_changed

    raise ValueError(f"Unsupported transition direction: {direction}")

    """
    Minimal v0.3 directional evaluator.

    This intentionally does not attempt numerical magnitude scoring.
    """

    direction = expectation.direction

    if direction == TransitionDirection.PRESERVE:
        return (
            observation.base.interpretation_class
            == observation.variant.interpretation_class
            and observation.base.decision_strength
            == observation.variant.decision_strength
        )

    if direction == TransitionDirection.STRENGTHEN:
        return (
            (
                observation.base.interpretation_class
                == observation.variant.interpretation_class
                and observation.variant.decision_strength == "stronger"
            )
            or observation.variant.support_level
            in {
                "secondary_supported",
                "supported_by_secondary_context",
            }
        )

    if direction == TransitionDirection.WEAKEN:
        return (
            (
                observation.base.interpretation_class
                == observation.variant.interpretation_class
                and observation.variant.decision_strength == "weaker"
            )
            or observation.variant.support_level
            == "weakened_by_secondary_context"
        )

    if direction == TransitionDirection.CHANGE:
        return observation.interpretation_changed

    raise ValueError(f"Unsupported transition direction: {direction}")