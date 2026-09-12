from dataclasses import dataclass

from experiment.domain.events import EventType
from experiment.domain.models import Communication, Event


@dataclass(frozen=True)
class CustomerTimeline:
    customer_id: str
    events: list[Event]


class CustomerTimelineReconstructor:
    def reconstruct(
        self,
        customer_id: str,
        communications: list[Communication],
    ) -> CustomerTimeline:
        events = []

        for communication in communications:
            if communication.customer_id != customer_id:
                continue

            if communication.direction == "inbound":
                event_type = EventType.CUSTOMER_ENGAGED.value
            else:
                event_type = EventType.CONTACT_MADE.value

            events.append(
                Event(
                    id=f"{communication.id}:{event_type}",
                    business_id=communication.business_id,
                    event_type=event_type,
                    entity_type="customer",
                    entity_id=customer_id,
                    timestamp=communication.timestamp,
                )
            )

        events.sort(key=lambda event: event.timestamp)

        return CustomerTimeline(
            customer_id=customer_id,
            events=events,
        )