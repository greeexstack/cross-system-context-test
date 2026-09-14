from __future__ import annotations

from experiment.v03.metrics import (
    directional_correctness_summary,
    unsupported_change,
    unsupported_change_rate,
)
from experiment.v03.transition_metrics import (
    ObservableState,
    TransitionDirection,
    TransitionExpectation,
    TransitionObservation,
)


def _observation(
    base_interpretation: str,
    base_support: str,
    base_strength: str,
    variant_interpretation: str,
    variant_support: str,
    variant_strength: str,
) -> TransitionObservation:
    return TransitionObservation(
        base=ObservableState(
            base_interpretation,
            base_support,
            base_strength,
        ),
        variant=ObservableState(
            variant_interpretation,
            variant_support,
            variant_strength,
        ),
    )


def test_directional_correctness_summary():
    summary = directional_correctness_summary(
        (True, True, False, True)
    )

    assert summary.total == 4
    assert summary.correct == 3
    assert summary.rate == 0.75


def test_empty_directional_correctness_summary():
    summary = directional_correctness_summary(())

    assert summary.total == 0
    assert summary.correct == 0
    assert summary.rate == 0.0


def test_unsupported_change_detects_interpretation_change():
    observation = _observation(
        "quote_pending_decision",
        "no_secondary_evidence",
        "moderate",
        "quote_followup_pending",
        "primary_only",
        "moderate",
    )

    assert unsupported_change(
        observation,
        TransitionExpectation(TransitionDirection.PRESERVE),
    )


def test_unsupported_change_detects_strength_change():
    observation = _observation(
        "quote_pending_decision",
        "no_secondary_evidence",
        "moderate",
        "quote_pending_decision",
        "primary_only",
        "stronger",
    )

    assert unsupported_change(
        observation,
        TransitionExpectation(TransitionDirection.PRESERVE),
    )


def test_unsupported_change_allows_preservation():
    observation = _observation(
        "quote_pending_decision",
        "no_secondary_evidence",
        "moderate",
        "quote_pending_decision",
        "primary_only",
        "moderate",
    )

    assert not unsupported_change(
        observation,
        TransitionExpectation(TransitionDirection.PRESERVE),
    )


def test_unsupported_change_rate_uses_only_preservation_trials():
    preserved = _observation(
        "quote_pending_decision",
        "no_secondary_evidence",
        "moderate",
        "quote_pending_decision",
        "primary_only",
        "moderate",
    )

    unsupported = _observation(
        "quote_pending_decision",
        "no_secondary_evidence",
        "moderate",
        "quote_followup_pending",
        "supported_by_secondary_context",
        "moderate",
    )

    strengthened = _observation(
        "quote_pending_decision",
        "no_secondary_evidence",
        "moderate",
        "quote_pending_decision",
        "secondary_supported",
        "stronger",
    )

    observations = (
        (
            preserved,
            TransitionExpectation(TransitionDirection.PRESERVE),
        ),
        (
            unsupported,
            TransitionExpectation(TransitionDirection.PRESERVE),
        ),
        (
            strengthened,
            TransitionExpectation(TransitionDirection.STRENGTHEN),
        ),
    )

    assert unsupported_change_rate(observations) == 0.5


def test_unsupported_change_rate_ignores_strengthening_trials():
    strengthened = _observation(
        "quote_pending_decision",
        "no_secondary_evidence",
        "moderate",
        "quote_pending_decision",
        "secondary_supported",
        "stronger",
    )

    observations = (
        (
            strengthened,
            TransitionExpectation(TransitionDirection.STRENGTHEN),
        ),
    )

    assert unsupported_change_rate(observations) == 0.0


def test_empty_unsupported_change_rate():
    assert unsupported_change_rate(()) == 0.0