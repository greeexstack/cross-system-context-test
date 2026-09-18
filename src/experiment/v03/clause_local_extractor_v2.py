from __future__ import annotations

import re

from .clause_local_extractor import (
    ClauseLocalEventFrameExtractor,
)


class ClauseLocalRelationalEventFrameExtractor(
    ClauseLocalEventFrameExtractor
):
    """
    v2 clause-local extractor.

    Mechanism change from v1:
    - v1 mostly recognizes fixed predicate patterns.
    - v2 explicitly models local semantic relations:
        financial subject -> approval event
        commercial subject -> incompatibility/rejection event
        modifier -> separate work item
        request predicate -> question/handoff complement

    The extractor still produces factual EventFrame objects and contains
    no benchmark labels or downstream decisions.
    """

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

    _FINANCIAL_SUBJECTS = {
        "budget",
        "funding",
        "spend",
        "amount",
        "bid",
        "quote",
        "quotation",
        "proposal",
    }

    _APPROVAL_RELATIONS = (
        re.compile(
            r"\b(?:budget|funding|spend|amount|bid|quote|quotation|proposal)\b"
            r".{0,80}"
            r"\b(?:approved|authorized|cleared|released|sanctioned)\b"
        ),
        re.compile(
            r"\b(?:budget|funding|spend|amount|bid|quote|quotation|proposal)\b"
            r".{0,80}"
            r"\b(?:received|got|was given|has received|received)\b"
            r".{0,25}"
            r"\b(?:approval|authorization|clearance|sign[- ]?off|signoff)\b"
        ),
        re.compile(
            r"\b(?:approval|authorization|clearance|sign[- ]?off|signoff)\b"
            r".{0,50}"
            r"\b(?:granted|received|given|completed)\b"
        ),
        re.compile(
            r"\b(?:amount|funding|spend|bid|quote)\b"
            r".{0,70}"
            r"\b(?:within|under|covered by)\b"
            r".{0,30}"
            r"\bapproved\b"
        ),
    )

    _INCOMPATIBILITY_RELATIONS = (
        re.compile(
            r"\b(?:terms?|conditions?|arrangement|deal|proposal|offer)\b"
            r".{0,60}"
            r"\b(?:do not|does not|don't|doesn't)\s+work\b"
        ),
        re.compile(
            r"\b(?:terms?|conditions?|arrangement|deal|proposal|offer)\b"
            r".{0,80}"
            r"\b(?:falls?|fall)\s+short\b"
        ),
        re.compile(
            r"\b(?:terms?|conditions?|arrangement|deal|proposal|offer)\b"
            r".{0,80}"
            r"\b(?:unacceptable|rejected|refused|declined|turned down)\b"
        ),
        re.compile(
            r"\b(?:customer|client|buyer|purchaser)\b"
            r".{0,50}"
            r"\b(?:declines?|rejects?|refuses?|rejecting|refusing)\b"
            r".{0,50}"
            r"\b(?:terms?|conditions?|deal|arrangement|proposal|offer)\b"
        ),
        re.compile(
            r"\bunwilling\s+to\s+proceed\b"
        ),
        re.compile(
            r"\bwill\s+not\s+accept\b"
        ),
                re.compile(
            r"\b(?:customer|client|buyer|purchaser)\b"
            r".{0,40}"
            r"\b(?:turned down|rejected|refused|declined)\b"
            r".{0,60}"
            r"\b(?:terms?|conditions?|deal|arrangement|proposal|offer)\b"
        ),
    )

    _REQUEST_QUESTION_RELATIONS = (
        re.compile(
            r"\b(?:asks?|asked|asking|requests?|requested|wants?|wanted)"
            r"\b"
            r".{0,90}"
            r"\b(?:what|how|guidance|explain|know)\b"
            r".{0,70}"
            r"\b(?:handoff|handover|transfer|transition|next|following|subsequent)\b"
        ),
        re.compile(
            r"\b(?:asks?|asked|asking|requests?|requested|wants?|wanted)"
            r"\b"
            r".{0,100}"
            r"\b(?:handoff|handover|transfer|transition)\b"
        ),
        re.compile(
            r"\b(?:what|how)\b"
            r".{0,70}"
            r"\b(?:handoff|handover|transfer|transition)\b"
            r".{0,60}"
            r"\b(?:would|will|should|does)\b"
        ),
    )

    _SEPARATE_WORK_ITEM_RELATIONS = (
        re.compile(
            r"\b(?:different|separate|another|unrelated)\b"
            r".{0,40}"
            r"\b(?:branch|site|store|deployment|installation|rollout|"
            r"location|project|initiative|launch|exercise)\b"
        ),
        re.compile(
            r"\b(?:different|separate|another|unrelated)\b"
            r".{0,80}"
            r"\b(?:work|effort|activity|operation)\b"
        ),
    )

    @classmethod
    def _is_approval_clause(
        cls,
        clause: str,
    ) -> bool:
        return any(
            pattern.search(clause)
            for pattern in cls._APPROVAL_RELATIONS
        )

    @classmethod
    def _is_rejection_clause(
        cls,
        clause: str,
    ) -> bool:
        return any(
            pattern.search(clause)
            for pattern in cls._INCOMPATIBILITY_RELATIONS
        )

    @classmethod
    def _is_next_step_clause(
        cls,
        clause: str,
    ) -> bool:
        return any(
            pattern.search(clause)
            for pattern in cls._REQUEST_QUESTION_RELATIONS
        )

    @classmethod
    def _detect_relevance(
        cls,
        normalized: str,
        clauses,
    ) -> str | None:
        if not any(
            marker in normalized
            for marker in cls._DIFFERENT_MARKERS
        ):
            return None

        if any(
            pattern.search(normalized)
            for pattern in cls._SEPARATE_WORK_ITEM_RELATIONS
        ):
            return "different_work_item"

        if any(
            pattern.search(normalized)
            for pattern in cls._NO_INFO_PATTERNS
        ):
            if any(
                word in normalized
                for word in cls._WORK_ITEM_OBJECTS
            ):
                return "different_work_item"

        return None