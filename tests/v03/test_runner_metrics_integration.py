from __future__ import annotations

from datetime import datetime, timezone

from experiment.v03.evidence import (
    EvidenceCondition,
    EvidenceIdentity,
    EvidenceProvenance,
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.reasoner import PrimaryState, ReasonerConfig, V03Reasoner
from experiment.v03.runner import TransitionCase, V03TransitionRunner
from experiment.v03.transition_metrics import TransitionDirection
from experiment.v03.transition_metrics import observe
from experiment.v03.metrics import (
    directional_correctness_summary,
    unsupported_change_rate,
)
from experiment.v03.transition_metrics import TransitionExpectation

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


def _evidence(
    semantics: EvidenceSemantics,
) -> SemanticEvidence:
    return SemanticEvidence(
        evidence_id="INTEGRATION",
        content="synthetic evidence",
        provenance=EvidenceProvenance(
            source_system="test",
            record_id="INTEGRATION",
            occurred_at=datetime(
                2026,
                9,
                12,
                10,
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


def test_runner_measurements_feed_both_v03_metrics():
    cases = (
        TransitionCase(
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
        ),
        TransitionCase(
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
        ),
        TransitionCase(
            case_id="MR3",
            primary=PrimaryState("negotiation_open"),
            secondary=EvidenceCondition(
                availability="available",
                items=(
                    _evidence(
                        EvidenceSemantics(
                            topic="commercial_terms",
                            expresses_rejection=True,
                            concerns_same_work_item=True,
                        )
                    ),
                ),
            ),
            expected_direction=TransitionDirection.WEAKEN,
        ),
    )

    runner = V03TransitionRunner(_reasoner())
    summary = runner.run(cases)

    assert len(summary.measurements) == 3
    assert summary.directional_correctness.rate == 1.0

    directional_summary = directional_correctness_summary(
        measurement.directional_correct
        for measurement in summary.measurements
    )

    assert directional_summary.total == 3
    assert directional_summary.correct == 3
    assert directional_summary.rate == 1.0

    preservation_inputs = tuple(
        (
            measurement.observation,
            TransitionExpectation(measurement.expected_direction),
        )
        for measurement in summary.measurements
        if measurement.expected_direction
        == TransitionDirection.PRESERVE
    )

    assert unsupported_change_rate(preservation_inputs) == 0.0


def test_runner_can_expose_an_unsupported_preservation_change():
    class BadReasoner:
        def evaluate(self, primary, secondary):
            from types import SimpleNamespace

            if secondary.items:
                return SimpleNamespace(
                    interpretation_class="quote_followup_pending",
                    support_level="primary_only",
                    decision_strength="moderate",
                    recommended_focus=None,
                )

            return SimpleNamespace(
                interpretation_class=primary.interpretation_class,
                support_level="no_secondary_evidence",
                decision_strength=primary.decision_strength,
                recommended_focus=None,
            )

    case = TransitionCase(
        case_id="BAD-MR4",
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

    summary = V03TransitionRunner(BadReasoner()).run((case,))

    assert not summary.measurements[0].directional_correct

    preservation_inputs = tuple(
        (
            measurement.observation,
            TransitionExpectation(measurement.expected_direction),
        )
        for measurement in summary.measurements
        if measurement.expected_direction
        == TransitionDirection.PRESERVE
    )

    assert unsupported_change_rate(preservation_inputs) == 1.0
def test_metrics_detect_an_unsupported_change_in_a_preserve_case():
    class BadReasoner:
        def evaluate(self, primary, secondary):
            from types import SimpleNamespace

            if secondary.items:
                return SimpleNamespace(
                    interpretation_class="quote_followup_pending",
                    support_level="supported_by_secondary_context",
                    decision_strength="stronger",
                    recommended_focus=None,
                )

            return SimpleNamespace(
                interpretation_class=primary.interpretation_class,
                support_level="no_secondary_evidence",
                decision_strength=primary.decision_strength,
                recommended_focus=None,
            )

    case = TransitionCase(
        case_id="BAD-PRESERVE",
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

    summary = V03TransitionRunner(BadReasoner()).run((case,))

    assert summary.directional_correctness.total == 1
    assert summary.directional_correctness.correct == 0
    assert summary.directional_correctness.rate == 0.0

    assert summary.unsupported_change_rate == 1.0