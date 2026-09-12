from datetime import datetime

from experiment.baseline.quote_followup import QuoteFollowupBaselineEvaluator
from experiment.detection.followup_gap import FollowupGapDetector
from experiment.domain.models import Opportunity
from experiment.diagnosis.primary_only import PrimaryOnlyDiagnoser


def test_primary_only_diagnoses_followup_gap():
    opportunity = Opportunity(
        id="opp_001",
        business_id="biz_001",
        customer_id="cust_001",
        owner_id="emp_001",
        stage="quote_sent",
        value=5000.0,
        quote_sent_at=datetime(2026, 1, 1, 10, 0),
        last_crm_activity_at=datetime(2026, 1, 2, 10, 0),
    )

    evaluation_at = datetime(2026, 1, 9, 10, 0)

    baseline = QuoteFollowupBaselineEvaluator().evaluate(
        opportunity,
        evaluation_at,
    )
    detection = FollowupGapDetector().detect(baseline)
    diagnosis = PrimaryOnlyDiagnoser().diagnose(
        opportunity,
        baseline,
        detection,
    )

    assert detection.detected is True
    assert diagnosis.opportunity_id == "opp_001"
    assert "exceeded" in diagnosis.diagnosis
    assert "CRM" in diagnosis.diagnosis
    assert diagnosis.confidence == "medium"
    assert len(diagnosis.evidence) >= 2
    assert "follow up" in diagnosis.recommendation.lower()


def test_primary_only_does_not_claim_customer_inactivity():
    opportunity = Opportunity(
        id="opp_002",
        business_id="biz_001",
        customer_id="cust_001",
        owner_id="emp_001",
        stage="quote_sent",
        value=5000.0,
        quote_sent_at=datetime(2026, 1, 1, 10, 0),
        last_crm_activity_at=datetime(2026, 1, 2, 10, 0),
    )

    evaluation_at = datetime(2026, 1, 9, 10, 0)

    baseline = QuoteFollowupBaselineEvaluator().evaluate(
        opportunity,
        evaluation_at,
    )
    detection = FollowupGapDetector().detect(baseline)
    diagnosis = PrimaryOnlyDiagnoser().diagnose(
        opportunity,
        baseline,
        detection,
    )

    assert "customer is inactive" not in diagnosis.diagnosis.lower()
    assert "customer has lost interest" not in diagnosis.diagnosis.lower()


def test_primary_only_does_not_recommend_followup_when_no_gap_detected():
    opportunity = Opportunity(
        id="opp_003",
        business_id="biz_001",
        customer_id="cust_001",
        owner_id="emp_001",
        stage="quote_sent",
        value=5000.0,
        quote_sent_at=datetime(2026, 1, 1, 10, 0),
        last_crm_activity_at=datetime(2026, 1, 2, 10, 0),
    )

    evaluation_at = datetime(2026, 1, 4, 10, 0)

    baseline = QuoteFollowupBaselineEvaluator().evaluate(
        opportunity,
        evaluation_at,
    )
    detection = FollowupGapDetector().detect(baseline)
    diagnosis = PrimaryOnlyDiagnoser().diagnose(
        opportunity,
        baseline,
        detection,
    )

    assert detection.detected is False
    assert "No primary-system follow-up gap" in diagnosis.diagnosis
    assert diagnosis.confidence == "high"