from datetime import datetime

from experiment.domain.models import Opportunity, Quote
from experiment.timeline.reconstruction import TimelineReconstructor


def test_opportunity_timeline_is_ordered():
    opportunity = Opportunity(
        id="opp_001",
        business_id="biz_001",
        customer_id="crm_cust_001",
        owner_id="emp_001",
        stage="quote_sent",
        value=50000.0,
        quote_sent_at=datetime.fromisoformat("2026-09-01T10:00:00"),
        last_crm_activity_at=datetime.fromisoformat("2026-09-01T10:00:00"),
    )

    quote = Quote(
        id="quote_001",
        opportunity_id="opp_001",
        amount=50000.0,
        sent_at=datetime.fromisoformat("2026-09-01T10:00:00"),
    )

    reconstructor = TimelineReconstructor()

    timeline = reconstructor.reconstruct_opportunity_timeline(
        opportunity,
        quote,
    )

    assert timeline.opportunity_id == "opp_001"
    assert len(timeline.events) == 2

    assert timeline.events[0].event_type == "quote_sent"
    assert timeline.events[1].event_type == "quote_sent"

    assert timeline.events[0].timestamp <= timeline.events[1].timestamp