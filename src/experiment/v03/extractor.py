from __future__ import annotations

from dataclasses import dataclass
import re

from .evidence import (
    EvidenceIdentity,
    EvidenceProvenance,
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)


@dataclass(frozen=True)
class ExtractionResult:
    evidence: SemanticEvidence
    matched_patterns: tuple[str, ...]


class RuleBasedSemanticExtractor:
    """
    Experimental semantic extractor for v0.3.

    This is deliberately a baseline, not the final architecture.

    The extractor converts natural-language observations into factual
    semantic attributes. It must never emit the benchmark's expected
    interpretation or expected state transition.
    """

    _FOLLOWUP_PATTERNS = (
        r"\bfollow[- ]?up\b",
        r"\bnext (?:discussion|conversation|call|meeting)\b",
        r"\bdiscuss(?:ion)? (?:it|this) again\b",
        r"\banother discussion\b",
        r"\bfurther discussion\b",
    )

    _APPROVAL_PATTERNS = (
        r"\bapproved budget\b",
        r"\bbudget approval\b",
        r"\bfinancial approval\b",
        r"\bwithin (?:the )?approved budget\b",
    )

    _PROCUREMENT_PATTERNS = (
        r"\bprocurement\b",
        r"\bpurchasing process\b",
    )

    _REJECTION_PATTERNS = (
        r"\bdo not work\b",
        r"\bdoes not work\b",
        r"\bdon't work\b",
        r"\bunacceptable\b",
        r"\brejected\b",
        r"\bnot prepared to accept\b",
        r"\breconsider(?:ed|ation)\b",
        r"\breviewed again\b",
    )

    _COMPLETION_PATTERNS = (
        r"\bcompleted\b",
        r"\bcomplete\b",
        r"\bfinished\b",
        r"\bis finished\b",
    )

    _NEXT_STEP_PATTERNS = (
        r"\bnext step\b",
        r"\bnext stage\b",
        r"\bfollowing handoff\b",
        r"\bwhat happens (?:next|after(?:ward)?)\b",
        r"\bwhat should happen\b",
    )

    _PROPOSAL_PATTERNS = (
        r"\bproposal\b",
        r"\bquote\b",
        r"\bquoted amount\b",
        r"\bcommercial terms\b",
    )

    _SERVICE_PATTERNS = (
        r"\bservice\b",
        r"\bhandoff\b",
        r"\bmigration workshop\b",
        r"\btransition\b",
    )

    _IRRELEVANCE_PATTERNS = (
        r"\bseparate\b",
        r"\bdifferent\b",
        r"\banother\b",
        r"\bno (?:statement|information|update)\b",
        r"\bunrelated\b",
    )

    def extract(
        self,
        *,
        evidence_id: str,
        content: str,
        source_system: str,
        record_id: str,
        occurred_at: str | None,
        customer_id: str | None,
        identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    ) -> ExtractionResult:
        semantics, matched = self._extract_semantics(content)

        timestamp = self._parse_timestamp(occurred_at)

        evidence = SemanticEvidence(
            evidence_id=evidence_id,
            content=content,
            provenance=EvidenceProvenance(
                source_system=source_system,
                record_id=record_id,
                occurred_at=timestamp,
            ),
            identity=EvidenceIdentity(
                customer_id=customer_id,
                quality=identity_quality,
            ),
            semantics=semantics,
        )

        return ExtractionResult(
            evidence=evidence,
            matched_patterns=tuple(matched),
        )

    def _extract_semantics(
        self,
        content: str,
    ) -> tuple[EvidenceSemantics, list[str]]:
        text = content.strip()
        lower = text.lower()
        matched: list[str] = []

        def matches(
            patterns: tuple[str, ...],
            label: str,
        ) -> bool:
            found = any(re.search(pattern, lower) for pattern in patterns)
            if found:
                matched.append(label)
            return found

        requests_followup = matches(
            self._FOLLOWUP_PATTERNS,
            "requests_followup",
        )

        confirms_approval = matches(
            self._APPROVAL_PATTERNS,
            "confirms_approval",
        )

        procurement_mentioned = matches(
            self._PROCUREMENT_PATTERNS,
            "procurement",
        )

        expresses_rejection = matches(
            self._REJECTION_PATTERNS,
            "expresses_rejection",
        )

        confirms_completion = matches(
            self._COMPLETION_PATTERNS,
            "confirms_completion",
        )

        requests_next_step = matches(
            self._NEXT_STEP_PATTERNS,
            "requests_next_step",
        )

        proposal_mentioned = matches(
            self._PROPOSAL_PATTERNS,
            "proposal_or_quote",
        )

        service_mentioned = matches(
            self._SERVICE_PATTERNS,
            "service",
        )

        possible_irrelevance = matches(
            self._IRRELEVANCE_PATTERNS,
            "possible_irrelevance",
        )

        expresses_acceptance = (
            confirms_approval
            or bool(re.search(r"\baccepted?\b|\bacceptance\b", lower))
        )

        if expresses_acceptance:
            matched.append("expresses_acceptance")

        if (
            possible_irrelevance
            and (
                "separate" in lower
                or "different" in lower
                or "unrelated" in lower
            )
        ):
            concerns_same_work_item = False
        else:
            concerns_same_work_item = None

        topic = None

        if proposal_mentioned:
            topic = "proposal"
        elif service_mentioned:
            topic = "service"
        elif procurement_mentioned:
            topic = "procurement"

        semantics = EvidenceSemantics(
            topic=topic,
            requests_followup=requests_followup,
            expresses_acceptance=expresses_acceptance,
            expresses_rejection=expresses_rejection,
            confirms_approval=confirms_approval,
            confirms_completion=confirms_completion,
            requests_next_step=requests_next_step,
            concerns_same_work_item=concerns_same_work_item,
        )

        return semantics, matched

    @staticmethod
    def _parse_timestamp(value: str | None):
        if value is None:
            return None

        from datetime import datetime

        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)