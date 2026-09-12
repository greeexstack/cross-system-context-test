from dataclasses import dataclass

from experiment.baseline.quote_followup import BaselineResult
from experiment.detection.followup_gap import FollowupGapDetection
from experiment.domain.models import Opportunity


@dataclass(frozen=True)
class PrimaryOnlyDiagnosis:
    opportunity_id: str
    diagnosis: str
    evidence: tuple[str, ...]
    confidence: str
    recommendation: str


class PrimaryOnlyDiagnoser:
    def diagnose(
        self,
        opportunity: Opportunity,
        baseline_result: BaselineResult,
        detection: FollowupGapDetection,
    ) -> PrimaryOnlyDiagnosis:
        evidence: list[str] = []

        if opportunity.quote_sent_at is not None:
            evidence.append(
                f"CRM quote sent at {opportunity.quote_sent_at.isoformat()}."
            )

        if opportunity.last_crm_activity_at is not None:
            evidence.append(
                "CRM last activity at "
                f"{opportunity.last_crm_activity_at.isoformat()}."
            )
        else:
            evidence.append("CRM contains no recorded activity timestamp.")

        evidence.append(
            "Experimental attention threshold: "
            f"{baseline_result.attention_threshold}."
        )

        if not detection.detected:
            return PrimaryOnlyDiagnosis(
                opportunity_id=opportunity.id,
                diagnosis=(
                    "No primary-system follow-up gap is currently detected."
                ),
                evidence=tuple(evidence),
                confidence="high",
                recommendation="No follow-up action is indicated by this detection.",
            )

        if opportunity.last_crm_activity_at is None:
            diagnosis = (
                "The opportunity has exceeded the experimental follow-up "
                "attention threshold, and the CRM contains no recorded "
                "activity timestamp after the quote."
            )
        else:
            diagnosis = (
                "The opportunity has exceeded the experimental follow-up "
                "attention threshold, and the CRM shows no recent internal "
                "activity after the quote."
            )

        return PrimaryOnlyDiagnosis(
            opportunity_id=opportunity.id,
            diagnosis=diagnosis,
            evidence=tuple(evidence),
            confidence="medium",
            recommendation=(
                "Verify the opportunity status and follow up with the "
                "opportunity owner."
            ),
        )