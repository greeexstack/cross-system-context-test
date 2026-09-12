from datetime import datetime, timedelta, timezone

from experiment.analysis.runner import PrimaryOnlyAnalysisRunner
from experiment.domain.models import Opportunity


def test_primary_only_analysis_runner_produces_complete_result():
    evaluation_at = datetime(
        2026,
        1,
        9,
        tzinfo=timezone.utc,
    )

    opportunity = Opportunity(
        id="opp_001",
        business_id="biz_001",
        customer_id="cust_001",
        owner_id="emp_001",
        stage="quote_sent",
        value=50000,
        quote_sent_at=evaluation_at - timedelta(days=8),
        last_crm_activity_at=evaluation_at - timedelta(days=6),
    )

    result = PrimaryOnlyAnalysisRunner().run(
        opportunity,
        evaluation_at,
    )

    assert result.opportunity_id == "opp_001"

    assert result.baseline.crossed is True
    assert result.detection.detected is True

    assert (
        result.diagnosis.diagnosis
        == (
            "The opportunity has exceeded the experimental follow-up "
            "attention threshold, and the CRM shows no recent internal "
            "activity after the quote."
        )
    )

    assert result.diagnosis.confidence == "medium"
    assert result.diagnosis.evidence
    assert result.diagnosis.recommendation