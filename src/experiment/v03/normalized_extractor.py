from __future__ import annotations

from dataclasses import dataclass
import re

from .evidence import (
    AssertionPolarity,
    EvidenceIdentity,
    EvidenceProvenance,
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)


@dataclass(frozen=True)
class NormalizedExtractionResult:
    evidence: SemanticEvidence
    normalized_text: str
    matched_concepts: tuple[str, ...]


class LexicalNormalizationSemanticExtractor:
    """
    Candidate v0.3 extractor.

    This is an experimental intermediate design between the original
    phrase-matching baseline and a future genuine semantic model.

    Pipeline:

        raw language
            -> lexical normalization
            -> factual semantic extraction
            -> SemanticEvidence

    Important:
        - No benchmark family IDs are used.
        - No expected transition is produced.
        - No supporting/contradictory role is emitted.
        - Provenance and identity remain separate from content semantics.
        - Negation is represented as factual polarity information.

    This should NOT be described as genuine semantic understanding.
    It is a dependency-free lexical-normalization experiment.
    """

    _CONCEPTS: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "followup",
            (
                r"\bfollow[- ]?up\b",
                r"\banother discussion\b",
                r"\banother conversation\b",
                r"\bfurther discussion\b",
                r"\bfurther conversation\b",
                r"\bnext discussion\b",
                r"\bnext conversation\b",
                r"\brequested another conversation\b",
                r"\bwants another conversation\b",
                r"\bwants another discussion\b",
                r"\bwould like another discussion\b",
                r"\bwants? to (?:arrange|schedule) .*discussion\b",
                r"\bwants? to (?:arrange|schedule) .*conversation\b",
                r"\bwants? to (?:speak|talk) .*again\b",
                r"\b(?:would like|would love) to (?:speak|talk) .*again\b",
                r"\bdiscuss(?:ed|ing)? .*again\b",
            ),
        ),
        (
            "approval",
            (
                r"\bapproved budget\b",
                r"\bbudget approval\b",
                r"\bfinancial approval\b",
                r"\bwithin (?:the )?approved budget\b",
                r"\bbudget has been authorized\b",
                r"\bfinancial authorization\b",
                r"\bfunding has been authorized\b",
                r"\bfunds? (?:has|have) been authorized\b",
                r"\bfunding for .* has been authorized\b",
                r"\b(?:budget|funding) (?:was|has been) approved\b",
                r"\b(?:amount|price|quote|quoted amount) .*approved\b",
            ),
        ),
        (
            "procurement",
            (
                r"\bprocurement\b",
                r"\bpurchasing process\b",
                r"\bpurchasing\b",
                r"\bprocurement process\b",
            ),
        ),
        (
            "rejection",
            (
                r"\bunacceptable\b",
                r"\brejected\b",
                r"\brejects\b",
                r"\bdo not work\b",
                r"\bdoes not work\b",
                r"\bdon't work\b",
                r"\bnot prepared to accept\b",
                r"\bunwilling to accept\b",
                r"\bwill not accept\b",
                r"\bwon't accept\b",
                r"\bnot willing to accept\b",
                r"\bneeds? to be reconsidered\b",
                r"\breconsider(?:ed|ation)\b",
                r"\breviewed again\b",
                r"\brevisit(?:ed)?\b",
            ),
        ),
        (
            "completion",
            (
                r"\bcompleted\b",
                r"\bcomplete\b",
                r"\bfinished\b",
                r"\bis finished\b",
                r"\bhas finished\b",
                r"\bhas been completed\b",
                r"\bwas completed\b",
                r"\bwas finished\b",
            ),
        ),
        (
            "next_step",
            (
                r"\bnext step\b",
                r"\bnext stage\b",
                r"\bfollowing handoff\b",
                r"\bsubsequent handoff\b",
                r"\bsubsequent transition\b",
                r"\bwhat happens (?:next|after(?:ward)?)\b",
                r"\bwhat should happen\b",
                r"\bwhat comes next\b",
                r"\bwhat comes after\b",
                r"\basks? .*next\b",
                r"\basks? .*what .*happens\b",
                r"\basks? .*what comes\b",
                r"\bwants? to know .*next\b",
                r"\bwants? to know .*what happens\b",
                r"\bwants? guidance .*next\b",
            ),
        ),
        (
            "proposal",
            (
                r"\bproposal\b",
                r"\boffer\b",
                r"\bquote\b",
                r"\bquoted amount\b",
                r"\bcommercial terms\b",
                r"\bproposed amount\b",
                r"\bproposed price\b",
            ),
        ),
        (
            "service",
            (
                r"\bservice\b",
                r"\bhandoff\b",
                r"\bmigration workshop\b",
                r"\bmigration session\b",
                r"\btransition\b",
                r"\brollout\b",
            ),
        ),
        (
            "irrelevant",
            (
                r"\bseparate\b",
                r"\bdifferent\b",
                r"\banother .*project\b",
                r"\bseparate .*project\b",
                r"\bunrelated\b",
                r"\bno (?:statement|information|update)\b",
                r"\bcontains no information\b",
                r"\bproviding no information\b",
                r"\bsays nothing about\b",
                r"\bno update on\b",
                r"\bwithout providing any update\b",
            ),
        ),
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
    ) -> NormalizedExtractionResult:
        normalized_text, concepts = self._normalize(content)

        negated_concepts = self._detect_negated_concepts(
            normalized_text,
            concepts,
        )

        polarity = (
            AssertionPolarity.NEGATIVE
            if negated_concepts and len(negated_concepts) == len(concepts)
            else AssertionPolarity.POSITIVE
        )

        semantics = self._build_semantics(
            normalized_text,
            concepts,
            negated_concepts,
            polarity,
        )

        evidence = SemanticEvidence(
            evidence_id=evidence_id,
            content=content,
            provenance=EvidenceProvenance(
                source_system=source_system,
                record_id=record_id,
                occurred_at=self._parse_timestamp(occurred_at),
            ),
            identity=EvidenceIdentity(
                customer_id=customer_id,
                quality=identity_quality,
            ),
            semantics=semantics,
        )

        return NormalizedExtractionResult(
            evidence=evidence,
            normalized_text=normalized_text,
            matched_concepts=tuple(concepts),
        )

    def _normalize(
        self,
        content: str,
    ) -> tuple[str, list[str]]:
        text = self._normalize_surface_form(content)
        lower = text.lower()

        concepts: list[str] = []

        for concept, patterns in self._CONCEPTS:
            if any(re.search(pattern, lower) for pattern in patterns):
                concepts.append(concept)

        return lower, concepts

    @staticmethod
    def _normalize_surface_form(text: str) -> str:
        """
        Apply only surface-level normalization.

        This intentionally avoids changing the underlying proposition.
        """
        normalized = text.strip().lower()

        normalized = normalized.replace("’", "'")
        normalized = normalized.replace("–", "-")
        normalized = normalized.replace("—", "-")

        normalized = re.sub(r"\s+", " ", normalized)

        return normalized

    @classmethod
    def _detect_negated_concepts(
        cls,
        normalized_text: str,
        concepts: list[str],
    ) -> list[str]:
        """
        Detect explicit local negation for concepts.

        This is intentionally narrow and clause-oriented. It is not
        intended to provide general natural-language negation parsing.
        """

        negated: list[str] = []

        patterns_by_concept: dict[str, tuple[str, ...]] = {
            "followup": (
                r"\bdo not want\b[^.?!;]*\b(?:discussion|conversation)\b",
                r"\bdoes not want\b[^.?!;]*\b(?:discussion|conversation)\b",
                r"\bdid not want\b[^.?!;]*\b(?:discussion|conversation)\b",
                r"\bdoesn't want\b[^.?!;]*\b(?:discussion|conversation)\b",
                r"\bdon't want\b[^.?!;]*\b(?:discussion|conversation)\b",
            ),
            "approval": (
                r"\bdo not have\b[^.?!;]*\bapproval\b",
                r"\bdoes not have\b[^.?!;]*\bapproval\b",
                r"\bdid not have\b[^.?!;]*\bapproval\b",
                r"\bdo not have\b[^.?!;]*\bapproved\b",
                r"\bdoes not have\b[^.?!;]*\bapproved\b",
            ),
            "completion": (
                r"\b(?:is|was|are|were)\s+not\s+complete\b",
                r"\b(?:is|was|are|were)\s+not\s+finished\b",
                r"\bhas\s+not\s+been\s+completed\b",
                r"\bhave\s+not\s+been\s+completed\b",
                r"\bhas\s+not\s+finished\b",
                r"\bhave\s+not\s+finished\b",
            ),
            "acceptance": (
                r"\bdo not accept\b",
                r"\bdoes not accept\b",
                r"\bdid not accept\b",
                r"\bdo not agree\b",
                r"\bdoes not agree\b",
            ),
        }

        for concept in concepts:
            patterns = patterns_by_concept.get(concept, ())

            if any(
                re.search(pattern, normalized_text)
                for pattern in patterns
            ):
                negated.append(concept)

        return negated

    def _build_semantics(
        self,
        normalized_text: str,
        concepts: list[str],
        negated_concepts: list[str],
        polarity: AssertionPolarity,
    ) -> EvidenceSemantics:
        concept_set = set(concepts)
        negated_set = set(negated_concepts)

        requests_followup = (
            True
            if "followup" in concept_set and "followup" not in negated_set
            else None
        )

        confirms_approval = (
            True
            if "approval" in concept_set and "approval" not in negated_set
            else None
        )

        expresses_rejection = (
            True
            if "rejection" in concept_set
            else None
        )

        confirms_completion = (
            True
            if "completion" in concept_set
            and "completion" not in negated_set
            else None
        )

        requests_next_step = (
            True
            if "next_step" in concept_set
            else None
        )

        expresses_acceptance = (
            True
            if (
                "approval" in concept_set
                and "approval" not in negated_set
            )
            else bool(
                re.search(
                    r"\baccepted?\b|\bacceptance\b|"
                    r"\bhas agreed\b|\bagreed to\b|"
                    r"\bis willing to proceed\b",
                    normalized_text,
                )
            )
        )

        if "acceptance" in negated_set:
            expresses_acceptance = None

        concerns_same_work_item: bool | None

        if "irrelevant" in concept_set:
            concerns_same_work_item = False
        else:
            concerns_same_work_item = None

        topic: str | None = None

        if "proposal" in concept_set:
            topic = "proposal"
        elif "service" in concept_set:
            topic = "service"
        elif "procurement" in concept_set:
            topic = "procurement"

        return EvidenceSemantics(
            topic=topic,
            polarity=polarity,
            negated_concepts=tuple(negated_concepts),
            requests_followup=requests_followup,
            expresses_acceptance=expresses_acceptance,
            expresses_rejection=expresses_rejection,
            confirms_approval=confirms_approval,
            confirms_completion=confirms_completion,
            requests_next_step=requests_next_step,
            concerns_same_work_item=concerns_same_work_item,
        )

    @staticmethod
    def _parse_timestamp(value: str | None):
        if value is None:
            return None

        from datetime import datetime

        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)