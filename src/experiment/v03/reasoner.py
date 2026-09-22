from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .evidence import (
    AssertionPolarity,
    EvidenceCondition,
    EvidenceProvenance,
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)


@dataclass(frozen=True)
class PrimaryState:
    """
    Structured primary interpretation supplied to the v0.3 reasoner.
    """

    interpretation_class: str
    decision_strength: str = "moderate"


@dataclass(frozen=True)
class TransitionResult:
    interpretation_class: str
    support_level: str
    decision_strength: str
    recommended_focus: str | None = None


@dataclass(frozen=True)
class ReasonerConfig:
    """
    Temporal policy for the v0.3 reasoning layer.
    """

    evaluation_at: datetime
    stale_after_days: int = 30

    def __post_init__(self) -> None:
        if self.evaluation_at.tzinfo is None:
            raise ValueError("evaluation_at must be timezone-aware")

        if self.stale_after_days < 0:
            raise ValueError("stale_after_days must be non-negative")


@dataclass(frozen=True)
class _ComposedEvidence:
    """
    Internal representation of a cross-record composition result.

    This is deliberately not part of the public TransitionResult.

    The composed semantic record retains the exact contributing evidence
    identifiers and provenance so that composition does not erase the
    evidence boundary that produced the resulting facts.
    """

    semantics: EvidenceSemantics
    source_evidence_ids: tuple[str, ...]
    source_provenance: tuple[EvidenceProvenance, ...]


_COMPOSABLE_FIELDS: tuple[tuple[str, str], ...] = (
    ("requests_followup", "followup"),
    ("expresses_acceptance", "acceptance"),
    ("expresses_rejection", "rejection"),
    ("confirms_approval", "approval"),
    ("confirms_completion", "completion"),
    ("requests_next_step", "next_step"),
)


class V03Reasoner:
    """
    Minimal evidence-transition reasoner.

    The reasoner consumes factual semantic attributes plus provenance.
    It does not consume benchmark expectations or family IDs.

    H6 cross-record composition is deliberately narrow:

      1. identity must already be confirmed;
      2. evidence must already be temporally valid;
      3. records must explicitly state that they concern the same
         work item;
      4. the factual assertions must not contain an unresolved
         positive/negative conflict;
      5. source evidence IDs and provenance are retained internally.

    Records that do not satisfy those conditions remain independently
    reasoned rather than being silently merged.
    """

    def __init__(self, config: ReasonerConfig | None = None) -> None:
        self.config = config or ReasonerConfig(
            evaluation_at=datetime.now(timezone.utc)
        )

    def evaluate(
        self,
        primary: PrimaryState,
        secondary: EvidenceCondition,
    ) -> TransitionResult:
        if secondary.is_unavailable():
            return TransitionResult(
                interpretation_class=primary.interpretation_class,
                support_level="safe_fallback_primary_only",
                decision_strength=primary.decision_strength,
            )

        if not secondary.has_evidence():
            return TransitionResult(
                interpretation_class=primary.interpretation_class,
                support_level="no_secondary_evidence",
                decision_strength=primary.decision_strength,
            )

        valid_identity_items = [
            item
            for item in secondary.items
            if item.identity.quality == IdentityQuality.CONFIRMED
        ]

        if not valid_identity_items:
            return TransitionResult(
                interpretation_class=primary.interpretation_class,
                support_level="primary_only",
                decision_strength=primary.decision_strength,
            )

        fresh_items = [
            item
            for item in valid_identity_items
            if self._is_fresh(item.timestamp)
        ]

        if not fresh_items:
            return TransitionResult(
                interpretation_class=primary.interpretation_class,
                support_level="temporal_context_rejected",
                decision_strength=primary.decision_strength,
            )

        relevant_items = [
            item
            for item in fresh_items
            if item.semantics.concerns_same_work_item is not False
        ]

        if not relevant_items:
            return TransitionResult(
                interpretation_class=primary.interpretation_class,
                support_level="primary_only",
                decision_strength=primary.decision_strength,
            )

        composed = self._compose_cross_record_evidence(
            tuple(relevant_items)
        )

        if composed is not None:
            composed_ids = set(composed.source_evidence_ids)

            # Preserve the independent contribution of relevant records
            # that were not eligible for H6 composition.
            remaining_semantics = [
                item.semantics
                for item in relevant_items
                if item.evidence_id not in composed_ids
            ]

            return self._apply_evidence(
                primary,
                [composed.semantics, *remaining_semantics],
            )

        return self._apply_evidence(
            primary,
            [item.semantics for item in relevant_items],
        )

    def _compose_cross_record_evidence(
        self,
        items: tuple[SemanticEvidence, ...],
    ) -> _ComposedEvidence | None:
        """
        Compose only the subset explicitly proven eligible for H6.

        Eligibility at this point assumes identity and freshness have
        already been filtered by evaluate(). The remaining H6 gate is
        explicit same-work-item evidence plus conflict containment.

        Returning None means that composition is not established as safe
        for this input, so the caller must preserve independent reasoning.
        """

        composable_items = tuple(
            item
            for item in items
            if (
                item.identity.quality == IdentityQuality.CONFIRMED
                and item.semantics.concerns_same_work_item is True
            )
        )

        # Cross-record composition requires at least two eligible records.
        if len(composable_items) < 2:
            return None

        if self._has_unresolved_polarity_conflict(
            composable_items
        ):
            return None

        negated_concepts = tuple(
            sorted(
                {
                    self._canonical_concept(concept)
                    for item in composable_items
                    for concept in item.semantics.negated_concepts
                }
            )
        )

        composed_fields: dict[str, bool | None] = {}

        for field_name, _concept in _COMPOSABLE_FIELDS:
            has_positive_fact = any(
                getattr(item.semantics, field_name) is True
                for item in composable_items
            )

            composed_fields[field_name] = (
                True if has_positive_fact else None
            )

        topics = tuple(
            item.semantics.topic
            for item in composable_items
            if item.semantics.topic is not None
        )

        if topics and len(set(topics)) == 1:
            topic = topics[0]
        else:
            topic = None

        polarities = {
            item.semantics.polarity
            for item in composable_items
        }

        if len(polarities) == 1:
            polarity = next(iter(polarities))
        else:
            polarity = AssertionPolarity.UNKNOWN

        semantics = EvidenceSemantics(
            topic=topic,
            polarity=polarity,
            negated_concepts=negated_concepts,
            requests_followup=composed_fields["requests_followup"],
            expresses_acceptance=composed_fields["expresses_acceptance"],
            expresses_rejection=composed_fields["expresses_rejection"],
            confirms_approval=composed_fields["confirms_approval"],
            confirms_completion=composed_fields["confirms_completion"],
            requests_next_step=composed_fields["requests_next_step"],
            concerns_same_work_item=True,
        )

        return _ComposedEvidence(
            semantics=semantics,
            source_evidence_ids=tuple(
                item.evidence_id
                for item in composable_items
            ),
            source_provenance=tuple(
                item.provenance
                for item in composable_items
            ),
        )

    @classmethod
    def _has_unresolved_polarity_conflict(
        cls,
        items: tuple[SemanticEvidence, ...],
    ) -> bool:
        positive_concepts: set[str] = set()
        negated_concepts: set[str] = set()

        has_acceptance = False
        has_rejection = False

        for item in items:
            semantics = item.semantics

            if semantics.expresses_acceptance is True:
                has_acceptance = True

            if semantics.expresses_rejection is True:
                has_rejection = True

            for field_name, concept in _COMPOSABLE_FIELDS:
                if getattr(semantics, field_name) is True:
                    positive_concepts.add(concept)

            for concept in semantics.negated_concepts:
                negated_concepts.add(
                    cls._canonical_concept(concept)
                )

        # Acceptance and rejection are incompatible factual assertions
        # for the same composition candidate. Treat the combination as
        # unresolved rather than allowing naïve positive-field merging.
        if has_acceptance and has_rejection:
            return True

        # Explicit semantic negation conflicts with a positive assertion
        # of the same concept.
        return bool(
            positive_concepts.intersection(negated_concepts)
        )

    @staticmethod
    def _canonical_concept(concept: str) -> str:
        """
        Normalize minor lexical variations in negated concept names.

        This does not perform semantic extraction. It only makes the
        already-established semantic field vocabulary comparable.
        """

        normalized = concept.strip().lower()
        normalized = normalized.replace("-", "_")
        normalized = " ".join(normalized.split())
        normalized = normalized.replace(" ", "_")

        aliases = {
            "follow_up": "followup",
            "nextstep": "next_step",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    def _apply_evidence(
        self,
        primary: PrimaryState,
        semantics: list[EvidenceSemantics],
    ) -> TransitionResult:
        has_rejection = any(
            item.expresses_rejection is True
            for item in semantics
        )

        has_acceptance = any(
            item.expresses_acceptance is True
            for item in semantics
        )

        has_approval = any(
            item.confirms_approval is True
            for item in semantics
        )

        has_followup = any(
            item.requests_followup is True
            for item in semantics
        )

        has_completion_and_next_step = any(
            item.confirms_completion is True
            and item.requests_next_step is True
            for item in semantics
        )

        if has_rejection:
            return TransitionResult(
                interpretation_class=primary.interpretation_class,
                support_level="weakened_by_secondary_context",
                decision_strength="weaker",
            )

        if has_completion_and_next_step:
            return TransitionResult(
                interpretation_class=primary.interpretation_class,
                support_level="supported_by_secondary_context",
                decision_strength=primary.decision_strength,
                recommended_focus="next_step_followup",
            )

        if has_approval or has_acceptance:
            return TransitionResult(
                interpretation_class=primary.interpretation_class,
                support_level="secondary_supported",
                decision_strength="stronger",
            )

        if has_followup:
            if primary.interpretation_class == "quote_pending_decision":
                return TransitionResult(
                    interpretation_class="quote_followup_pending",
                    support_level="supported_by_secondary_context",
                    decision_strength=primary.decision_strength,
                )

            return TransitionResult(
                interpretation_class=primary.interpretation_class,
                support_level="secondary_supported",
                decision_strength="stronger",
            )

        return TransitionResult(
            interpretation_class=primary.interpretation_class,
            support_level="primary_only",
            decision_strength=primary.decision_strength,
        )

    def _is_fresh(self, timestamp: datetime | None) -> bool:
        if timestamp is None:
            return False

        when = timestamp

        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)

        age = self.config.evaluation_at - when

        return age <= timedelta(days=self.config.stale_after_days)