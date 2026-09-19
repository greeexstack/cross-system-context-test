from __future__ import annotations



from .event_frames import (
    EventFrame,
    EventFrameExtractionResult,
    FramePolarity,
)


class SpacyDependencyEventFrameExtractor:
    """
    Experimental dependency-based factual extractor.

    Mechanism:
        text -> dependency parse -> local predicate/argument relations
             -> factual event frames

    This deliberately does not reuse the clause-local regex rules.
    Lexical sets provide semantic categories, while dependency structure
    determines how those categories are related.
    """

    _FOLLOWUP_PREDICATES = {
        "ask",
        "request",
        "want",
        "wish",
        "prefer",
        "indicate",
        "welcome",
        "express",
        "signal",
        "suggest",
        "propose",
        "recommend",
        "reconnect",
        "continue",
        "resume",
    }

    _FOLLOWUP_TARGETS = {
        "conversation",
        "discussion",
        "call",
        "meeting",
        "talk",
        "speak",
        "reconnect",
        "catch",
        "chat",
    }

    _APPROVAL_PREDICATES = {
        "approve",
        "authorize",
        "sanction",
        "clear",
        "release",
        "approve",
    }

    _APPROVAL_NOUNS = {
        "approval",
        "authorization",
        "clearance",
        "signoff",
        "sign-off",
    }

    _FINANCIAL_OBJECTS = {
        "budget",
        "funding",
        "spend",
        "amount",
        "bid",
        "quote",
        "quotation",
        "sum",
        "expenditure",
        "purchase",
        "allocation",
        "package",
        "proposal",
    }

    _PROCUREMENT_SUBJECTS = {
        "procurement",
        "purchasing",
        "purchase",
        "buying",
        "source",
        "sourcing",
    }

    _PROCUREMENT_PROGRESS = {
        "start",
        "begin",
        "open",
        "proceed",
        "progress",
        "advance",
        "move",
        "underway",
        "continue",
    }

    _REJECTION_PREDICATES = {
        "reject",
        "decline",
        "refuse",
        "turn",
        "work",
        "fall",
    }

    _COMMERCIAL_OBJECTS = {
        "term",
        "terms",
        "condition",
        "conditions",
        "arrangement",
        "deal",
        "proposal",
        "offer",
    }

    _COMPLETION_PREDICATES = {
        "complete",
        "finish",
        "conclude",
        "end",
        "wrap",
        "done",
    }

    _SERVICE_OBJECTS = {
        "service",
        "implementation",
        "deployment",
        "migration",
        "onboarding",
        "rollout",
        "session",
        "workshop",
        "exercise",
        "clinic",
    }

    _NEXT_STEP_TARGETS = {
        "next",
        "following",
        "subsequent",
        "handoff",
        "handover",
        "transfer",
        "transition",
    }

    _REQUEST_PREDICATES = {
        "ask",
        "request",
        "want",
        "wish",
        "prefer",
        "seek",
        "need",
    }

    _WORK_ITEM_OBJECTS = {
        "branch",
        "site",
        "store",
        "deployment",
        "installation",
        "rollout",
        "location",
        "project",
        "initiative",
        "launch",
        "exercise",
    }

    _SEPARATION_MARKERS = {
        "different",
        "separate",
        "another",
        "unrelated",
    }

    def __init__(self) -> None:
        try:
            import spacy
        except ImportError as exc:
            raise RuntimeError(
                "spaCy is required for the optional NLP experiment. "
                "Install the project extra with: "
                "python -m pip install -e .[nlp-experiment]"
            ) from exc

        if not spacy.util.is_package("en_core_web_sm"):
            raise RuntimeError(
                "spaCy English model 'en_core_web_sm' is required for "
                "the optional NLP experiment. Run: "
                "python -m spacy download en_core_web_sm"
            )

        self._nlp = spacy.load("en_core_web_sm")
    def extract(
        self,
        *,
        content: str,
    ) -> EventFrameExtractionResult:
        normalized = self._normalize(content)
        doc = self._nlp(normalized)

        frames: list[EventFrame] = []

        relevance = self._detect_relevance(doc)

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
                frames=(frames[0],),
                normalized_text=normalized,
            )

        for token in doc:
            lemma = token.lemma_.lower()

            if self._is_followup_relation(token, doc):
                frames.append(
                    EventFrame(
                        actor="customer",
                        action="request",
                        object="followup_conversation",
                        state="requested",
                        polarity=FramePolarity.POSITIVE,
                        temporal_reference=self._temporal_reference(
                            token,
                            doc,
                        ),
                    )
                )

            if self._is_approval_relation(token, doc):
                frames.append(
                    EventFrame(
                        actor="customer",
                        action="confirm",
                        object="quote",
                        state="budget_approved",
                        polarity=FramePolarity.POSITIVE,
                    )
                )

            if self._is_procurement_relation(token, doc):
                frames.append(
                    EventFrame(
                        actor="customer",
                        action="report",
                        object="procurement",
                        state="progressing",
                        polarity=FramePolarity.POSITIVE,
                    )
                )

            if self._is_rejection_relation(token, doc):
                frames.append(
                    EventFrame(
                        actor="customer",
                        action="accept",
                        object="commercial_terms",
                        state="rejected",
                        polarity=FramePolarity.NEGATIVE,
                    )
                )

            if self._is_completion_relation(token, doc):
                frames.append(
                    EventFrame(
                        actor="customer",
                        action="confirm",
                        object="service",
                        state="completed",
                        polarity=FramePolarity.POSITIVE,
                    )
                )

            if self._is_next_step_relation(token, doc):
                frames.append(
                    EventFrame(
                        actor="customer",
                        action="request",
                        object=self._next_step_object(doc),
                        state="next_step",
                        polarity=FramePolarity.POSITIVE,
                        temporal_reference="next_step",
                    )
                )

        return EventFrameExtractionResult(
            frames=self._deduplicate(frames),
            normalized_text=normalized,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.strip().lower().split())

    @classmethod
    def _subtree_lemmas(cls, token) -> set[str]:
        return {
            child.lemma_.lower()
            for child in token.subtree
        }

    @classmethod
    def _subtree_text(cls, token) -> str:
        return " ".join(
            child.text.lower()
            for child in token.subtree
        )

    @classmethod
    def _has_subject(cls, token) -> bool:
        return any(
            child.dep_ in {"nsubj", "nsubjpass"}
            for child in token.children
        )

    @classmethod
    def _is_followup_relation(
        cls,
        token,
        doc,
    ) -> bool:
        if token.lemma_.lower() not in cls._FOLLOWUP_PREDICATES:
            return False

        subtree = cls._subtree_lemmas(token)

        if not subtree.intersection(cls._FOLLOWUP_TARGETS):
            return False

        return (
            cls._has_subject(token)
            or token.dep_ in {"xcomp", "ccomp", "conj", "relcl"}
        )

    @classmethod
    def _is_approval_relation(
        cls,
        token,
        doc,
    ) -> bool:
        lemma = token.lemma_.lower()
        subtree = cls._subtree_lemmas(token)

        if lemma in cls._APPROVAL_PREDICATES:
            return bool(
                subtree.intersection(
                    cls._FINANCIAL_OBJECTS
                )
            )

        if lemma in {
            "issue",
            "receive",
            "get",
            "obtain",
        }:
            return bool(
                subtree.intersection(
                    cls._APPROVAL_NOUNS
                )
                and subtree.intersection(
                    cls._FINANCIAL_OBJECTS
                )
            )

        return False

    @classmethod
    def _is_procurement_relation(
        cls,
        token,
        doc,
    ) -> bool:
        lemma = token.lemma_.lower()

        if lemma not in cls._PROCUREMENT_PROGRESS:
            return False

        subtree = cls._subtree_lemmas(token)

        return bool(
            subtree.intersection(
                cls._PROCUREMENT_SUBJECTS
            )
        )

    @classmethod
    def _is_rejection_relation(
        cls,
        token,
        doc,
    ) -> bool:
        lemma = token.lemma_.lower()
        subtree = cls._subtree_lemmas(token)
        text = cls._subtree_text(token)

        if lemma in {
            "reject",
            "decline",
            "refuse",
        }:
            return bool(
                subtree.intersection(
                    cls._COMMERCIAL_OBJECTS
                )
            )

        if lemma == "turn":
            return (
                "down" in text
                and bool(
                    subtree.intersection(
                        cls._COMMERCIAL_OBJECTS
                    )
                )
            )

        if lemma == "work":
            subject_objects = {
                child.lemma_.lower()
                for child in token.children
                if child.dep_ in {"nsubj", "nsubjpass"}
            }

            negated = any(
                child.dep_ == "neg"
                for child in token.children
            )

            return (
                negated
                and bool(
                    subject_objects.intersection(
                        cls._COMMERCIAL_OBJECTS
                    )
                )
            )

        if lemma == "fall":
            return (
                "short" in subtree
                and bool(
                    subtree.intersection(
                        cls._COMMERCIAL_OBJECTS
                    )
                )
            )

        return False

    @classmethod
    def _is_completion_relation(
        cls,
        token,
        doc,
    ) -> bool:
        lemma = token.lemma_.lower()

        if lemma not in cls._COMPLETION_PREDICATES:
            return False

        subtree = cls._subtree_lemmas(token)

        return bool(
            subtree.intersection(
                cls._SERVICE_OBJECTS
            )
        )

    @classmethod
    def _is_next_step_relation(
        cls,
        token,
        doc,
    ) -> bool:
        lemma = token.lemma_.lower()

        if lemma not in cls._REQUEST_PREDICATES:
            return False

        subtree = cls._subtree_lemmas(token)

        return bool(
            subtree.intersection(
                cls._NEXT_STEP_TARGETS
            )
        )

    @classmethod
    def _detect_relevance(
        cls,
        doc,
    ) -> str | None:
        for token in doc:
            if token.lemma_.lower() not in cls._WORK_ITEM_OBJECTS:
                continue

            path_tokens = set(
                child.lemma_.lower()
                for child in token.subtree
            )

            head_path = {
                ancestor.lemma_.lower()
                for ancestor in token.ancestors
            }

            combined = path_tokens | head_path

            if combined.intersection(
                cls._SEPARATION_MARKERS
            ):
                return "different_work_item"

        return None

    @classmethod
    def _temporal_reference(
        cls,
        token,
        doc,
    ) -> str | None:
        subtree_text = cls._subtree_text(token)

        for marker in (
            "thursday",
            "week",
            "later",
            "next",
            "tomorrow",
        ):
            if marker in subtree_text:
                return marker

        return None

    @classmethod
    def _next_step_object(
        cls,
        doc,
    ) -> str:
        lemmas = {
            token.lemma_.lower()
            for token in doc
        }

        if lemmas.intersection(
            {
                "handoff",
                "handover",
                "transfer",
                "transition",
            }
        ):
            return "handoff"

        return "next_step"

    @staticmethod
    def _deduplicate(
        frames: list[EventFrame],
    ) -> tuple[EventFrame, ...]:
        result: list[EventFrame] = []
        seen: set[EventFrame] = set()

        for frame in frames:
            if frame in seen:
                continue

            seen.add(frame)
            result.append(frame)

        return tuple(result)