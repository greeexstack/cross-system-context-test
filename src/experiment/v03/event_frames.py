from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class FramePolarity(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EventFrame:
    """
    Canonical factual event representation.

    This frame describes observed content. It does not encode a business
    decision, benchmark expectation, or downstream interpretation.
    """

    actor: str | None = None
    action: str | None = None
    object: str | None = None
    state: str | None = None
    polarity: FramePolarity = FramePolarity.UNKNOWN
    temporal_reference: str | None = None
    relevance: str | None = None


@dataclass(frozen=True)
class EventFrameExtractionResult:
    frames: tuple[EventFrame, ...]
    normalized_text: str


class CanonicalEventFrameExtractor:
    """
    Experimental dependency-free event-frame extractor.

    This deliberately remains a lexical intermediate model. Its purpose is
    to test whether a canonical factual representation is more stable under
    wording variation than the current boolean phrase-detection model.

    It never receives benchmark labels or expected transitions.
    """

    _FOLLOWUP_ACTION_WORDS = {
        "ask",
        "asked",
        "asking",
        "request",
        "requested",
        "want",
        "wants",
        "wanted",
        "suggest",
        "suggested",
        "reconnect",
        "reconnects",
        "reconnected",
        "speak",
        "speaks",
        "spoke",
        "talk",
        "talks",
        "discuss",
        "discusses",
        "discussed",
        "discussion",
        "conversation",
        "call",
        "meeting",
    }

    _REVIEW_WORDS = {
        "review",
        "reviewed",
        "reviewing",
        "consider",
        "considered",
        "considering",
        "assess",
        "assessed",
        "assessing",
        "examine",
        "examined",
        "examining",
        "evaluate",
        "evaluated",
        "evaluating",
    }

    _PROPOSAL_WORDS = {
        "proposal",
        "offer",
        "quote",
        "quoted",
        "plan",
    }

    _APPROVAL_WORDS = {
        "approved",
        "approval",
        "authorize",
        "authorized",
        "authorization",
        "clearance",
        "cleared",
        "funding",
        "budget",
    }

    _PROCUREMENT_WORDS = {
        "procurement",
        "purchasing",
        "purchase",
        "buying",
    }

    _PROGRESS_WORDS = {
        "progress",
        "progressing",
        "started",
        "begun",
        "underway",
        "moving",
        "advancing",
        "processing",
    }

    _REJECTION_WORDS = {
        "reject",
        "rejected",
        "rejects",
        "unacceptable",
        "refuse",
        "refused",
        "refuses",
        "unwilling",
        "won't",
        "will",
        "accept",
        "acceptance",
        "terms",
        "conditions",
    }

    _COMPLETION_WORDS = {
        "complete",
        "completed",
        "finished",
        "finish",
        "concluded",
        "over",
        "done",
    }

    _NEXT_STEP_WORDS = {
        "next",
        "following",
        "subsequent",
    }

    _SERVICE_WORDS = {
        "service",
        "implementation",
        "workshop",
        "rollout",
        "migration",
        "session",
        "handoff",
        "handover",
        "transition",
    }

    _IRRELEVANCE_MARKERS = {
        "different",
        "separate",
        "another",
        "unrelated",
    }

    _IRRELEVANT_OBJECT_WORDS = {
        "project",
        "rollout",
        "deployment",
        "initiative",
        "location",
        "branch",
        "store",
    }

    _NO_INFORMATION_PATTERNS = (
        r"\bnothing\s+(?:was\s+)?said\s+about\b",
        r"\bno\s+(?:update|information|statement)\b",
        r"\bcontains\s+no\s+information\b",
        r"\bprovid(?:es|ing)\s+no\s+(?:information|update)\b",
        r"\bwithout\s+providing\s+(?:any\s+)?update\b",
    )

    def extract(
        self,
        *,
        content: str,
    ) -> EventFrameExtractionResult:
        normalized = self._normalize(content)
        tokens = set(re.findall(r"[a-z0-9']+", normalized))

        frames: list[EventFrame] = []

        relevance = self._relevance(normalized, tokens)

        if relevance == "different_work_item":
            frames.append(
                EventFrame(
                    actor="customer",
                    action="discuss",
                    object=None,
                    state="different_work_item",
                    polarity=FramePolarity.POSITIVE,
                    relevance=relevance,
                )
            )
            return EventFrameExtractionResult(
                frames=tuple(frames),
                normalized_text=normalized,
            )

        proposal_context = bool(
            tokens.intersection(self._PROPOSAL_WORDS)
        )

        if (
            proposal_context
            and tokens.intersection(self._REVIEW_WORDS)
        ):
            frames.append(
                EventFrame(
                    actor="customer",
                    action="review",
                    object="proposal",
                    state="under_review",
                    polarity=FramePolarity.POSITIVE,
                    relevance=relevance,
                )
            )

        if (
            proposal_context
            and tokens.intersection(self._FOLLOWUP_ACTION_WORDS)
            and self._has_followup_target(tokens)
        ):
            frames.append(
                EventFrame(
                    actor="customer",
                    action="request",
                    object="followup_conversation",
                    state="requested",
                    polarity=FramePolarity.POSITIVE,
                    temporal_reference=self._temporal_reference(
                        normalized
                    ),
                    relevance=relevance,
                )
            )

        if self._has_budget_approval(normalized, tokens):
            frames.append(
                EventFrame(
                    actor="customer",
                    action="confirm",
                    object="quote",
                    state="budget_approved",
                    polarity=FramePolarity.POSITIVE,
                    relevance=relevance,
                )
            )

        if (
            tokens.intersection(self._PROCUREMENT_WORDS)
            and tokens.intersection(self._PROGRESS_WORDS)
        ):
            frames.append(
                EventFrame(
                    actor="customer",
                    action="report",
                    object="procurement",
                    state="progressing",
                    polarity=FramePolarity.POSITIVE,
                    relevance=relevance,
                )
            )

        if self._has_commercial_rejection(normalized, tokens):
            frames.append(
                EventFrame(
                    actor="customer",
                    action="accept",
                    object="commercial_terms",
                    state="rejected",
                    polarity=FramePolarity.NEGATIVE,
                    relevance=relevance,
                )
            )

        if (
            tokens.intersection(self._COMPLETION_WORDS)
            and tokens.intersection(self._SERVICE_WORDS)
        ):
            frames.append(
                EventFrame(
                    actor="customer",
                    action="confirm",
                    object="service",
                    state="completed",
                    polarity=FramePolarity.POSITIVE,
                    relevance=relevance,
                )
            )

        if self._has_next_step(normalized, tokens):
            frames.append(
                EventFrame(
                    actor="customer",
                    action="request",
                    object="handoff"
                    if "handoff" in tokens
                    or "handover" in tokens
                    or "transition" in tokens
                    else "next_step",
                    state="next_step",
                    polarity=FramePolarity.POSITIVE,
                    temporal_reference="next_step",
                    relevance=relevance,
                )
            )

        return EventFrameExtractionResult(
            frames=tuple(frames),
            normalized_text=normalized,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = text.strip().lower()
        normalized = normalized.replace("â€™", "'")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    @classmethod
    def _has_followup_target(
        cls,
        tokens: set[str],
    ) -> bool:
        discussion_target = bool(
            tokens.intersection(
                {
                    "discussion",
                    "conversation",
                    "call",
                    "meeting",
                    "reconnect",
                    "speak",
                    "talk",
                }
            )
        )

        temporal_target = bool(
            tokens.intersection(
                {
                    "next",
                    "thursday",
                    "week",
                    "later",
                }
            )
        )

        return discussion_target or temporal_target

    @classmethod
    def _has_budget_approval(
        cls,
        normalized: str,
        tokens: set[str],
    ) -> bool:
        has_financial_context = bool(
            tokens.intersection(
                {
                    "budget",
                    "funding",
                    "amount",
                    "price",
                    "quote",
                    "quoted",
                }
            )
        )

        has_approval_signal = bool(
            tokens.intersection(
                {
                    "approved",
                    "approval",
                    "authorized",
                    "authorization",
                    "clearance",
                    "cleared",
                    "fits",
                    "covered",
                    "within",
                }
            )
        )

        return (
            has_financial_context
            and has_approval_signal
        )

    @classmethod
    def _has_commercial_rejection(
        cls,
        normalized: str,
        tokens: set[str],
    ) -> bool:
        has_terms = bool(
    tokens.intersection(
        {
            "terms",
            "conditions",
        }
    )
) or bool(
    re.search(
        r"\bcommercial\s+arrangement\b",
        normalized,
    )
)
        has_rejection = bool(
    tokens.intersection(
        {
            "rejected",
            "reject",
            "unacceptable",
            "unwilling",
            "refused",
        }
    )
) or bool(
    re.search(
        r"\b(?:will not|won't)\s+accept\b"
        r"|\bdoes not meet\b[^.?!;]*\bneeds?\b"
        r"|\bdoesn't meet\b[^.?!;]*\bneeds?\b",
        normalized,
    )
)

        return has_terms and has_rejection

    @classmethod
    def _has_next_step(
        cls,
        normalized: str,
        tokens: set[str],
    ) -> bool:
        explicit_next = bool(
            tokens.intersection(cls._NEXT_STEP_WORDS)
        )

        next_patterns = (
            r"\bwhat\s+comes\s+next\b",
            r"\bwhat\s+happens\s+next\b",
            r"\bwhat\s+happens\s+after\b",
            r"\bwhat\s+should\s+happen\b",
            r"\bwants?\s+to\s+know\s+.*\bnext\b",
            r"\basks?\s+.*\bnext\b",
        )

        return explicit_next or any(
            re.search(pattern, normalized)
            for pattern in next_patterns
        )

    @classmethod
    def _temporal_reference(
        cls,
        normalized: str,
    ) -> str | None:
        match = re.search(
            r"\bnext\s+([a-z0-9-]+(?:\s+[a-z0-9-]+)?)",
            normalized,
        )

        if match:
            return match.group(0)

        return None

    @classmethod
    def _relevance(
        cls,
        normalized: str,
        tokens: set[str],
    ) -> str | None:
        if not tokens.intersection(
            cls._IRRELEVANCE_MARKERS
        ):
            return None

        has_different_object = bool(
            tokens.intersection(
                cls._IRRELEVANT_OBJECT_WORDS
            )
        )

        has_no_information = any(
            re.search(
                pattern,
                normalized,
            )
            for pattern in cls._NO_INFORMATION_PATTERNS
        )

        if has_different_object and (
            has_no_information
            or "different" in tokens
            or "separate" in tokens
            or "another" in tokens
        ):
            return "different_work_item"

        return None