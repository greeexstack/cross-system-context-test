from datetime import datetime, timedelta

from experiment.baseline.quote_followup import (
    QuoteFollowupBaselineEvaluator,
)
from experiment.domain.models import Opportunity


def make_opportunity(
    *,
    opportunity_id: str = "opp_001",
    quote_sent_at: datetime | None = datetime(2026, 9, 1),
    cycle_type: str = "standard",
) -> Opportunity:
    return Opportunity(
        id=opportunity_id,
        business_id="biz_001",
        customer_id="cust_001",
        owner_id="emp_001",
        stage="quote_sent",
        value=100000.0,
        cycle_type=cycle_type,
        quote_sent_at=quote_sent_at,
        last_crm_activity_at=None,
    )


def test_standard_opportunity_crosses_seven_day_attention_threshold():
    opportunity = make_opportunity(
        quote_sent_at=datetime(2026, 9, 1)
    )

    evaluation_at = datetime(2026, 9, 8)

    result = QuoteFollowupBaselineEvaluator().evaluate(
        opportunity,
        evaluation_at,
    )

    assert result.applicable is True
    assert result.crossed is True
    assert result.elapsed == timedelta(days=7)
    assert result.attention_threshold == timedelta(days=7)


def test_standard_opportunity_below_threshold_does_not_cross():
    opportunity = make_opportunity(
        quote_sent_at=datetime(2026, 9, 5)
    )

    evaluation_at = datetime(2026, 9, 8)

    result = QuoteFollowupBaselineEvaluator().evaluate(
        opportunity,
        evaluation_at,
    )

    assert result.applicable is True
    assert result.crossed is False
    assert result.elapsed == timedelta(days=3)


def test_long_cycle_opportunity_is_outside_standard_baseline():
    opportunity = make_opportunity(
        quote_sent_at=datetime(2026, 8, 1),
        cycle_type="long",
    )

    evaluation_at = datetime(2026, 9, 8)

    result = QuoteFollowupBaselineEvaluator().evaluate(
        opportunity,
        evaluation_at,
    )

    assert result.applicable is False
    assert result.crossed is False
    assert "Long-cycle" in result.reason


def test_missing_quote_timestamp_is_explicitly_unavailable():
    opportunity = make_opportunity(
        quote_sent_at=None
    )

    evaluation_at = datetime(2026, 9, 8)

    result = QuoteFollowupBaselineEvaluator().evaluate(
        opportunity,
        evaluation_at,
    )

    assert result.applicable is False
    assert result.crossed is False
    assert result.elapsed is None
    assert "missing" in result.reason.lower()