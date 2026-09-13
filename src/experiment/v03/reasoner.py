from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .evidence import (
    EvidenceCondition,
    EvidenceSemantics,
    IdentityQuality,
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


class V03Reasoner:
    """
    Minimal evidence-transition reasoner.

    The reasoner consumes factual semantic attributes plus provenance.
    It does not consume benchmark expectations or family IDs.
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

        return self._apply_evidence(
            primary,
            [item.semantics for item in relevant_items],
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