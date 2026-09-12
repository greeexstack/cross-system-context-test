from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceItem:
    source: str
    event: str
    entity_type: str
    entity_id: str
    timestamp: str | None
    detail: str


@dataclass(frozen=True)
class PrimaryOnlyEvidence:
    opportunity_id: str
    items: tuple[EvidenceItem, ...]