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
class SourceFailure:
    source_system: str
    error_class: str


@dataclass(frozen=True)
class IsolatedSourceResult:
    valid_evidence_ids: tuple[str, ...]
    failures: tuple[SourceFailure, ...]

    @property
    def failed_sources(self) -> tuple[str, ...]:
        return tuple(
            failure.source_system
            for failure in self.failures
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
    *items,
    availability: str = "available",
) -> EvidenceCondition:
    return EvidenceCondition(
        availability=availability,
        items=tuple(items),
    )


def _isolated(
    evidence,
    *failures: SourceFailure,
) -> IsolatedSourceResult:
    valid_ids = tuple(
        item.evidence_id
        for item in evidence
        if (
            item.identity.quality == IdentityQuality.CONFIRMED
            and item.timestamp is not None
        )
    )

    return IsolatedSourceResult(
        valid_evidence_ids=valid_ids,
        failures=tuple(failures),
    )


def test_one_source_timeout_does_not_remove_valid_crm_evidence():
    crm = _extract(
        "CRM-FOLLOWUP",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    result = _isolated(
        (crm,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert result.valid_evidence_ids == (
        "CRM-FOLLOWUP",
    )

    assert result.failed_sources == (
        "email",
    )


def test_one_source_authentication_failure_does_not_remove_other_evidence():
    crm = _extract(
        "CRM-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    email = _extract(
        "EMAIL-NEXT",
        "email",
        "The customer asks what comes next.",
    )

    result = _isolated(
        (
            crm,
            email,
        ),
        SourceFailure(
            source_system="billing",
            error_class="authentication",
        ),
    )

    assert set(result.valid_evidence_ids) == {
        "CRM-COMPLETION",
        "EMAIL-NEXT",
    }

    assert result.failed_sources == (
        "billing",
    )


def test_reasoning_from_valid_source_is_unchanged_by_unrelated_failure():
    crm = _extract(
        "CRM-FOLLOWUP",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    baseline = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            crm,
        ),
    )

    unrelated_failure = SourceFailure(
        source_system="email",
        error_class="timeout",
    )

    isolated = _isolated(
        (crm,),
        unrelated_failure,
    )

    with_failure = _reasoner().evaluate(
        PrimaryState("quote_pending_decision"),
        _condition(
            crm,
        ),
    )

    assert isolated.valid_evidence_ids == (
        "CRM-FOLLOWUP",
    )

    assert with_failure == baseline


def test_failure_metadata_does_not_become_semantic_evidence():
    crm = _extract(
        "CRM-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    result = _isolated(
        (crm,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert result.valid_evidence_ids == (
        "CRM-COMPLETION",
    )

    assert not hasattr(
        result,
        "confirms_completion",
    )

    assert not hasattr(
        result,
        "requests_next_step",
    )


def test_source_failure_does_not_mutate_evidence_semantics():
    evidence = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    before = evidence.semantics

    _isolated(
        (evidence,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert evidence.semantics == before


def test_source_failure_does_not_mutate_evidence_provenance():
    evidence = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    before = evidence.provenance

    _isolated(
        (evidence,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert evidence.provenance == before


def test_multiple_failures_remain_independently_traceable():
    crm = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    result = _isolated(
        (crm,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
        SourceFailure(
            source_system="billing",
            error_class="authorization",
        ),
    )

    assert result.failed_sources == (
        "email",
        "billing",
    )

    assert result.valid_evidence_ids == (
        "CRM",
    )


def test_failure_order_does_not_change_failure_set():
    crm = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    first = _isolated(
        (crm,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
        SourceFailure(
            source_system="billing",
            error_class="authorization",
        ),
    )

    second = _isolated(
        (crm,),
        SourceFailure(
            source_system="billing",
            error_class="authorization",
        ),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert set(first.failed_sources) == set(
        second.failed_sources
    )

    assert first.valid_evidence_ids == (
        second.valid_evidence_ids
    )


def test_a_failed_source_cannot_supply_fake_evidence_id():
    crm = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    result = _isolated(
        (crm,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert "EMAIL" not in result.valid_evidence_ids
    assert "email" not in result.valid_evidence_ids


def test_filtered_evidence_and_source_failure_remain_distinct():
    wrong_identity = _extract(
        "WRONG",
        "email",
        "The customer wants another discussion about the proposal.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    result = _isolated(
        (wrong_identity,),
        SourceFailure(
            source_system="billing",
            error_class="timeout",
        ),
    )

    assert result.valid_evidence_ids == ()
    assert result.failed_sources == (
        "billing",
    )


def test_stale_evidence_and_source_failure_remain_distinct():
    extractor = LexicalNormalizationSemanticExtractor()

    stale = extractor.extract(
        evidence_id="STALE",
        content="The customer wants another discussion about the proposal.",
        source_system="legacy",
        record_id="STALE",
        occurred_at="2026-07-01T10:00:00Z",
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    ).evidence

    result = _isolated(
        (stale,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert result.valid_evidence_ids == (
        "STALE",
    )

    assert result.failed_sources == (
        "email",
    )


def test_failure_is_not_inferred_from_empty_evidence():
    result = _isolated(
        (),
    )

    assert result.valid_evidence_ids == ()
    assert result.failures == ()


def test_failure_requires_explicit_failure_record():
    crm = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    result = _isolated(
        (crm,),
    )

    assert result.failed_sources == ()
    assert result.valid_evidence_ids == (
        "CRM",
    )


def test_source_failure_preserves_independent_source_identity():
    crm = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    result = _isolated(
        (crm,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert crm.provenance.source_system == "crm"
    assert result.failed_sources == ("email",)


def test_source_failure_does_not_create_source_priority():
    crm = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    result = _isolated(
        (crm,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert not hasattr(result, "source_priority")
    assert not hasattr(result, "winner")
    assert not hasattr(result, "recency_priority")


def test_failure_reason_is_preserved():
    result = _isolated(
        (),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert result.failures == (
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )


def test_different_failure_classes_are_not_collapsed():
    result = _isolated(
        (),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
        SourceFailure(
            source_system="billing",
            error_class="authorization",
        ),
    )

    assert {
        failure.error_class
        for failure in result.failures
    } == {
        "timeout",
        "authorization",
    }


def test_failure_isolation_is_deterministic():
    crm = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    first = _isolated(
        (crm,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    second = _isolated(
        (crm,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert first == second


def test_failure_isolation_has_no_benchmark_logic():
    crm = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    result = _isolated(
        (crm,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert not hasattr(
        result,
        "expected_direction",
    )

    assert not hasattr(
        result,
        "benchmark_family",
    )


def test_valid_evidence_and_failure_can_be_reported_together():
    completion = _extract(
        "CRM-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    result = _isolated(
        (completion,),
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )

    assert result.valid_evidence_ids == (
        "CRM-COMPLETION",
    )

    assert result.failures == (
        SourceFailure(
            source_system="email",
            error_class="timeout",
        ),
    )


def test_one_failed_source_does_not_hide_multiple_valid_sources():
    completion = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "EMAIL",
        "email",
        "The customer asks what comes next.",
    )

    support = _extract(
        "SUPPORT",
        "support",
        "The customer wants another discussion about the proposal.",
    )

    result = _isolated(
        (
            completion,
            next_step,
            support,
        ),
        SourceFailure(
            source_system="billing",
            error_class="timeout",
        ),
    )

    assert set(result.valid_evidence_ids) == {
        "CRM",
        "EMAIL",
        "SUPPORT",
    }

    assert result.failed_sources == (
        "billing",
    )


def test_failure_isolation_does_not_select_a_reasoning_winner():
    crm = _extract(
        "CRM",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    email = _extract(
        "EMAIL",
        "email",
        "The customer does not want another discussion about the proposal.",
    )

    result = _isolated(
        (
            crm,
            email,
        ),
        SourceFailure(
            source_system="billing",
            error_class="timeout",
        ),
    )

    assert set(result.valid_evidence_ids) == {
        "CRM",
        "EMAIL",
    }

    assert not hasattr(
        result,
        "winner",
    )