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
from experiment.v03.metrics import (
    directional_correctness_summary,
    unsupported_change_rate,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)
from experiment.v03.runner import (
    TransitionCase,
    V03TransitionRunner,
)
from experiment.v03.transition_metrics import (
    TransitionDirection,
    TransitionExpectation,
)


EVALUATION_AT = datetime(
    2026,
    9,
    13,
    12,
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


def _extract(
    evidence_id: str,
    text: str,
    occurred_at: str,
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system="test",
        record_id=evidence_id,
        occurred_at=occurred_at,
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    ).evidence


def _condition(
    *items: SemanticEvidence,
) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=items,
    )


def test_directional_metric_remains_per_case():
    cases = (
        TransitionCase(
            case_id="CONFLICT-STRENGTHEN",
            primary=PrimaryState("quote_pending_decision"),
            secondary=_condition(
                _extract(
                    "POSITIVE",
                    "The customer wants another discussion about the proposal.",
                    "2026-09-12T10:00:00Z",
                ),
            ),
            expected_direction=TransitionDirection.STRENGTHEN,
        ),
        TransitionCase(
            case_id="CONFLICT-PRESERVE",
            primary=PrimaryState("quote_pending_decision"),
            secondary=_condition(
                _extract(
                    "NEGATIVE",
                    "The customer does not want another discussion about the proposal.",
                    "2026-09-12T10:00:00Z",
                ),
            ),
            expected_direction=TransitionDirection.PRESERVE,
        ),
    )

    summary = V03TransitionRunner(_reasoner()).run(cases)

    metric = directional_correctness_summary(
        measurement.directional_correct
        for measurement in summary.measurements
    )

    assert metric.total == 2
    assert metric.correct == 2
    assert metric.rate == 1.0


def test_conflicting_followup_preserve_population_has_zero_unsupported_change():
    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    case = TransitionCase(
        case_id="CONFLICT-PRESERVE",
        primary=PrimaryState("quote_pending_decision"),
        secondary=_condition(negative),
        expected_direction=TransitionDirection.PRESERVE,
    )

    summary = V03TransitionRunner(_reasoner()).run((case,))

    observations = (
        (
            measurement.observation,
            TransitionExpectation(measurement.expected_direction),
        )
        for measurement in summary.measurements
    )

    assert unsupported_change_rate(observations) == 0.0


def test_conflicting_fresh_evidence_can_score_directionally_correct():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    case = TransitionCase(
        case_id="CONFLICT-FRESH",
        primary=PrimaryState("quote_pending_decision"),
        secondary=_condition(
            positive,
            negative,
        ),
        expected_direction=TransitionDirection.STRENGTHEN,
    )

    summary = V03TransitionRunner(_reasoner()).run((case,))

    assert summary.directional_correctness.total == 1
    assert summary.directional_correctness.correct == 1
    assert summary.directional_correctness.rate == 1.0


def test_conflicting_evidence_does_not_enter_unsupported_change_population():
    positive = _extract(
        "POSITIVE",
        "The customer wants another discussion about the proposal.",
        "2026-09-10T10:00:00Z",
    )

    negative = _extract(
        "NEGATIVE",
        "The customer does not want another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    case = TransitionCase(
        case_id="CONFLICT-STRENGTHEN",
        primary=PrimaryState("quote_pending_decision"),
        secondary=_condition(
            positive,
            negative,
        ),
        expected_direction=TransitionDirection.STRENGTHEN,
    )

    summary = V03TransitionRunner(_reasoner()).run((case,))

    observations = (
        (
            measurement.observation,
            TransitionExpectation(measurement.expected_direction),
        )
        for measurement in summary.measurements
    )

    assert unsupported_change_rate(observations) == 0.0


def test_stale_conflicting_evidence_is_excluded_before_metrics():
    fresh_positive = _extract(
        "FRESH",
        "The customer wants another discussion about the proposal.",
        "2026-09-12T10:00:00Z",
    )

    stale_negative = _extract(
        "STALE",
        "The customer does not want another discussion about the proposal.",
        "2026-07-01T10:00:00Z",
    )

    case = TransitionCase(
        case_id="STALE-CONFLICT",
        primary=PrimaryState("quote_pending_decision"),
        secondary=_condition(
            fresh_positive,
            stale_negative,
        ),
        expected_direction=TransitionDirection.STRENGTHEN,
    )

    summary = V03TransitionRunner(_reasoner()).run((case,))

    measurement = summary.measurements[0]

    assert measurement.directional_correct is True
    assert summary.directional_correctness.rate == 1.0