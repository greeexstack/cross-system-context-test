from dataclasses import dataclass

from experiment.baseline.quote_followup import BaselineResult
from experiment.detection.followup_gap import FollowupGapDetection
from experiment.domain.models import Opportunity
from experiment.evidence.builder import PrimaryOnlyEvidenceBuilder
from experiment.evidence.primary_only import EvidenceItem


@dataclass(frozen=True)
class PrimaryOnlyDiagnosis:
    opportunity_id: str
    diagnosis: str
    diagnosis_type: str
    evidence: tuple[EvidenceItem, ...]
    confidence: str
    recommendation: str


class PrimaryOnlyDiagnoser:
    def __init__(
        self,
        evidence_builder: PrimaryOnlyEvidenceBuilder | None = None,
    ):
        self.evidence_builder = (
            evidence_builder or PrimaryOnlyEvidenceBuilder()
        )

    def diagnose(
        self,
        opportunity: Opportunity,
        baseline_result: BaselineResult,
        detection: FollowupGapDetection,
    ) -> PrimaryOnlyDiagnosis:
        evidence = self.evidence_builder.build(
            opportunity,
            baseline_result,
            detection,
        )

        if not baseline_result.applicable:
            return PrimaryOnlyDiagnosis(
                opportunity_id=opportunity.id,
                diagnosis=(
                    "No primary-system follow-up gap is currently "
                    "detected because the opportunity is outside "
                    "the applicable follow-up baseline."
                ),
                diagnosis_type="no_finding",
                evidence=evidence.items,
                confidence="medium",
                recommendation=(
                    "No follow-up action is indicated by this detection."
                ),
            )

        if not detection.detected:
            return PrimaryOnlyDiagnosis(
                opportunity_id=opportunity.id,
                diagnosis=(
                    "No primary-system follow-up gap is currently detected."
                ),
                diagnosis_type="no_finding",
                evidence=evidence.items,
                confidence="high",
                recommendation=(
                    "No follow-up action is indicated by this detection."
                ),
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
            diagnosis_type="internal_activity_gap",
            evidence=evidence.items,
            confidence="medium",
            recommendation=(
                "Verify the opportunity status and follow up with the "
                "opportunity owner."
            ),
        )