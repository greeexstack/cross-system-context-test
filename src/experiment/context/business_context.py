from dataclasses import dataclass

from experiment.domain.models import Opportunity, Quote
from experiment.resolution.customer import CustomerMatch
from experiment.timeline.customer import CustomerTimeline
from experiment.timeline.reconstruction import OpportunityTimeline


@dataclass(frozen=True)
class BusinessContext:
    opportunity: Opportunity
    quote: Quote
    customer_match: CustomerMatch
    opportunity_timeline: OpportunityTimeline
    customer_timeline: CustomerTimeline