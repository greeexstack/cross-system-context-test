from __future__ import annotations

from datetime import datetime, timezone

from experiment.v03.battery import (
    EVALUATION_AT,
    build_f10_case,
    build_v03_battery,
)
from experiment.v03.reasoner import ReasonerConfig, V03Reasoner
from experiment.v03.runner import V03TransitionRunner


def test_v03_battery_contains_expected_cases():
    cases = build_v03_battery()

    assert len(cases) == 9

    assert {
        case.case_id
        for case in cases
    } == {
        "MR1-relevant-followup",
        "MR2-supporting-approval",
        "MR3-contradictory-rejection",
        "MR4-irrelevant-work",
        "MR5-wrong-identity",
        "MR6-ambiguous-identity",
        "MR7-stale",
        "MR8-unavailable-source",
        "MR9-no-secondary",
    }


def test_f10_case_is_separately_available():
    case = build_f10_case()

    assert case.case_id == "F10-service-next-step"
    assert case.primary.interpretation_class == (
        "service_completed_next_step_unrecorded"
    )
    assert case.secondary.is_available()
    assert len(case.secondary.items) == 1


def test_battery_produces_expected_metric_summary():
    reasoner = V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )

    runner = V03TransitionRunner(reasoner)

    cases = (
        *build_v03_battery(),
        build_f10_case(),
    )

    summary = runner.run(cases)

    assert summary.directional_correctness.total == 10
    assert summary.directional_correctness.correct == 10
    assert summary.directional_correctness.rate == 1.0

    assert summary.unsupported_change_rate == 0.0