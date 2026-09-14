from __future__ import annotations

from datetime import datetime, timezone

from experiment.v03.evidence import EvidenceCondition, EvidenceSemantics
from experiment.v03.reasoner import PrimaryState, ReasonerConfig, V03Reasoner
from experiment.v03.runner import (
    TransitionCase,
    V03TransitionRunner,
)
from experiment.v03.transition_metrics import TransitionDirection


EVALUATION_AT = datetime(
    2026,
    9,
    13,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _evidence(semantics: EvidenceSemantics):
    from datetime import datetime

    from experiment.v03.evidence import (
        EvidenceIdentity,
        EvidenceProvenance,
        IdentityQuality,
        SemanticEvidence,
    )

    return SemanticEvidence(
        evidence_id="RUNNER",
        content="synthetic evidence",
        provenance=EvidenceProvenance(
            source_system="test",
            record_id="RUNNER",
            occurred_at=datetime.fromisoformat(
                "2026-09-12T10:00:00+00:00"
            ),
        ),
        identity=EvidenceIdentity(
            customer_id="C001",
            quality=IdentityQuality.CONFIRMED,
        ),
        semantics=semantics,
    )


def test_runner_measures_strengthening_transition():
    case = TransitionCase(
        case_id="MR2",
        primary=PrimaryState("quote_pending_decision"),
        secondary=EvidenceCondition(
            availability="available",
            items=(
                _evidence(
                    EvidenceSemantics(
                        topic="proposal",
                        confirms_approval=True,
                        expresses_acceptance=True,
                        concerns_same_work_item=True,
                    )
                ),
            ),
        ),
        expected_direction=TransitionDirection.STRENGTHEN,
    )

    summary = V03TransitionRunner(_reasoner()).run((case,))

    assert len(summary.measurements) == 1
    assert summary.measurements[0].directional_correct
    assert summary.directional_correctness.rate == 1.0


def test_runner_measures_preservation_transition():
    case = TransitionCase(
        case_id="MR4",
        primary=PrimaryState("quote_pending_decision"),
        secondary=EvidenceCondition(
            availability="available",
            items=(
                _evidence(
                    EvidenceSemantics(
                        topic="store_rollout",
                        concerns_same_work_item=False,
                    )
                ),
            ),
        ),
        expected_direction=TransitionDirection.PRESERVE,
    )

    summary = V03TransitionRunner(_reasoner()).run((case,))

    assert summary.measurements[0].directional_correct
    assert summary.directional_correctness.rate == 1.0


def test_runner_keeps_expected_direction_outside_reasoner():
    class RecordingReasoner:
        def __init__(self):
            self.calls = []

        def evaluate(self, primary, secondary):
            self.calls.append((primary, secondary))
            from types import SimpleNamespace

            return SimpleNamespace(
                interpretation_class=primary.interpretation_class,
                support_level="primary_only",
                decision_strength=primary.decision_strength,
                recommended_focus=None,
            )

    recording = RecordingReasoner()

    case = TransitionCase(
        case_id="PRESERVE",
        primary=PrimaryState("quote_pending_decision"),
        secondary=EvidenceCondition(
            availability="available",
            items=(),
        ),
        expected_direction=TransitionDirection.PRESERVE,
    )

    V03TransitionRunner(recording).run((case,))

    assert len(recording.calls) == 2

    for primary, secondary in recording.calls:
        assert not hasattr(primary, "expected_direction")
        assert not hasattr(secondary, "expected_direction")
def test_runner_reports_unsupported_change_rate_for_preservation_cases():
    case = TransitionCase(
        case_id="MR4",
        primary=PrimaryState("quote_pending_decision"),
        secondary=EvidenceCondition(
            availability="available",
            items=(
                _evidence(
                    EvidenceSemantics(
                        topic="store_rollout",
                        concerns_same_work_item=False,
                    )
                ),
            ),
        ),
        expected_direction=TransitionDirection.PRESERVE,
    )

    summary = V03TransitionRunner(_reasoner()).run((case,))

    assert summary.unsupported_change_rate == 0.0