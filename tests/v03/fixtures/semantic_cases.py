from __future__ import annotations

from experiment.v03.evidence import (
    EvidenceCondition,
    EvidenceIdentity,
    EvidenceProvenance,
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)


def _evidence(
    *,
    evidence_id: str,
    customer_id: str = "C001",
    semantics: EvidenceSemantics,
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    occurred_at: str = "2026-09-12T10:00:00+00:00",
    content: str = "synthetic evidence",
) -> SemanticEvidence:
    from datetime import datetime

    return SemanticEvidence(
        evidence_id=evidence_id,
        content=content,
        provenance=EvidenceProvenance(
            source_system="synthetic_test_source",
            record_id=evidence_id,
            occurred_at=datetime.fromisoformat(occurred_at),
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


# ---------------------------------------------------------------------------
# F01 — relevant follow-up evidence
# ---------------------------------------------------------------------------

F01_RELEVANT = _available(
    _evidence(
        evidence_id="F01-EVIDENCE",
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
        content=(
            "The customer wants another discussion about the proposal "
            "next week."
        ),
    )
)


# ---------------------------------------------------------------------------
# F02 — supporting / corroborating evidence
# ---------------------------------------------------------------------------

F02_SUPPORTING = _available(
    _evidence(
        evidence_id="F02-EVIDENCE",
        semantics=EvidenceSemantics(
            topic="proposal",
            confirms_approval=True,
            expresses_acceptance=True,
            concerns_same_work_item=True,
        ),
        content=(
            "The quoted amount has budget approval and the purchasing "
            "process is progressing."
        ),
    )
)


# ---------------------------------------------------------------------------
# F03 — contradictory evidence
# ---------------------------------------------------------------------------

F03_CONTRADICTORY = _available(
    _evidence(
        evidence_id="F03-EVIDENCE",
        semantics=EvidenceSemantics(
            topic="commercial_terms",
            expresses_rejection=True,
            concerns_same_work_item=True,
        ),
        content=(
            "The customer rejects the revised commercial terms and "
            "wants the proposal reconsidered."
        ),
    )
)


# ---------------------------------------------------------------------------
# F04 — irrelevant evidence
# ---------------------------------------------------------------------------

F04_IRRELEVANT = _available(
    _evidence(
        evidence_id="F04-EVIDENCE",
        semantics=EvidenceSemantics(
            topic="store_rollout",
            concerns_same_work_item=False,
        ),
        content=(
            "The customer is discussing a separate store rollout and "
            "has not provided an update on the quoted opportunity."
        ),
    )
)


# ---------------------------------------------------------------------------
# F05 — wrong identity
# ---------------------------------------------------------------------------

F05_WRONG_IDENTITY = _available(
    _evidence(
        evidence_id="F05-EVIDENCE",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
        content=(
            "A customer is asking to discuss the proposal again, but "
            "the communication belongs to another customer."
        ),
    )
)


# ---------------------------------------------------------------------------
# F06 — ambiguous identity
# ---------------------------------------------------------------------------

F06_AMBIGUOUS_IDENTITY = _available(
    _evidence(
        evidence_id="F06-EVIDENCE",
        identity_quality=IdentityQuality.AMBIGUOUS,
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
        content=(
            "A customer appears to want another proposal discussion, "
            "but the source identity cannot be confidently resolved."
        ),
    )
)


# ---------------------------------------------------------------------------
# F07 — stale evidence
# ---------------------------------------------------------------------------

F07_STALE = _available(
    _evidence(
        evidence_id="F07-EVIDENCE",
        occurred_at="2026-08-01T10:00:00+00:00",
        semantics=EvidenceSemantics(
            topic="proposal",
            requests_followup=True,
            concerns_same_work_item=True,
        ),
        content=(
            "The customer wanted another discussion about the proposal."
        ),
    )
)


# ---------------------------------------------------------------------------
# F08 — unavailable secondary system
# ---------------------------------------------------------------------------

F08_UNAVAILABLE = _unavailable()


# ---------------------------------------------------------------------------
# F10 — completed service + requested next step
# ---------------------------------------------------------------------------

F10_SERVICE_NEXT_STEP = _available(
    _evidence(
        evidence_id="F10-EVIDENCE",
        semantics=EvidenceSemantics(
            topic="service",
            confirms_completion=True,
            requests_next_step=True,
            concerns_same_work_item=True,
        ),
        content=(
            "The migration workshop is complete and the customer is "
            "asking about the next handoff."
        ),
    )
)


# ---------------------------------------------------------------------------
# Semantic-equivalence pairs
#
# These pairs intentionally have identical semantic structures while their
# natural-language content differs. They are used to test the reasoning layer,
# not the natural-language extractor.
# ---------------------------------------------------------------------------

F01_EQUIVALENT_A = _evidence(
    evidence_id="F01-A",
    semantics=EvidenceSemantics(
        topic="proposal",
        requests_followup=True,
        concerns_same_work_item=True,
    ),
    content=(
        "The customer is reviewing the proposal and wants another "
        "discussion next week."
    ),
)

F01_EQUIVALENT_B = _evidence(
    evidence_id="F01-B",
    semantics=EvidenceSemantics(
        topic="proposal",
        requests_followup=True,
        concerns_same_work_item=True,
    ),
    content=(
        "The customer is considering the offer and would like to "
        "speak about it again during the coming week."
    ),
)


F02_EQUIVALENT_A = _evidence(
    evidence_id="F02-A",
    semantics=EvidenceSemantics(
        topic="proposal",
        confirms_approval=True,
        expresses_acceptance=True,
        concerns_same_work_item=True,
    ),
    content=(
        "The proposed amount is within the customer's approved budget."
    ),
)

F02_EQUIVALENT_B = _evidence(
    evidence_id="F02-B",
    semantics=EvidenceSemantics(
        topic="proposal",
        confirms_approval=True,
        expresses_acceptance=True,
        concerns_same_work_item=True,
    ),
    content=(
        "Funding has been authorized for the amount quoted to the customer."
    ),
)


F03_EQUIVALENT_A = _evidence(
    evidence_id="F03-A",
    semantics=EvidenceSemantics(
        topic="commercial_terms",
        expresses_rejection=True,
        concerns_same_work_item=True,
    ),
    content=(
        "The customer rejects the revised commercial terms."
    ),
)

F03_EQUIVALENT_B = _evidence(
    evidence_id="F03-B",
    semantics=EvidenceSemantics(
        topic="commercial_terms",
        expresses_rejection=True,
        concerns_same_work_item=True,
    ),
    content=(
        "The customer is unwilling to accept the updated commercial terms."
    ),
)


F10_EQUIVALENT_A = _evidence(
    evidence_id="F10-A",
    semantics=EvidenceSemantics(
        topic="service",
        confirms_completion=True,
        requests_next_step=True,
        concerns_same_work_item=True,
    ),
    content=(
        "The migration session has finished and the customer asks "
        "what comes next."
    ),
)

F10_EQUIVALENT_B = _evidence(
    evidence_id="F10-B",
    semantics=EvidenceSemantics(
        topic="service",
        confirms_completion=True,
        requests_next_step=True,
        concerns_same_work_item=True,
    ),
    content=(
        "The migration workshop is complete, and the customer wants "
        "guidance on the following handoff."
    ),
)