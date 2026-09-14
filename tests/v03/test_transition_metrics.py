from __future__ import annotations

from types import SimpleNamespace

import pytest

from experiment.v03.transition_metrics import (
    ObservableState,
    TransitionDirection,
    TransitionExpectation,
    TransitionObservation,
    directional_correctness,
)


def result(
    interpretation_class: str,
    support_level: str,
    decision_strength: str,
    recommended_focus: str | None = None,
):
    return SimpleNamespace(
        interpretation_class=interpretation_class,
        support_level=support_level,
        decision_strength=decision_strength,
        recommended_focus=recommended_focus,
    )


def test_preserve_requires_primary_interpretation_and_strength():
    observation = TransitionObservation(
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
    )

    assert directional_correctness(
        observation,
        TransitionExpectation(TransitionDirection.PRESERVE),
    )


def test_preserve_fails_when_interpretation_changes():
    observation = TransitionObservation(
        base=ObservableState(
            "quote_pending_decision",
            "no_secondary_evidence",
            "moderate",
        ),
        variant=ObservableState(
            "quote_followup_pending",
            "supported_by_secondary_context",
            "moderate",
        ),
    )

    assert not directional_correctness(
        observation,
        TransitionExpectation(TransitionDirection.PRESERVE),
    )


def test_strengthen_accepts_stronger_decision_strength():
    observation = TransitionObservation(
        base=ObservableState(
            "quote_pending_decision",
            "no_secondary_evidence",
            "moderate",
        ),
        variant=ObservableState(
            "quote_pending_decision",
            "secondary_supported",
            "stronger",
        ),
    )

    assert directional_correctness(
        observation,
        TransitionExpectation(TransitionDirection.STRENGTHEN),
    )


def test_strengthen_accepts_supported_by_secondary_context():
    observation = TransitionObservation(
        base=ObservableState(
            "quote_pending_decision",
            "no_secondary_evidence",
            "moderate",
        ),
        variant=ObservableState(
            "quote_followup_pending",
            "supported_by_secondary_context",
            "moderate",
        ),
    )

    assert directional_correctness(
        observation,
        TransitionExpectation(TransitionDirection.STRENGTHEN),
    )


def test_weaken_accepts_weaker_strength():
    observation = TransitionObservation(
        base=ObservableState(
            "negotiation_open",
            "no_secondary_evidence",
            "moderate",
        ),
        variant=ObservableState(
            "negotiation_open",
            "weakened_by_secondary_context",
            "weaker",
        ),
    )

    assert directional_correctness(
        observation,
        TransitionExpectation(TransitionDirection.WEAKEN),
    )


def test_change_requires_interpretation_change():
    observation = TransitionObservation(
        base=ObservableState(
            "quote_pending_decision",
            "no_secondary_evidence",
            "moderate",
        ),
        variant=ObservableState(
            "quote_followup_pending",
            "supported_by_secondary_context",
            "moderate",
        ),
    )

    assert directional_correctness(
        observation,
        TransitionExpectation(TransitionDirection.CHANGE),
    )


def test_observable_state_tracks_material_dimensions():
    base = result(
        "quote_pending_decision",
        "no_secondary_evidence",
        "moderate",
    )

    variant = result(
        "quote_followup_pending",
        "supported_by_secondary_context",
        "moderate",
        "followup",
    )

    observation = TransitionObservation(
        base=ObservableState(
            base.interpretation_class,
            base.support_level,
            base.decision_strength,
            base.recommended_focus,
        ),
        variant=ObservableState(
            variant.interpretation_class,
            variant.support_level,
            variant.decision_strength,
            variant.recommended_focus,
        ),
    )

    assert observation.interpretation_changed
    assert observation.support_changed
    assert not observation.strength_changed