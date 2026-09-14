from __future__ import annotations

from datetime import datetime, timezone

from experiment.v03.evidence import (
    EvidenceCondition,
    EvidenceIdentity,
    EvidenceProvenance,
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)
from experiment.v03.runner import (
    TransitionCase,
    V03TransitionRunner,
)
from experiment.v03.transition_metrics import TransitionDirection


EVALUATION_AT = datetime(
    2026,
    9,
    13,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


def _reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )


def _evidence(
    *,
    content: str,
    semantics: EvidenceSemantics,
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    occurred_at: str = "2026-09-12T10:00:00+00:00",
) -> SemanticEvidence:
    return SemanticEvidence(
        evidence_id="BATTERY",
        content=content,
        provenance=EvidenceProvenance(
            source_system="synthetic",
            record_id="BATTERY",
            occurred_at=datetime.fromisoformat(occurred_at),
        ),
        identity=EvidenceIdentity(
            customer_id="C001",
            quality=identity_quality,
        ),
        semantics=semantics,
    )


def test_small_v03_metric_battery():
    cases = (
        TransitionCase(
            case_id="MR1",
            primary=PrimaryState("quote_pending_decision"),
            secondary=EvidenceCondition(
                availability="available",
                items=(
                    _evidence(
                        content=(
                            "The customer wants another discussion "
                            "about the proposal next week."
                        ),
                        semantics=EvidenceSemantics(
                            topic="proposal",
                            requests_followup=True,
                            concerns_same_work_item=True,
                        ),
                    ),
                ),
            ),
            expected_direction=TransitionDirection.STRENGTHEN,
        ),
        TransitionCase(
            case_id="MR2",
            primary=PrimaryState("quote_pending_decision"),
            secondary=EvidenceCondition(
                availability="available",
                items=(
                    _evidence(
                        content=(
                            "Funding for the proposed amount is approved."
                        ),
                        semantics=EvidenceSemantics(
                            topic="proposal",
                            confirms_approval=True,
                            expresses_acceptance=True,
                            concerns_same_work_item=True,
                        ),
                    ),
                ),
            ),
            expected_direction=TransitionDirection.STRENGTHEN,
        ),
        TransitionCase(
            case_id="MR3",
            primary=PrimaryState("negotiation_open"),
            secondary=EvidenceCondition(
                availability="available",
                items=(
                    _evidence(
                        content="The customer rejects the revised terms.",
                        semantics=EvidenceSemantics(
                            topic="commercial_terms",
                            expresses_rejection=True,
                            concerns_same_work_item=True,
                        ),
                    ),
                ),
            ),
            expected_direction=TransitionDirection.WEAKEN,
        ),
        TransitionCase(
            case_id="MR4",
            primary=PrimaryState("quote_pending_decision"),
            secondary=EvidenceCondition(
                availability="available",
                items=(
                    _evidence(
                        content=(
                            "The customer is discussing a separate rollout."
                        ),
                        semantics=EvidenceSemantics(
                            topic="store_rollout",
                            concerns_same_work_item=False,
                        ),
                    ),
                ),
            ),
            expected_direction=TransitionDirection.PRESERVE,
        ),
        TransitionCase(
            case_id="MR5",
            primary=PrimaryState("quote_pending_decision"),
            secondary=EvidenceCondition(
                availability="available",
                items=(
                    _evidence(
                        content=(
                            "Another customer wants to discuss the proposal."
                        ),
                        semantics=EvidenceSemantics(
                            topic="proposal",
                            requests_followup=True,
                            concerns_same_work_item=True,
                        ),
                        identity_quality=IdentityQuality.NO_MATCH,
                    ),
                ),
            ),
            expected_direction=TransitionDirection.PRESERVE,
        ),
        TransitionCase(
            case_id="MR6",
            primary=PrimaryState("quote_pending_decision"),
            secondary=EvidenceCondition(
                availability="available",
                items=(
                    _evidence(
                        content=(
                            "A customer wants another proposal discussion."
                        ),
                        semantics=EvidenceSemantics(
                            topic="proposal",
                            requests_followup=True,
                            concerns_same_work_item=True,
                        ),
                        identity_quality=IdentityQuality.AMBIGUOUS,
                    ),
                ),
            ),
            expected_direction=TransitionDirection.PRESERVE,
        ),
        TransitionCase(
            case_id="MR7",
            primary=PrimaryState("quote_pending_decision"),
            secondary=EvidenceCondition(
                availability="available",
                items=(
                    _evidence(
                        content=(
                            "The customer wanted another proposal discussion."
                        ),
                        semantics=EvidenceSemantics(
                            topic="proposal",
                            requests_followup=True,
                            concerns_same_work_item=True,
                        ),
                        occurred_at="2026-07-01T10:00:00+00:00",
                    ),
                ),
            ),
            expected_direction=TransitionDirection.PRESERVE,
        ),
        TransitionCase(
            case_id="MR8",
            primary=PrimaryState("quote_pending_decision"),
            secondary=EvidenceCondition(
                availability="unavailable",
                items=(),
            ),
            expected_direction=TransitionDirection.PRESERVE,
        ),
        TransitionCase(
            case_id="MR9",
            primary=PrimaryState("quote_pending_decision"),
            secondary=EvidenceCondition(
                availability="available",
                items=(),
            ),
            expected_direction=TransitionDirection.PRESERVE,
        ),
    )

    summary = V03TransitionRunner(_reasoner()).run(cases)

    assert len(summary.measurements) == 9

    assert summary.directional_correctness.total == 9
    assert summary.directional_correctness.correct == 9
    assert summary.directional_correctness.rate == 1.0

    assert summary.unsupported_change_rate == 0.0