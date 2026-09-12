from dataclasses import dataclass
from datetime import datetime, timedelta

from experiment.domain.models import Opportunity


@dataclass(frozen=True)
class QuoteFollowupBaseline:
    attention_after_days: int = 7


@dataclass(frozen=True)
class BaselineResult:
    opportunity_id: str
    elapsed: timedelta | None
    attention_threshold: timedelta
    crossed: bool
    applicable: bool
    reason: str


class QuoteFollowupBaselineEvaluator:
    def __init__(
        self,
        baseline: QuoteFollowupBaseline | None = None,
    ):
        self.baseline = baseline or QuoteFollowupBaseline()

    def evaluate(
        self,
        opportunity: Opportunity,
        evaluation_at: datetime,
    ) -> BaselineResult:
        attention_threshold = timedelta(
            days=self.baseline.attention_after_days
        )

        if opportunity.quote_sent_at is None:
            return BaselineResult(
                opportunity_id=opportunity.id,
                elapsed=None,
                attention_threshold=attention_threshold,
                crossed=False,
                applicable=False,
                reason="Quote sent timestamp is missing.",
            )

        if opportunity.cycle_type == "long":
            return BaselineResult(
                opportunity_id=opportunity.id,
                elapsed=evaluation_at - opportunity.quote_sent_at,
                attention_threshold=attention_threshold,
                crossed=False,
                applicable=False,
                reason="Long-cycle opportunity is outside the standard follow-up baseline.",
            )

        elapsed = evaluation_at - opportunity.quote_sent_at
        crossed = elapsed >= attention_threshold

        if crossed:
            reason = (
                "Elapsed time since quote exceeded the research-derived "
                "experimental attention threshold."
            )
        else:
            reason = (
                "Elapsed time since quote has not exceeded the "
                "research-derived experimental attention threshold."
            )

        return BaselineResult(
            opportunity_id=opportunity.id,
            elapsed=elapsed,
            attention_threshold=attention_threshold,
            crossed=crossed,
            applicable=True,
            reason=reason,
        )