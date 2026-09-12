from experiment.evidence.primary_only import (
    EvidenceItem,
    PrimaryOnlyEvidence,
)


def test_evidence_item_preserves_source_and_provenance():
    item = EvidenceItem(
        source="CRM",
        event="quote_sent",
        entity_type="opportunity",
        entity_id="opp_001",
        timestamp="2026-01-01T10:00:00",
        detail="Quote was sent.",
    )

    assert item.source == "CRM"
    assert item.event == "quote_sent"
    assert item.entity_type == "opportunity"
    assert item.entity_id == "opp_001"
    assert item.timestamp == "2026-01-01T10:00:00"
    assert item.detail == "Quote was sent."


def test_primary_only_evidence_belongs_to_one_opportunity():
    evidence = PrimaryOnlyEvidence(
        opportunity_id="opp_001",
        items=(
            EvidenceItem(
                source="CRM",
                event="quote_sent",
                entity_type="opportunity",
                entity_id="opp_001",
                timestamp="2026-01-01T10:00:00",
                detail="Quote was sent.",
            ),
        ),
    )

    assert evidence.opportunity_id == "opp_001"
    assert len(evidence.items) == 1
    assert evidence.items[0].entity_id == "opp_001"


def test_evidence_can_explicitly_have_no_timestamp():
    item = EvidenceItem(
        source="CRM",
        event="crm_activity",
        entity_type="opportunity",
        entity_id="opp_001",
        timestamp=None,
        detail="CRM contains no recorded activity timestamp.",
    )

    assert item.timestamp is None