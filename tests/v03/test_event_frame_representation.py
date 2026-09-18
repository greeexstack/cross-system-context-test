from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FramePolarity(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EventFrame:
    actor: str | None = None
    action: str | None = None
    object: str | None = None
    state: str | None = None
    polarity: FramePolarity = FramePolarity.UNKNOWN
    temporal_reference: str | None = None
    relevance: str | None = None


FORBIDDEN_FRAME_FIELDS = {
    "expected_transition",
    "ground_truth",
    "benchmark_family",
    "pair_id",
    "support_level",
    "interpretation_class",
    "decision_strength",
    "recommendation",
    "finding",
}


def test_event_frame_contains_only_factual_fields() -> None:
    fields = set(
        EventFrame.__dataclass_fields__
    )

    assert fields.isdisjoint(
        FORBIDDEN_FRAME_FIELDS
    )


def test_event_frame_distinguishes_unknown_from_negative() -> None:
    unknown = EventFrame(
        actor="customer",
        action="accept",
        object="commercial_terms",
        state=None,
        polarity=FramePolarity.UNKNOWN,
    )

    negative = EventFrame(
        actor="customer",
        action="accept",
        object="commercial_terms",
        state="rejected",
        polarity=FramePolarity.NEGATIVE,
    )

    assert unknown != negative
    assert unknown.polarity is FramePolarity.UNKNOWN
    assert negative.polarity is FramePolarity.NEGATIVE


def test_event_frame_supports_multiple_factual_events() -> None:
    completion = EventFrame(
        actor="customer",
        action="confirm",
        object="service",
        state="completed",
        polarity=FramePolarity.POSITIVE,
    )

    next_step = EventFrame(
        actor="customer",
        action="request",
        object="handoff",
        state="next_step",
        polarity=FramePolarity.POSITIVE,
    )

    frames = (completion, next_step)

    assert len(frames) == 2
    assert frames[0].state == "completed"
    assert frames[1].state == "next_step"


def test_event_frame_does_not_encode_business_decision() -> None:
    frame = EventFrame(
        actor="customer",
        action="request",
        object="followup_conversation",
        state="requested",
        polarity=FramePolarity.POSITIVE,
        relevance="same_work_item",
    )

    assert not any(
        hasattr(frame, name)
        for name in FORBIDDEN_FRAME_FIELDS
    )