from dataclasses import dataclass
from datetime import datetime

from experiment.domain.events import EventType
from experiment.domain.models import Event, Opportunity, Quote


@dataclass(frozen=True)
class OpportunityTimeline:
    opportunity_id: str
    events: list[Event]


class TimelineReconstructor:
    def reconstruct_opportunity_timeline(
        self,
        opportunity: Opportunity,
        quote: Quote,
    ) -> OpportunityTimeline:
        events = []

        if opportunity.quote_sent_at is not None:
            events.append(
                Event(
                    id=f"{opportunity.id}:quote_sent",
                    business_id=opportunity.business_id,
                    event_type=EventType.QUOTE_SENT.value,
                    entity_type="opportunity",
                    entity_id=opportunity.id,
                    timestamp=opportunity.quote_sent_at,
                )
            )

        events.append(
            Event(
                id=f"{quote.id}:quote_sent",
                business_id=opportunity.business_id,
                event_type=EventType.QUOTE_SENT.value,
                entity_type="quote",
                entity_id=quote.id,
                timestamp=quote.sent_at,
            )
        )

        events.sort(key=lambda event: event.timestamp)

        return OpportunityTimeline(
            opportunity_id=opportunity.id,
            events=events,
        )