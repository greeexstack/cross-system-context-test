from __future__ import annotations

from dataclasses import dataclass
import re

from .event_frames import (
    EventFrame,
    EventFrameExtractionResult,
    FramePolarity,
)


@dataclass(frozen=True)
class LocalClause:
    text: str
    index: int


class ClauseLocalEventFrameExtractor:
    """
    Experimental clause-local factual extractor.

    Hypothesis:
    semantic relations are more stable when detected inside local clauses
    using predicate/argument patterns, instead of using a document-wide set
    of co-occurring keywords.

    This candidate contains no benchmark labels or downstream decisions.
    """

    _FOLLOWUP_PATTERNS = (
        re.compile(
            r"\b(?:asked|requests?|requested|wants?|wanted|would like)\b"
            r".{0,80}\b(?:call|conversation|discussion|talk|speak|reconnect)\b"
        ),
        re.compile(
            r"\b(?:call|conversation|discussion|talk|speaking|reconnect(?:ion)?)\b"
            r".{0,40}\b(?:requested|asked|wanted|would like|resume|resumed)\b"
        ),
        re.compile(
            r"\bcircle\s+back\b"
        ),
    )

    _APPROVAL_PATTERNS = (
        re.compile(
            r"\b(?:budget|funding|spend|amount|proposed spend|bid)\b"
            r".{0,60}\b(?:approved|authorized|cleared|released|signed off)\b"
        ),
        re.compile(
            r"\b(?:approved|authorized|cleared|released|signed off)\b"
            r".{0,60}\b(?:budget|funding|spend|amount|bid|proposal)\b"
        ),
        re.compile(
            r"\b(?:authorization|approval|sign[- ]off|clearance)\b"
            r".{0,50}\b(?:granted|received|given)\b"
        ),
        re.compile(
            r"\b(?:funding|amount|spend|bid)\b"
            r".{0,60}\b(?:under the|within the)\b"
            r".{0,40}\bapproved budget\b"
        ),
    )

    _PROCUREMENT_PATTERNS = (
        re.compile(
            r"\b(?:procurement|purchasing|buying|sourcing)\b"
            r".{0,50}\b(?:started|begun|underway|proceeding|progressing|moving ahead|advancing)\b"
        ),
        re.compile(
            r"\b(?:procurement|purchasing|buying|sourcing)\b"
            r".{0,50}\b(?:opening|processing|moving|working)\b"
        ),
        re.compile(
            r"\b(?:order|intake)\b"
            r".{0,50}\b(?:opened|opening|started|begun)\b"
        ),
    )

    _REJECTION_PATTERNS = (
        re.compile(
            r"\b(?:does not work|doesn't work|does not meet|doesn't meet)\b"
            r".{0,80}\b(?:needs?|requirements?)\b"
        ),
        re.compile(
            r"\b(?:turned down|rejected|refused|declined|unacceptable)\b"
            r".{0,60}\b(?:deal|terms?|conditions?|arrangement|proposal|offer)\b"
        ),
        re.compile(
            r"\b(?:deal|terms?|conditions?|arrangement|proposal|offer)\b"
            r".{0,60}\b(?:rejected|refused|declined|unacceptable)\b"
        ),
        re.compile(
            r"\bunwilling\s+to\s+proceed\b"
        ),
        re.compile(
            r"\bwill\s+not\s+accept\b"
        ),
    )

    _COMPLETION_PATTERNS = (
        re.compile(
            r"\b(?:session|workshop|exercise|rollout|implementation|deployment|"
            r"migration|onboarding)\b"
            r".{0,50}\b(?:ended|finished|completed|concluded|is over|wrapped up|done)\b"
        ),
        re.compile(
            r"\b(?:ended|finished|completed|concluded|is over|wrapped up|done)\b"
            r".{0,50}\b(?:session|workshop|exercise|rollout|implementation|"
            r"deployment|migration|onboarding)\b"
        ),
    )

    _NEXT_STEP_PATTERNS = (
        re.compile(
            r"\b(?:asked|asks|asking|wants?|wanted|would like)\b"
            r".{0,80}\b(?:what|guidance|explain|explained|know)\b"
            r".{0,50}\b(?:next|following|subsequent|after)\b"
        ),
        re.compile(
            r"\b(?:what\s+comes\s+next|what\s+happens\s+next)\b"
        ),
        re.compile(
            r"\b(?:next|following|subsequent)\b"
            r".{0,50}\b(?:step|transition|transfer|handoff|handover)\b"
        ),
        re.compile(
            r"\b(?:handoff|handover|transfer|transition)\b"
            r".{0,50}\b(?:guidance|explain|explained|what)\b"
        ),
    )

    _SERVICE_WORDS = {
        "implementation",
        "deployment",
        "migration",
        "onboarding",
        "rollout",
        "session",
        "workshop",
        "exercise",
        "handoff",
        "handover",
        "transition",
        "transfer",
    }

    _PROPOSAL_WORDS = {
        "proposal",
        "offer",
        "quote",
        "quotation",
        "plan",
        "bid",
        "deal",
    }

    _COMMERCIAL_WORDS = {
        "terms",
        "conditions",
        "arrangement",
        "deal",
        "commercial",
    }

    _FOLLOWUP_TARGET_WORDS = {
        "call",
        "conversation",
        "discussion",
        "talk",
        "speak",
        "reconnect",
        "circle",
        "back",
    }

    _DIFFERENT_MARKERS = {
        "different",
        "separate",
        "another",
        "unrelated",
    }

    _IRRELEVANT_OBJECTS = {
        "branch",
        "site",
        "store",
        "deployment",
        "installation",
        "rollout",
        "location",
        "project",
        "initiative",
    }

    _NO_INFO_PATTERNS = (
        re.compile(r"\bnot\s+discussed\b"),
        re.compile(r"\bwas\s+not\s+discussed\b"),
        re.compile(r"\bwere\s+not\s+discussed\b"),
        re.compile(r"\bno\s+(?:information|update|details)\b"),
        re.compile(r"\bcontains?\s+no\s+(?:information|details)\b"),
        re.compile(r"\bhas\s+not\s+addressed\b"),
        re.compile(r"\bremained\s+untouched\b"),
    )

    def extract(
        self,
        *,
        content: str,
    ) -> EventFrameExtractionResult:
        normalized = self._normalize(content)
        clauses = self._split_clauses(normalized)

        frames: list[EventFrame] = []

        relevance = self._detect_relevance(
            normalized,
            clauses,
        )

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

        for clause in clauses:
            if self._is_followup_clause(clause.text):
                frames.append(
                    EventFrame(
                        actor="customer",
                        action="request",
                        object="followup_conversation",
                        state="requested",
                        polarity=FramePolarity.POSITIVE,
                        temporal_reference=self._temporal_reference(
                            clause.text,
                        ),
                        relevance=relevance,
                    )
                )

            if self._is_approval_clause(clause.text):
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

            if self._is_procurement_clause(clause.text):
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

            if self._is_rejection_clause(clause.text):
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

            if self._is_completion_clause(clause.text):
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

            if self._is_next_step_clause(clause.text):
                frames.append(
                    EventFrame(
                        actor="customer",
                        action="request",
                        object=self._next_step_object(clause.text),
                        state="next_step",
                        polarity=FramePolarity.POSITIVE,
                        temporal_reference="next_step",
                        relevance=relevance,
                    )
                )

        return EventFrameExtractionResult(
            frames=self._deduplicate(frames),
            normalized_text=normalized,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = text.strip().lower()
        normalized = normalized.replace("â€™", "'")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    @staticmethod
    def _split_clauses(text: str) -> tuple[LocalClause, ...]:
        parts = re.split(
            r"""
            [.;!?]+
            |
            \s+\band\b\s+
            |
            \s+\bwhile\b\s+
            |
            \s+\bbut\b\s+
            |
            \s+\bso\b\s+
            |
            \s+\bwith\b\s+
            """,
            text,
            flags=re.IGNORECASE | re.VERBOSE,
        )

        clauses = [
            part.strip(" ,")
            for part in parts
            if part.strip(" ,")
        ]

        return tuple(
            LocalClause(text=clause, index=index)
            for index, clause in enumerate(clauses)
        )

    @classmethod
    def _is_followup_clause(cls, clause: str) -> bool:
        if not any(
            word in clause
            for word in cls._FOLLOWUP_TARGET_WORDS
        ):
            return False

        return any(
            pattern.search(clause)
            for pattern in cls._FOLLOWUP_PATTERNS
        )

    @classmethod
    def _is_approval_clause(cls, clause: str) -> bool:
        return any(
            pattern.search(clause)
            for pattern in cls._APPROVAL_PATTERNS
        )

    @classmethod
    def _is_procurement_clause(cls, clause: str) -> bool:
        return any(
            pattern.search(clause)
            for pattern in cls._PROCUREMENT_PATTERNS
        )

    @classmethod
    def _is_rejection_clause(cls, clause: str) -> bool:
        return any(
            pattern.search(clause)
            for pattern in cls._REJECTION_PATTERNS
        )

    @classmethod
    def _is_completion_clause(cls, clause: str) -> bool:
        return any(
            pattern.search(clause)
            for pattern in cls._COMPLETION_PATTERNS
        )

    @classmethod
    def _is_next_step_clause(cls, clause: str) -> bool:
        return any(
            pattern.search(clause)
            for pattern in cls._NEXT_STEP_PATTERNS
        )

    @classmethod
    def _next_step_object(cls, clause: str) -> str:
        if re.search(
            r"\b(?:handoff|handover|transfer|transition)\b",
            clause,
        ):
            return "handoff"

        return "next_step"

    @classmethod
    def _detect_relevance(
        cls,
        normalized: str,
        clauses: tuple[LocalClause, ...],
    ) -> str | None:
        if not any(
            marker in normalized
            for marker in cls._DIFFERENT_MARKERS
        ):
            return None

        has_irrelevant_object = any(
            word in normalized
            for word in cls._IRRELEVANT_OBJECTS
        )

        has_no_information = any(
            pattern.search(normalized)
            for pattern in cls._NO_INFO_PATTERNS
        )

        if (
            has_irrelevant_object
            and (
                has_no_information
                or any(
                    marker in normalized
                    for marker in cls._DIFFERENT_MARKERS
                )
            )
        ):
            return "different_work_item"

        return None

    @staticmethod
    def _temporal_reference(
        clause: str,
    ) -> str | None:
        match = re.search(
            r"\b(?:after|before|on|by)\s+"
            r"([a-z0-9-]+(?:\s+[a-z0-9-]+){0,2})",
            clause,
        )

        if match:
            return match.group(0)

        return None

    @staticmethod
    def _deduplicate(
        frames: list[EventFrame],
    ) -> tuple[EventFrame, ...]:
        seen: set[EventFrame] = set()
        result: list[EventFrame] = []

        for frame in frames:
            if frame not in seen:
                seen.add(frame)
                result.append(frame)

        return tuple(result)