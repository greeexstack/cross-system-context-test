from dataclasses import dataclass
from enum import Enum


class CommunicationSourceStatus(str, Enum):
    UNAVAILABLE = "unavailable"
    AVAILABLE_NO_COMMUNICATION = "available_no_communication"
    COMMUNICATION_OBSERVED = "communication_observed"


class CustomerIdentityStatus(str, Enum):
    UNAVAILABLE = "unavailable"
    NOT_OBSERVED = "not_observed"
    CONFIDENT_MATCH = "confident_match"
    AMBIGUOUS_MATCH = "ambiguous_match"
    NO_MATCH = "no_match"


@dataclass(frozen=True)
class CrossSystemContext:
    communication_source_status: CommunicationSourceStatus
    customer_identity_status: CustomerIdentityStatus