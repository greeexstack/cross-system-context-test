from datetime import datetime, timedelta, timezone

from experiment.diagnosis.cross_system import CrossSystemDiagnoser
from experiment.domain.models import Communication, Opportunity
from experiment.evidence.primary_only import EvidenceItem


def make_opportunity():
    evaluation_at = datetime(
        2026,
        1,
        9,
        tzinfo=timezone.utc,
    )

    return Opportunity(
        id="opp_001",
        business_id="biz_001",
        customer_id="cust_001",
        owner_id="emp_001",
        stage="quote_sent",
        value=50000,
        quote_sent_at=evaluation_at - timedelta(days=8),
        last_crm_activity_at=evaluation_at - timedelta(days=6),
    )


def make_primary_evidence():
    return (
        EvidenceItem(
            source="CRM",
            event="quote_sent",
            entity_type="opportunity",
            entity_id="opp_001",
            timestamp="2026-01-01T00:00:00+00:00",
            detail="Quote was sent.",
        ),
    )


def test_customer_quote_communication_changes_diagnosis():
    opportunity = make_opportunity()

    communication = Communication(
        id="comm_001",
        business_id="biz_001",
        customer_id="cust_001",
        direction="inbound",
        timestamp=datetime(2026, 1, 8, tzinfo=timezone.utc),
        channel="whatsapp",
        topic="quote",
        content="Ready to discuss the next step.",
    )

    result = CrossSystemDiagnoser().diagnose(
        opportunity,
        communication,
        make_primary_evidence(),
    )

    assert (
        result.diagnosis
        == (
            "The customer recently engaged about the quote, "
            "while the CRM shows no corresponding recent "
            "internal activity. The primary-system follow-up "
            "gap therefore appears more consistent with an "
            "internal activity or follow-up gap than customer "
            "inactivity."
        )
    )

    assert result.confidence == "high"
    assert result.recommendation == (
        "Verify the communication and follow up with "
        "the opportunity owner."
    )

    assert any(
        item.source == "COMMUNICATION"
        for item in result.evidence
    )


def test_irrelevant_invoice_communication_does_not_change_diagnosis():
    opportunity = make_opportunity()

    communication = Communication(
        id="comm_002",
        business_id="biz_001",
        customer_id="cust_001",
        direction="inbound",
        timestamp=datetime(2026, 1, 8, tzinfo=timezone.utc),
        channel="whatsapp",
        topic="invoice",
        content="Question about an old invoice.",
    )

    result = CrossSystemDiagnoser().diagnose(
        opportunity,
        communication,
        make_primary_evidence(),
    )

    assert (
        "unrelated invoice"
        in result.diagnosis
    )

    assert result.confidence == "high"

    assert result.recommendation == (
        "Verify the opportunity status and follow up with "
        "the opportunity owner."
    )


def test_ambiguous_communication_does_not_create_confident_conclusion():
    opportunity = make_opportunity()

    communication = Communication(
        id="comm_003",
        business_id="biz_001",
        customer_id="cust_001",
        direction="inbound",
        timestamp=datetime(2026, 1, 8, tzinfo=timezone.utc),
        channel="whatsapp",
        topic="general",
        content="Can you send me an update?",
    )

    result = CrossSystemDiagnoser().diagnose(
        opportunity,
        communication,
        make_primary_evidence(),
    )

    assert result.confidence == "low"

    assert (
        result.recommendation
        == "Verify the communication context before taking "
        "follow-up action."
    )


def test_missing_external_communication_preserves_uncertainty():
    opportunity = make_opportunity()

    result = CrossSystemDiagnoser().diagnose(
        opportunity,
        None,
        make_primary_evidence(),
    )

    assert (
        "external communication data is unavailable"
        in result.diagnosis
    )

    assert result.confidence == "medium"

    assert (
        "external communication data was unavailable"
        in result.recommendation
    )