from datetime import datetime

from experiment.domain.models import Communication
from experiment.timeline.customer import CustomerTimelineReconstructor


def test_customer_timeline_reconstructs_communication_events():
    communications = [
        Communication(
            id="comm_001",
            business_id="biz_001",
            customer_id="comm_cust_001",
            direction="outbound",
            timestamp=datetime.fromisoformat("2026-09-03T10:00:00"),
            channel="email",
            topic="quote",
            content="Quote sent.",
        ),
        Communication(
            id="comm_002",
            business_id="biz_001",
            customer_id="comm_cust_001",
            direction="inbound",
            timestamp=datetime.fromisoformat("2026-09-05T11:00:00"),
            channel="whatsapp",
            topic="quote",
            content="Customer asks for an update.",
        ),
        Communication(
            id="comm_003",
            business_id="biz_001",
            customer_id="comm_cust_002",
            direction="inbound",
            timestamp=datetime.fromisoformat("2026-09-06T12:00:00"),
            channel="phone",
            topic="quote",
            content="Different customer.",
        ),
    ]

    reconstructor = CustomerTimelineReconstructor()

    timeline = reconstructor.reconstruct(
        customer_id="comm_cust_001",
        communications=communications,
    )

    assert timeline.customer_id == "comm_cust_001"
    assert len(timeline.events) == 2

    assert timeline.events[0].event_type == "contact_made"
    assert timeline.events[1].event_type == "customer_engaged"

    assert timeline.events[0].timestamp < timeline.events[1].timestamp