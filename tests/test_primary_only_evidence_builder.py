from datetime import datetime

from experiment.baseline.quote_followup import QuoteFollowupBaselineEvaluator
from experiment.detection.followup_gap import FollowupGapDetector
from experiment.domain.models import Opportunity
from experiment.evidence.builder import PrimaryOnlyEvidenceBuilder


def test_builder_creates_evidence_for_detected_gap():
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

    evidence = PrimaryOnlyEvidenceBuilder().build(
        opportunity,
        baseline,
        detection,
    )

    assert evidence.opportunity_id == "opp_001"
    assert len(evidence.items) == 4

    events = {item.event for item in evidence.items}

    assert "quote_sent" in events
    assert "crm_activity" in events
    assert "followup_attention_threshold" in events
    assert "followup_gap_detection" in events


def test_builder_records_missing_crm_activity_without_inventing_timestamp():
    opportunity = Opportunity(
        id="opp_002",
        business_id="biz_001",
        customer_id="cust_001",
        owner_id="emp_001",
        stage="quote_sent",
        value=5000.0,
        quote_sent_at=datetime(2026, 1, 1, 10, 0),
        last_crm_activity_at=None,
    )

    evaluation_at = datetime(2026, 1, 9, 10, 0)

    baseline = QuoteFollowupBaselineEvaluator().evaluate(
        opportunity,
        evaluation_at,
    )
    detection = FollowupGapDetector().detect(baseline)

    evidence = PrimaryOnlyEvidenceBuilder().build(
        opportunity,
        baseline,
        detection,
    )

    activity_items = [
        item
        for item in evidence.items
        if item.event == "crm_activity_missing"
    ]

    assert len(activity_items) == 1
    assert activity_items[0].timestamp is None
    assert "no recorded activity" in activity_items[0].detail.lower()


def test_builder_evidence_is_crm_only_for_primary_system():
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

    evidence = PrimaryOnlyEvidenceBuilder().build(
        opportunity,
        baseline,
        detection,
    )

    sources = {item.source for item in evidence.items}

    assert "CRM" in sources
    assert "COMMUNICATION" not in sources