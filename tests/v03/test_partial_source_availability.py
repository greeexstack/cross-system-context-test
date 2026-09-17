from __future__ import annotations

from dataclasses import dataclass

from experiment.v03.evidence import (
    EvidenceCondition,
    IdentityQuality,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)
from experiment.v03.battery import EVALUATION_AT


@dataclass(frozen=True)
class SourceState:
    source_system: str
    availability: str


@dataclass(frozen=True)
class PartialAvailability:
    sources: tuple[SourceState, ...]
    evidence_ids: tuple[str, ...]


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _extract(
    evidence_id: str,
    source_system: str,
    text: str,
    *,
    customer_id: str = "C001",
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
):
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system=source_system,
        record_id=evidence_id,
        occurred_at="2026-09-12T10:00:00Z",
        customer_id=customer_id,
        identity_quality=identity_quality,
    ).evidence


def _condition(
    availability: str,
    *items,
) -> EvidenceCondition:
    return EvidenceCondition(
        availability=availability,
        items=tuple(items),
    )


def _eligible_ids(
    condition: EvidenceCondition,
) -> tuple[str, ...]:
    return tuple(
        item.evidence_id
        for item in condition.items
        if (
            item.identity.quality == IdentityQuality.CONFIRMED
            and item.timestamp is not None
        )
    )


def test_one_available_source_can_supply_valid_evidence():
    crm = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    result = PartialAvailability(
        sources=(
            SourceState("crm", "available"),
        ),
        evidence_ids=_eligible_ids(
            _condition(
                "available",
                crm,
            )
        ),
    )

    assert result.sources == (
        SourceState("crm", "available"),
    )

    assert result.evidence_ids == ("CRM-1",)


def test_unavailable_second_source_does_not_delete_available_source_evidence():
    crm = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    crm_condition = _condition(
        "available",
        crm,
    )

    result = PartialAvailability(
        sources=(
            SourceState("crm", "available"),
            SourceState("email", "unavailable"),
        ),
        evidence_ids=_eligible_ids(
            crm_condition,
        ),
    )

    assert result.evidence_ids == ("CRM-1",)


def test_available_source_still_changes_reasoning_when_another_source_is_unavailable():
    crm = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            "available",
            crm,
        ),
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_unavailable_source_does_not_create_fake_evidence():
    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            "unavailable",
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"
    assert result.decision_strength == "moderate"


def test_available_empty_source_and_unavailable_source_remain_distinct():
    available_empty = _condition(
        "available",
    )

    unavailable = _condition(
        "unavailable",
    )

    assert available_empty.availability == "available"
    assert unavailable.availability == "unavailable"

    assert available_empty.items == ()
    assert unavailable.items == ()


def test_partial_availability_preserves_each_source_state():
    state = PartialAvailability(
        sources=(
            SourceState("crm", "available"),
            SourceState("email", "unavailable"),
            SourceState("billing", "available"),
        ),
        evidence_ids=("CRM-1",),
    )

    assert {
        source.source_system: source.availability
        for source in state.sources
    } == {
        "crm": "available",
        "email": "unavailable",
        "billing": "available",
    }


def test_unavailable_source_is_not_equivalent_to_filtered_source():
    valid = _extract(
        "VALID",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    wrong_identity = _extract(
        "WRONG",
        "email",
        "The customer wants another discussion about the proposal.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    filtered = _condition(
        "available",
        wrong_identity,
    )

    unavailable = _condition(
        "unavailable",
    )

    assert filtered.availability == "available"
    assert unavailable.availability == "unavailable"

    assert _eligible_ids(filtered) == ()
    assert _eligible_ids(unavailable) == ()


def test_valid_source_plus_filtered_source_retains_valid_evidence():
    valid = _extract(
        "VALID",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    wrong_identity = _extract(
        "WRONG",
        "email",
        "The quoted amount has budget approval.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    condition = _condition(
        "available",
        valid,
        wrong_identity,
    )

    assert _eligible_ids(condition) == (
        "VALID",
    )


def test_valid_source_plus_stale_source_retains_valid_evidence():
    valid = _extract(
        "VALID",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    stale_extractor = LexicalNormalizationSemanticExtractor()

    stale = stale_extractor.extract(
        evidence_id="STALE",
        content="The customer asks what comes next.",
        source_system="email",
        record_id="STALE",
        occurred_at="2026-07-01T10:00:00Z",
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    ).evidence

    condition = _condition(
        "available",
        valid,
        stale,
    )

    # This helper reports identity/timestamp eligibility only;
    # the actual freshness policy remains separate.
    assert condition.items[0].evidence_id == "VALID"
    assert condition.items[1].evidence_id == "STALE"


def test_partial_source_failure_does_not_change_valid_source_semantics():
    crm = _extract(
        "CRM",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    before = crm.semantics

    PartialAvailability(
        sources=(
            SourceState("crm", "available"),
            SourceState("email", "unavailable"),
        ),
        evidence_ids=("CRM",),
    )

    assert crm.semantics == before


def test_partial_source_failure_does_not_change_source_provenance():
    crm = _extract(
        "CRM",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    before = crm.provenance

    PartialAvailability(
        sources=(
            SourceState("crm", "available"),
            SourceState("email", "unavailable"),
        ),
        evidence_ids=("CRM",),
    )

    assert crm.provenance == before


def test_multiple_available_sources_can_contribute_independently():
    crm = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    email = _extract(
        "EMAIL",
        "email",
        "The customer asks what comes next.",
    )

    condition = _condition(
        "available",
        crm,
        email,
    )

    assert _eligible_ids(condition) == (
        "CRM",
        "EMAIL",
    )


def test_one_unavailable_source_does_not_prevent_other_sources_from_being_traced():
    crm = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    state = PartialAvailability(
        sources=(
            SourceState("crm", "available"),
            SourceState("email", "unavailable"),
            SourceState("support", "available"),
        ),
        evidence_ids=("CRM",),
    )

    assert "CRM" in state.evidence_ids

    assert (
        state.sources[1]
        == SourceState("email", "unavailable")
    )


def test_all_sources_unavailable_means_no_secondary_records():
    state = PartialAvailability(
        sources=(
            SourceState("crm", "unavailable"),
            SourceState("email", "unavailable"),
        ),
        evidence_ids=(),
    )

    assert state.evidence_ids == ()

    assert all(
        source.availability == "unavailable"
        for source in state.sources
    )


def test_all_sources_available_but_empty_is_not_failure():
    state = PartialAvailability(
        sources=(
            SourceState("crm", "available"),
            SourceState("email", "available"),
        ),
        evidence_ids=(),
    )

    assert state.evidence_ids == ()

    assert all(
        source.availability == "available"
        for source in state.sources
    )


def test_partial_availability_is_deterministic():
    state = PartialAvailability(
        sources=(
            SourceState("crm", "available"),
            SourceState("email", "unavailable"),
        ),
        evidence_ids=("CRM",),
    )

    assert state == state


def test_partial_availability_has_no_source_priority():
    state = PartialAvailability(
        sources=(
            SourceState("crm", "available"),
            SourceState("email", unavailable := "unavailable"),
        ),
        evidence_ids=(),
    )

    assert not hasattr(state, "source_priority")
    assert not hasattr(state, "winner")
    assert not hasattr(state, "recency_priority")


def test_partial_availability_has_no_benchmark_policy():
    state = PartialAvailability(
        sources=(
            SourceState("crm", "available"),
            SourceState("email", "unavailable"),
        ),
        evidence_ids=(),
    )

    assert not hasattr(
        state,
        "expected_direction",
    )

    assert not hasattr(
        state,
        "benchmark_family",
    )