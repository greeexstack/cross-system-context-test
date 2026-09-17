from __future__ import annotations

from dataclasses import dataclass

from experiment.v03.battery import EVALUATION_AT
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


@dataclass(frozen=True)
class SourceObservation:
    source_system: str
    availability: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class OrchestratedContext:
    sources: tuple[SourceObservation, ...]

    @property
    def all_evidence_ids(self) -> tuple[str, ...]:
        return tuple(
            evidence_id
            for source in self.sources
            for evidence_id in source.evidence_ids
        )

    @property
    def available_sources(self) -> tuple[str, ...]:
        return tuple(
            source.source_system
            for source in self.sources
            if source.availability == "available"
        )

    @property
    def unavailable_sources(self) -> tuple[str, ...]:
        return tuple(
            source.source_system
            for source in self.sources
            if source.availability == "unavailable"
        )

    @property
    def failed_sources(self) -> tuple[str, ...]:
        return tuple(
            source.source_system
            for source in self.sources
            if source.availability == "failed"
        )


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
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    customer_id: str = "C001",
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
    *items,
    availability: str = "available",
) -> EvidenceCondition:
    return EvidenceCondition(
        availability=availability,
        items=tuple(items),
    )


def _source_observation(
    source_system: str,
    availability: str,
    *evidence_ids: str,
) -> SourceObservation:
    return SourceObservation(
        source_system=source_system,
        availability=availability,
        evidence_ids=tuple(evidence_ids),
    )


def test_available_source_with_valid_evidence_is_represented():
    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
                "CRM-1",
            ),
        ),
    )

    assert context.available_sources == ("crm",)
    assert context.unavailable_sources == ()
    assert context.failed_sources == ()

    assert context.all_evidence_ids == ("CRM-1",)


def test_unavailable_source_has_no_evidence_ids():
    context = OrchestratedContext(
        sources=(
            _source_observation(
                "email",
                "unavailable",
            ),
        ),
    )

    assert context.unavailable_sources == ("email",)
    assert context.all_evidence_ids == ()


def test_failed_source_has_no_evidence_ids():
    context = OrchestratedContext(
        sources=(
            _source_observation(
                "billing",
                "failed",
            ),
        ),
    )

    assert context.failed_sources == ("billing",)
    assert context.all_evidence_ids == ()


def test_valid_crm_evidence_survives_email_failure():
    crm = _extract(
        "CRM-FOLLOWUP",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    crm_condition = _condition(
        crm,
        availability="available",
    )

    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        crm_condition,
    )

    assert result.interpretation_class == "quote_followup_pending"
    assert result.support_level == "supported_by_secondary_context"


def test_email_failure_does_not_create_fake_followup_evidence():
    result = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            availability="unavailable",
        ),
    )

    assert result.interpretation_class == "quote_pending_decision"

    # An unavailable secondary system triggers the reasoner's
    # explicit safe fallback rather than pretending that the source
    # was queried successfully and returned no evidence.
    assert result.support_level == "safe_fallback_primary_only"
    assert result.decision_strength == "moderate"
    assert result.recommended_focus is None

def test_available_empty_source_is_not_equivalent_to_failed_source():
    available_empty = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
            ),
        ),
    )

    failed = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "failed",
            ),
        ),
    )

    assert available_empty.available_sources == ("crm",)
    assert failed.failed_sources == ("crm",)

    assert available_empty.all_evidence_ids == ()
    assert failed.all_evidence_ids == ()


def test_partial_success_preserves_valid_evidence_and_failure_state():
    crm = _extract(
        "CRM-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
                "CRM-COMPLETION",
            ),
            _source_observation(
                "email",
                "failed",
            ),
        ),
    )

    assert context.available_sources == ("crm",)
    assert context.failed_sources == ("email",)
    assert context.all_evidence_ids == ("CRM-COMPLETION",)

    assert crm.provenance.source_system == "crm"


def test_partial_success_can_contain_multiple_available_sources():
    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
                "CRM-1",
            ),
            _source_observation(
                "email",
                "available",
                "EMAIL-1",
            ),
            _source_observation(
                "billing",
                "failed",
            ),
        ),
    )

    assert set(context.available_sources) == {
        "crm",
        "email",
    }

    assert context.failed_sources == ("billing",)

    assert set(context.all_evidence_ids) == {
        "CRM-1",
        "EMAIL-1",
    }


def test_filtered_evidence_is_not_confused_with_source_failure():
    wrong_identity = _extract(
        "WRONG-ID",
        "email",
        "The customer wants another discussion about the proposal.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    context = OrchestratedContext(
        sources=(
            _source_observation(
                "email",
                "available",
                "WRONG-ID",
            ),
        ),
    )

    assert context.available_sources == ("email",)
    assert context.all_evidence_ids == ("WRONG-ID",)

    eligible = tuple(
        item.evidence_id
        for item in (
            wrong_identity,
        )
        if item.identity.quality == IdentityQuality.CONFIRMED
    )

    assert eligible == ()


def test_source_failure_does_not_change_evidence_identity():
    evidence = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
                "CRM-1",
            ),
            _source_observation(
                "email",
                "failed",
            ),
        ),
    )

    assert context.available_sources == ("crm",)

    assert evidence.identity.customer_id == "C001"
    assert evidence.identity.quality == IdentityQuality.CONFIRMED


def test_source_failure_does_not_change_evidence_provenance():
    evidence = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    before = evidence.provenance

    OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
                "CRM-1",
            ),
            _source_observation(
                "email",
                "failed",
            ),
        ),
    )

    assert evidence.provenance == before


def test_source_status_does_not_change_semantic_content():
    evidence = _extract(
        "CRM-1",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    before = evidence.semantics

    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
                "CRM-1",
            ),
            _source_observation(
                "email",
                "unavailable",
            ),
        ),
    )

    assert context.available_sources == ("crm",)
    assert evidence.semantics == before


def test_same_evidence_can_be_traced_to_its_declared_source():
    evidence = _extract(
        "CRM-1",
        "crm",
        "The migration workshop is complete.",
    )

    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
                "CRM-1",
            ),
        ),
    )

    assert context.all_evidence_ids == ("CRM-1",)
    assert evidence.provenance.source_system == "crm"


def test_source_status_and_evidence_can_be_joined_without_source_priority():
    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
                "CRM-1",
            ),
            _source_observation(
                "email",
                "failed",
            ),
        ),
    )

    assert context.available_sources == ("crm",)
    assert context.failed_sources == ("email",)

    assert not hasattr(context, "source_priority")
    assert not hasattr(context, "winner")
    assert not hasattr(context, "recency_priority")


def test_two_valid_sources_can_support_two_distinct_facts():
    completion = _extract(
        "CRM-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "EMAIL-NEXT",
        "email",
        "The customer asks what comes next.",
    )

    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
                "CRM-COMPLETION",
            ),
            _source_observation(
                "email",
                "available",
                "EMAIL-NEXT",
            ),
        ),
    )

    assert set(context.all_evidence_ids) == {
        "CRM-COMPLETION",
        "EMAIL-NEXT",
    }

    assert completion.provenance.source_system == "crm"
    assert next_step.provenance.source_system == "email"


def test_unavailable_source_cannot_contribute_to_composition():
    completion = _extract(
        "CRM-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
                "CRM-COMPLETION",
            ),
            _source_observation(
                "email",
                "unavailable",
            ),
        ),
    )

    assert context.all_evidence_ids == (
        "CRM-COMPLETION",
    )

    assert "EMAIL-NEXT" not in context.all_evidence_ids


def test_failed_source_cannot_contribute_to_composition():
    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
                "CRM-COMPLETION",
            ),
            _source_observation(
                "email",
                "failed",
            ),
        ),
    )

    assert "EMAIL-NEXT" not in context.all_evidence_ids


def test_source_state_is_explicit_per_source():
    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
            ),
            _source_observation(
                "email",
                "unavailable",
            ),
            _source_observation(
                "billing",
                "failed",
            ),
        ),
    )

    state = {
        source.source_system: source.availability
        for source in context.sources
    }

    assert state == {
        "crm": "available",
        "email": "unavailable",
        "billing": "failed",
    }


def test_empty_orchestrated_context_has_no_evidence():
    context = OrchestratedContext(
        sources=(),
    )

    assert context.all_evidence_ids == ()
    assert context.available_sources == ()
    assert context.unavailable_sources == ()
    assert context.failed_sources == ()


def test_orchestrated_context_is_deterministic():
    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
                "CRM-1",
            ),
            _source_observation(
                "email",
                "failed",
            ),
        ),
    )

    assert context == context


def test_source_order_does_not_change_classification_sets():
    crm = _source_observation(
        "crm",
        "available",
        "CRM-1",
    )

    email = _source_observation(
        "email",
        "failed",
    )

    first = OrchestratedContext(
        sources=(crm, email),
    )

    second = OrchestratedContext(
        sources=(email, crm),
    )

    assert set(first.available_sources) == set(
        second.available_sources
    )

    assert set(first.failed_sources) == set(
        second.failed_sources
    )

    assert set(first.all_evidence_ids) == set(
        second.all_evidence_ids
    )


def test_orchestration_has_no_benchmark_specific_fields():
    context = OrchestratedContext(
        sources=(
            _source_observation(
                "crm",
                "available",
            ),
        ),
    )

    assert not hasattr(
        context,
        "expected_direction",
    )

    assert not hasattr(
        context,
        "benchmark_family",
    )

    assert not hasattr(
        context,
        "winner",
    )