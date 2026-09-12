from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Business:
    id: str
    name: str


@dataclass(frozen=True)
class Customer:
    id: str
    business_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass(frozen=True)
class Employee:
    id: str
    business_id: str
    name: str


@dataclass(frozen=True)
class Opportunity:
    id: str
    business_id: str
    customer_id: str
    owner_id: str
    stage: str
    value: float
    quote_sent_at: Optional[datetime] = None
    last_crm_activity_at: Optional[datetime] = None


@dataclass(frozen=True)
class Quote:
    id: str
    opportunity_id: str
    amount: float
    sent_at: datetime


@dataclass(frozen=True)
class Communication:
    id: str
    business_id: str
    customer_id: str
    direction: str
    timestamp: datetime
    channel: str
    topic: str
    content: str


@dataclass(frozen=True)
class Event:
    id: str
    business_id: str
    event_type: str
    entity_type: str
    entity_id: str
    timestamp: datetime