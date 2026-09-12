from datetime import datetime

from experiment.context.business_context import BusinessContext
from experiment.domain.models import Opportunity, Quote
from experiment.resolution.customer import CustomerMatch
from experiment.timeline.customer import CustomerTimeline
from experiment.timeline.reconstruction import OpportunityTimeline


def test_business_context_combines_crm_and_communication_context():
    opportunity = Opportunity(
        id="opp_001",
        business_id="biz_001",
        customer_id="crm_cust_001",
        owner_id="emp_001",
        stage="quote_sent",
        value=50000.0,
        quote_sent_at=datetime.fromisoformat("2026-09-01T10:00:00"),
    )

    quote = Quote(
        id="quote_001",
        opportunity_id="opp_001",
        amount=50000.0,
        sent_at=datetime.fromisoformat("2026-09-01T10:00:00"),
    )

    customer_match = CustomerMatch(
        crm_customer_id="crm_cust_001",
        communication_customer_id="comm_cust_001",
        status="confident_match",
        confidence=1.0,
        reason="Exact email match.",
    )

    opportunity_timeline = OpportunityTimeline(
        opportunity_id="opp_001",
        events=[],
    )

    customer_timeline = CustomerTimeline(
        customer_id="comm_cust_001",
        events=[],
    )

    context = BusinessContext(
        opportunity=opportunity,
        quote=quote,
        customer_match=customer_match,
        opportunity_timeline=opportunity_timeline,
        customer_timeline=customer_timeline,
    )

    assert context.opportunity.id == "opp_001"
    assert context.quote.id == "quote_001"
    assert context.customer_match.status == "confident_match"
    assert context.opportunity_timeline.opportunity_id == "opp_001"
    assert context.customer_timeline.customer_id == "comm_cust_001"