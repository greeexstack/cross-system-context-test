from __future__ import annotations

from experiment.v03.evidence import IdentityQuality
from experiment.v03.extractor import RuleBasedSemanticExtractor


def test_followup_paraphrase_extracts_same_fact_pattern() -> None:
    extractor = RuleBasedSemanticExtractor()

    original = extractor.extract(
        evidence_id="E1",
        content=(
            "The customer is currently assessing the proposal and "
            "would like another discussion next week."
        ),
        source_system="test",
        record_id="E1",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
    )

    paraphrase = extractor.extract(
        evidence_id="E2",
        content=(
            "The customer is evaluating the offer and wants to arrange "
            "a further discussion in the coming week."
        ),
        source_system="test",
        record_id="E2",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
    )

    assert original.evidence.semantics.requests_followup is True
    assert paraphrase.evidence.semantics.requests_followup is True


def test_supporting_evidence_extracts_approval() -> None:
    extractor = RuleBasedSemanticExtractor()

    result = extractor.extract(
        evidence_id="E3",
        content=(
            "The customer has budget approval for the quoted amount "
            "and says procurement is progressing."
        ),
        source_system="test",
        record_id="E3",
        occurred_at="2026-09-12T11:00:00Z",
        customer_id="C001",
    )

    assert result.evidence.semantics.confirms_approval is True
    assert result.evidence.semantics.expresses_acceptance is True


def test_contradictory_evidence_extracts_rejection() -> None:
    extractor = RuleBasedSemanticExtractor()

    result = extractor.extract(
        evidence_id="E4",
        content=(
            "The customer rejects the revised commercial terms and "
            "wants the proposal reconsidered."
        ),
        source_system="test",
        record_id="E4",
        occurred_at="2026-09-12T13:00:00Z",
        customer_id="C001",
    )

    assert result.evidence.semantics.expresses_rejection is True


def test_irrelevant_evidence_is_marked_as_not_same_work_item() -> None:
    extractor = RuleBasedSemanticExtractor()

    result = extractor.extract(
        evidence_id="E5",
        content=(
            "The customer is discussing a different store rollout "
            "and says nothing about this quoted opportunity."
        ),
        source_system="test",
        record_id="E5",
        occurred_at="2026-09-12T08:00:00Z",
        customer_id="C001",
    )

    assert result.evidence.semantics.concerns_same_work_item is False


def test_service_next_step_extracts_completion_and_followup() -> None:
    extractor = RuleBasedSemanticExtractor()

    result = extractor.extract(
        evidence_id="E6",
        content=(
            "The customer confirms the migration workshop is finished "
            "and asks what happens in the following handoff."
        ),
        source_system="test",
        record_id="E6",
        occurred_at="2026-09-12T12:00:00Z",
        customer_id="C001",
    )

    semantics = result.evidence.semantics

    assert semantics.confirms_completion is True
    assert semantics.requests_next_step is True


def test_identity_information_is_preserved() -> None:
    extractor = RuleBasedSemanticExtractor()

    result = extractor.extract(
        evidence_id="E7",
        content="The customer wants to discuss the proposal again.",
        source_system="email",
        record_id="M007",
        occurred_at="2026-09-12T12:00:00Z",
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    )

    assert result.evidence.provenance.source_system == "email"
    assert result.evidence.provenance.record_id == "M007"
    assert result.evidence.identity.customer_id == "C001"
    assert result.evidence.identity.quality == IdentityQuality.CONFIRMED


def test_extractor_does_not_emit_benchmark_transition_labels() -> None:
    extractor = RuleBasedSemanticExtractor()

    result = extractor.extract(
        evidence_id="E8",
        content="The customer wants another discussion about the proposal.",
        source_system="test",
        record_id="E8",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="C001",
    )

    assert not hasattr(result.evidence.semantics, "expected_transition")
    assert not hasattr(result.evidence.semantics, "support_level")
    assert not hasattr(result.evidence.semantics, "interpretation_class")