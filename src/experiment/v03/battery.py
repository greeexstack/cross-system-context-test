from __future__ import annotations

from datetime import datetime, timezone

from .evidence import (
    EvidenceCondition,
    EvidenceIdentity,
    EvidenceProvenance,
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)
from .reasoner import PrimaryState
from .runner import TransitionCase
from .transition_metrics import TransitionDirection


EVALUATION_AT = datetime(
    2026,
    9,
    13,
    12,
    0,
    tzinfo=timezone.utc,
)

EVIDENCE_TIME = datetime(
    2026,
    9,
    12,
    10,
    0,
    tzinfo=timezone.utc,
)


def _evidence(
    *,
    evidence_id: str,
    content: str,
    semantics: EvidenceSemantics,
    customer_id: str | None = "C001",
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    occurred_at: datetime | None = EVIDENCE_TIME,
) -> SemanticEvidence:
    return SemanticEvidence(
        evidence_id=evidence_id,
        content=content,
        provenance=EvidenceProvenance(
            source_system="synthetic",
            record_id=evidence_id,
            occurred_at=occurred_at,
        ),
        identity=EvidenceIdentity(
            customer_id=customer_id,
            quality=identity_quality,
        ),
        semantics=semantics,
    )


def _available(*items: SemanticEvidence) -> EvidenceCondition:
    return EvidenceCondition(
        availability="available",
        items=items,
    )


def _unavailable() -> EvidenceCondition:
    return EvidenceCondition(
        availability="unavailable",
        items=(),
    )


def build_v03_battery() -> tuple[TransitionCase, ...]:
    """
    Small controlled v0.3 transition battery.

    Expected directions are evaluator-side metadata. They are never
    embedded in the evidence supplied to the reasoner.
    """

    return (
        # --------------------------------------------------------------
        # MR-1 — relevant evidence
        # --------------------------------------------------------------
        TransitionCase(
            case_id="MR1-relevant-followup",
            primary=PrimaryState("quote_pending_decision"),
            secondary=_available(
                _evidence(
                    evidence_id="MR1",
                    content=(
                        "The customer wants another discussion about "
                        "the proposal next week."
                    ),
                    semantics=EvidenceSemantics(
                        topic="proposal",
                        requests_followup=True,
                        concerns_same_work_item=True,
                    ),
                ),
            ),
            expected_direction=TransitionDirection.STRENGTHEN,
        ),

        # --------------------------------------------------------------
        # MR-2 — supporting evidence
        # --------------------------------------------------------------
        TransitionCase(
            case_id="MR2-supporting-approval",
            primary=PrimaryState("quote_pending_decision"),
            secondary=_available(
                _evidence(
                    evidence_id="MR2",
                    content=(
                        "The quoted amount has budget approval and "
                        "the purchasing process is progressing."
                    ),
                    semantics=EvidenceSemantics(
                        topic="proposal",
                        confirms_approval=True,
                        expresses_acceptance=True,
                        concerns_same_work_item=True,
                    ),
                ),
            ),
            expected_direction=TransitionDirection.STRENGTHEN,
        ),

        # --------------------------------------------------------------
        # MR-3 — contradictory evidence
        # --------------------------------------------------------------
        TransitionCase(
            case_id="MR3-contradictory-rejection",
            primary=PrimaryState("negotiation_open"),
            secondary=_available(
                _evidence(
                    evidence_id="MR3",
                    content=(
                        "The customer rejects the revised commercial "
                        "terms and wants the proposal reconsidered."
                    ),
                    semantics=EvidenceSemantics(
                        topic="commercial_terms",
                        expresses_rejection=True,
                        concerns_same_work_item=True,
                    ),
                ),
            ),
            expected_direction=TransitionDirection.WEAKEN,
        ),

        # --------------------------------------------------------------
        # MR-4 — irrelevant evidence
        # --------------------------------------------------------------
        TransitionCase(
            case_id="MR4-irrelevant-work",
            primary=PrimaryState("quote_pending_decision"),
            secondary=_available(
                _evidence(
                    evidence_id="MR4",
                    content=(
                        "The customer is discussing a separate store "
                        "rollout and says nothing about this opportunity."
                    ),
                    semantics=EvidenceSemantics(
                        topic="store_rollout",
                        concerns_same_work_item=False,
                    ),
                ),
            ),
            expected_direction=TransitionDirection.PRESERVE,
        ),

        # --------------------------------------------------------------
        # MR-5 — wrong identity
        # --------------------------------------------------------------
        TransitionCase(
            case_id="MR5-wrong-identity",
            primary=PrimaryState("quote_pending_decision"),
            secondary=_available(
                _evidence(
                    evidence_id="MR5",
                    content=(
                        "The customer wants another discussion "
                        "about the proposal."
                    ),
                    semantics=EvidenceSemantics(
                        topic="proposal",
                        requests_followup=True,
                        concerns_same_work_item=True,
                    ),
                    customer_id="C999",
                    identity_quality=IdentityQuality.NO_MATCH,
                ),
            ),
            expected_direction=TransitionDirection.PRESERVE,
        ),

        # --------------------------------------------------------------
        # MR-6 — ambiguous identity
        # --------------------------------------------------------------
        TransitionCase(
            case_id="MR6-ambiguous-identity",
            primary=PrimaryState("quote_pending_decision"),
            secondary=_available(
                _evidence(
                    evidence_id="MR6",
                    content=(
                        "A customer wants another discussion about "
                        "the proposal."
                    ),
                    semantics=EvidenceSemantics(
                        topic="proposal",
                        requests_followup=True,
                        concerns_same_work_item=True,
                    ),
                    identity_quality=IdentityQuality.AMBIGUOUS,
                ),
            ),
            expected_direction=TransitionDirection.PRESERVE,
        ),

        # --------------------------------------------------------------
        # MR-7 — stale evidence
        # --------------------------------------------------------------
        TransitionCase(
            case_id="MR7-stale",
            primary=PrimaryState("quote_pending_decision"),
            secondary=_available(
                _evidence(
                    evidence_id="MR7",
                    content=(
                        "The customer wanted another discussion "
                        "about the proposal."
                    ),
                    semantics=EvidenceSemantics(
                        topic="proposal",
                        requests_followup=True,
                        concerns_same_work_item=True,
                    ),
                    occurred_at=datetime(
                        2026,
                        7,
                        1,
                        10,
                        0,
                        tzinfo=timezone.utc,
                    ),
                ),
            ),
            expected_direction=TransitionDirection.PRESERVE,
        ),

        # --------------------------------------------------------------
        # MR-8 — unavailable source
        # --------------------------------------------------------------
        TransitionCase(
            case_id="MR8-unavailable-source",
            primary=PrimaryState("quote_pending_decision"),
            secondary=_unavailable(),
            expected_direction=TransitionDirection.PRESERVE,
        ),

        # --------------------------------------------------------------
        # MR-9 — evidence removed / primary-only
        # --------------------------------------------------------------
        TransitionCase(
            case_id="MR9-no-secondary",
            primary=PrimaryState("quote_pending_decision"),
            secondary=_available(),
            expected_direction=TransitionDirection.PRESERVE,
        ),
    )


def build_f10_case() -> TransitionCase:
    """
    Dedicated service-transition case kept separate because it has
    a compound semantic condition.
    """

    return TransitionCase(
        case_id="F10-service-next-step",
        primary=PrimaryState(
            "service_completed_next_step_unrecorded"
        ),
        secondary=_available(
            _evidence(
                evidence_id="F10",
                content=(
                    "The migration workshop is complete and the customer "
                    "is asking about the next handoff."
                ),
                semantics=EvidenceSemantics(
                    topic="service",
                    confirms_completion=True,
                    requests_next_step=True,
                    concerns_same_work_item=True,
                ),
            ),
        ),
        expected_direction=TransitionDirection.STRENGTHEN,
    )