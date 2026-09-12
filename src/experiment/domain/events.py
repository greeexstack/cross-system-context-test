from enum import Enum


class EventType(str, Enum):
    LEAD_CREATED = "lead_created"
    OPPORTUNITY_CREATED = "opportunity_created"
    QUOTE_SENT = "quote_sent"
    CONTACT_ATTEMPTED = "contact_attempted"
    CONTACT_MADE = "contact_made"
    CUSTOMER_ENGAGED = "customer_engaged"
    FOLLOWUP_SENT = "followup_sent"