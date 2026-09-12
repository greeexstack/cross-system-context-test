from datetime import datetime, timezone

from experiment.analysis.cross_system_runner import (
    CrossSystemAnalysisRunner,
)
from experiment.domain.models import (
    Communication,
    Customer,
    Opportunity,
)


def make_customer():
    return Customer(
        id="cust_001",
        business_id="biz_001",
        name="Test Customer",
        email="test@example.com",
        phone="+14155550101",
    )


def make_opportunity():
    return Opportunity(
        id="opp_001",
        business_id="biz_001",
        customer_id="cust_001",
        owner_id="emp_001",
        stage="quote_sent",
        value=50000.0,
        quote_sent_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        last_crm_activity_at=datetime(
            2026,
            1,
            2,
            tzinfo=timezone.utc,
        ),
    )


def test_confidently_matched_communication_reaches_diagnosis():
    evaluation_at = datetime(
        2026,
        1,
        9,
        tzinfo=timezone.utc,
    )

    communication = Communication(
        id="comm_001",
        business_id="biz_001",
        customer_id="comm_cust_001",
        direction="inbound",
        timestamp=datetime(
            2026,
            1,
            8,
            tzinfo=timezone.utc,
        ),
        channel="whatsapp",
        topic="quote",
        content="Ready to discuss the next step.",
        customer_name="Test Customer",
        customer_email="test@example.com",
        customer_phone="+14155550101",
    )

    result = CrossSystemAnalysisRunner().run(
        make_opportunity(),
        make_customer(),
        evaluation_at,
        communication,
    )

    assert result.customer_match is not None
    assert result.customer_match.status == "confident_match"
    assert result.customer_match.confidence == 1.0

    assert result.diagnosis.confidence == "high"
    assert "customer recently engaged" in result.diagnosis.diagnosis.lower()


def test_unmatched_communication_cannot_change_opportunity_diagnosis():
    evaluation_at = datetime(
        2026,
        1,
        9,
        tzinfo=timezone.utc,
    )

    communication = Communication(
        id="comm_002",
        business_id="biz_001",
        customer_id="comm_cust_002",
        direction="inbound",
        timestamp=datetime(
            2026,
            1,
            8,
            tzinfo=timezone.utc,
        ),
        channel="whatsapp",
        topic="quote",
        content="Ready to discuss the next step.",
        customer_name="Different Customer",
        customer_email="different@example.com",
        customer_phone="+442079460123",
    )

    result = CrossSystemAnalysisRunner().run(
        make_opportunity(),
        make_customer(),
        evaluation_at,
        communication,
    )

    assert result.customer_match is not None
    assert result.customer_match.status == "no_match"

    assert "customer recently engaged" not in (
        result.diagnosis.diagnosis.lower()
    )

    assert result.diagnosis.confidence == "medium"


def test_missing_communication_preserves_unavailable_context():
    evaluation_at = datetime(
        2026,
        1,
        9,
        tzinfo=timezone.utc,
    )

    result = CrossSystemAnalysisRunner().run(
        make_opportunity(),
        make_customer(),
        evaluation_at,
        None,
    )

    assert result.customer_match is None

    assert (
        "external communication data is unavailable"
        in result.diagnosis.diagnosis.lower()
    )

    assert result.diagnosis.confidence == "medium"