from dataclasses import dataclass

from experiment.baseline.quote_followup import BaselineResult


@dataclass(frozen=True)
class FollowupGapDetection:
    opportunity_id: str
    detected: bool
    reason: str


class FollowupGapDetector:
    def detect(
        self,
        baseline_result: BaselineResult,
    ) -> FollowupGapDetection:
        if not baseline_result.applicable:
            return FollowupGapDetection(
                opportunity_id=baseline_result.opportunity_id,
                detected=False,
                reason=(
                    "Follow-up gap detection is not applicable "
                    "because the baseline is unavailable or excluded."
                ),
            )

        if not baseline_result.crossed:
            return FollowupGapDetection(
                opportunity_id=baseline_result.opportunity_id,
                detected=False,
                reason=(
                    "The opportunity has not crossed the "
                    "follow-up attention threshold."
                ),
            )

        return FollowupGapDetection(
            opportunity_id=baseline_result.opportunity_id,
            detected=True,
            reason=(
                "The opportunity has crossed the follow-up "
                "attention threshold and warrants investigation."
            ),
        )