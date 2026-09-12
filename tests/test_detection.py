from datetime import datetime

from experiment.baseline.quote_followup import (
    BaselineResult,
)
from experiment.detection.followup_gap import (
    FollowupGapDetector,
)


def test_crossed_baseline_produces_followup_gap_detection():
    baseline_result = BaselineResult(
        opportunity_id="opp_001",
        elapsed=datetime(2026, 9, 8) - datetime(2026, 9, 1),
        attention_threshold=datetime(2026, 9, 8) - datetime(2026, 9, 1),
        crossed=True,
        applicable=True,
        reason="Threshold crossed.",
    )

    result = FollowupGapDetector().detect(baseline_result)

    assert result.opportunity_id == "opp_001"
    assert result.detected is True
    assert "warrants investigation" in result.reason


def test_below_baseline_does_not_produce_detection():
    baseline_result = BaselineResult(
        opportunity_id="opp_002",
        elapsed=datetime(2026, 9, 8) - datetime(2026, 9, 5),
        attention_threshold=datetime(2026, 9, 8) - datetime(2026, 9, 1),
        crossed=False,
        applicable=True,
        reason="Threshold not crossed.",
    )

    result = FollowupGapDetector().detect(baseline_result)

    assert result.opportunity_id == "opp_002"
    assert result.detected is False
    assert "not crossed" in result.reason


def test_inapplicable_baseline_does_not_produce_detection():
    baseline_result = BaselineResult(
        opportunity_id="opp_003",
        elapsed=None,
        attention_threshold=datetime(2026, 9, 8) - datetime(2026, 9, 1),
        crossed=False,
        applicable=False,
        reason="Baseline unavailable.",
    )

    result = FollowupGapDetector().detect(baseline_result)

    assert result.opportunity_id == "opp_003"
    assert result.detected is False
    assert "not applicable" in result.reason