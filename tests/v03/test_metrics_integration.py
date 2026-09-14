from __future__ import annotations

from experiment.v03.metrics import unsupported_change_rate
from experiment.v03.transition_metrics import ObservableState, TransitionObservation
from experiment.v03.transition_metrics import (
    TransitionDirection,
    TransitionExpectation,
)
def test_unsupported_change_rate_uses_preservation_population():
    observations = (
        (
            TransitionObservation(
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
            TransitionExpectation(TransitionDirection.PRESERVE),
        ),
        (
            TransitionObservation(
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
            ),
            TransitionExpectation(TransitionDirection.PRESERVE),
        ),
    )

    assert unsupported_change_rate(observations) == 0.5