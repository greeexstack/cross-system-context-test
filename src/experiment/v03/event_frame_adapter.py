from __future__ import annotations

from .evidence import EvidenceSemantics
from .event_frames import EventFrame


def frames_to_semantics(
    frames: tuple[EventFrame, ...],
) -> EvidenceSemantics:
    """
    Compatibility adapter from factual event frames to the existing
    EvidenceSemantics contract.

    This adapter contains no benchmark labels or business decisions.
    It maps only factual frame content into the existing factual fields
    consumed by the current v0.3 reasoner.
    """

    requests_followup = any(
        frame.action == "request"
        and frame.object == "followup_conversation"
        and frame.state == "requested"
        and frame.polarity.value == "positive"
        for frame in frames
    )

    confirms_approval = any(
        frame.action == "confirm"
        and frame.object == "quote"
        and frame.state == "budget_approved"
        and frame.polarity.value == "positive"
        for frame in frames
    )

    expresses_rejection = any(
        frame.action == "accept"
        and frame.object == "commercial_terms"
        and frame.state == "rejected"
        and frame.polarity.value == "negative"
        for frame in frames
    )

    confirms_completion = any(
        frame.action == "confirm"
        and frame.object == "service"
        and frame.state == "completed"
        and frame.polarity.value == "positive"
        for frame in frames
    )

    requests_next_step = any(
        frame.action == "request"
        and frame.object in {"handoff", "next_step"}
        and frame.state == "next_step"
        and frame.polarity.value == "positive"
        for frame in frames
    )

    different_work_item = any(
        frame.relevance == "different_work_item"
        for frame in frames
    )

    topic = None

    if any(
        frame.object in {"proposal", "quote", "followup_conversation"}
        for frame in frames
    ):
        topic = "proposal"
    elif any(
        frame.object == "commercial_terms"
        for frame in frames
    ):
        topic = "commercial_terms"
    elif any(
        frame.object in {"service", "handoff"}
        for frame in frames
    ):
        topic = "service"
    elif any(
        frame.object == "procurement"
        for frame in frames
    ):
        topic = "procurement"

    return EvidenceSemantics(
        topic=topic,
        requests_followup=(
            True
            if requests_followup
            else None
        ),
        expresses_acceptance=(
            None
        ),
        expresses_rejection=(
            True
            if expresses_rejection
            else None
        ),
        confirms_approval=(
            True
            if confirms_approval
            else None
        ),
        confirms_completion=(
            True
            if confirms_completion
            else None
        ),
        requests_next_step=(
            True
            if requests_next_step
            else None
        ),
        concerns_same_work_item=(
            False
            if different_work_item
            else None
        ),
    )