from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class IdentityQuality(str, Enum):
    CONFIRMED = "confirmed"
    AMBIGUOUS = "ambiguous"
    NO_MATCH = "no_match"


class TemporalQuality(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EvidenceProvenance:
    source_system: str
    record_id: str
    occurred_at: datetime | None


@dataclass(frozen=True)
class EvidenceIdentity:
    customer_id: str | None
    quality: IdentityQuality


@dataclass(frozen=True)
class EvidenceSemantics:
    """
    Factual semantic attributes extracted from the observation.

    These describe what the evidence says. They do not encode the
    benchmark's expected behavioral transition.

    Example:
        requests_followup=True

    is an observation about the communication.

    It must not become:

        expected_transition="strengthen"
    """

    topic: str | None = None

    requests_followup: bool | None = None
    expresses_acceptance: bool | None = None
    expresses_rejection: bool | None = None
    confirms_approval: bool | None = None
    confirms_completion: bool | None = None
    requests_next_step: bool | None = None

    concerns_same_work_item: bool | None = None


@dataclass(frozen=True)
class SemanticEvidence:
    """
    Normalized secondary evidence.

    Raw content and provenance are preserved alongside factual semantics.
    """

    evidence_id: str
    content: str
    provenance: EvidenceProvenance
    identity: EvidenceIdentity
    semantics: EvidenceSemantics

    @property
    def timestamp(self) -> datetime | None:
        return self.provenance.occurred_at


@dataclass(frozen=True)
class EvidenceCondition:
    """
    Secondary evidence available to the reasoning layer for one state.
    """

    availability: str
    items: tuple[SemanticEvidence, ...] = ()

    def is_available(self) -> bool:
        return self.availability == "available"

    def is_unavailable(self) -> bool:
        return self.availability == "unavailable"

    def has_evidence(self) -> bool:
        return bool(self.items)