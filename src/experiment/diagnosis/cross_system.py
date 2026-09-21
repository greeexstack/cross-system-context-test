from dataclasses import dataclass

from experiment.analysis.context import (
    CommunicationSourceStatus,
    CustomerIdentityStatus,
)
from experiment.baseline.quote_followup import BaselineResult
from experiment.detection.followup_gap import FollowupGapDetection
from experiment.domain.models import Communication, Opportunity
from experiment.evidence.primary_only import EvidenceItem


@dataclass(frozen=True)
class CrossSystemDiagnosis:
    opportunity_id: str
    diagnosis: str
    diagnosis_type: str
    evidence: tuple[EvidenceItem, ...]
    confidence: str
    recommendation: str


class CrossSystemDiagnoser:
    def diagnose(
        self,
        opportunity: Opportunity,
        communication: Communication | None,
        primary_evidence: tuple[EvidenceItem, ...],
        baseline_result: BaselineResult | None = None,
        primary_detection: FollowupGapDetection | None = None,
        customer_identity_status: CustomerIdentityStatus | None = None,
        communication_source_status: CommunicationSourceStatus | None = None,
    ) -> CrossSystemDiagnosis:

        if baseline_result is not None and not baseline_result.applicable:
            return CrossSystemDiagnosis(
                opportunity_id=opportunity.id,
                diagnosis=(
                    "No cross-system follow-up gap is currently detected "
                    "because the opportunity is outside the applicable "
                    "follow-up baseline."
                ),
                diagnosis_type="no_finding",
                evidence=primary_evidence,
                confidence="high",
                recommendation=(
                    "No follow-up action is indicated by this detection."
                ),
            )

        primary_detected = (
            primary_detection.detected
            if primary_detection is not None
            else True
        )

        if (
            communication_source_status
            == CommunicationSourceStatus.AVAILABLE_NO_COMMUNICATION
        ):
            if primary_detected:
                return CrossSystemDiagnosis(
                    opportunity_id=opportunity.id,
                    diagnosis=(
                        "The CRM indicates a follow-up gap, and the "
                        "communication source is available but shows no "
                        "observed customer communication."
                    ),
                    diagnosis_type="followup_gap",
                    evidence=primary_evidence,
                    confidence="high",
                    recommendation=(
                        "Verify the opportunity status and follow up with "
                        "the opportunity owner."
                    ),
                )

            return CrossSystemDiagnosis(
                opportunity_id=opportunity.id,
                diagnosis=(
                    "No cross-system follow-up gap is currently detected, "
                    "and no customer communication was observed."
                ),
                diagnosis_type="no_finding",
                evidence=primary_evidence,
                confidence="high",
                recommendation=(
                    "No follow-up action is indicated by this detection."
                ),
            )

        if (
            communication_source_status
            == CommunicationSourceStatus.UNAVAILABLE
        ):
            if primary_detected:
                return CrossSystemDiagnosis(
                    opportunity_id=opportunity.id,
                    diagnosis=(
                        "The CRM indicates a follow-up gap, but external "
                        "communication data is unavailable."
                    ),
                    diagnosis_type="external_data_unavailable",
                    evidence=primary_evidence,
                    confidence="medium",
                    recommendation=(
                        "Follow up with the opportunity owner and record "
                        "that external communication data was unavailable."
                    ),
                )

            return CrossSystemDiagnosis(
                opportunity_id=opportunity.id,
                diagnosis=(
                    "No cross-system follow-up gap is currently detected, "
                    "but external communication data is unavailable."
                ),
                diagnosis_type="external_data_unavailable",
                evidence=primary_evidence,
                confidence="medium",
                recommendation=(
                    "No follow-up action is indicated by this detection."
                ),
            )

        if customer_identity_status in (
            CustomerIdentityStatus.AMBIGUOUS_MATCH,
            CustomerIdentityStatus.NO_MATCH,
        ):
            if primary_detected:
                return CrossSystemDiagnosis(
                    opportunity_id=opportunity.id,
                    diagnosis=(
                        "The CRM indicates a follow-up gap, but the observed "
                        "communication could not be confidently attributed "
                        "to the CRM customer."
                    ),
                    diagnosis_type="unverified_communication",
                    evidence=primary_evidence,
                    confidence="medium",
                    recommendation=(
                        "Verify the CRM follow-up status before taking "
                        "action."
                    ),
                )

            return CrossSystemDiagnosis(
                opportunity_id=opportunity.id,
                diagnosis=(
                    "No cross-system follow-up gap is currently detected, "
                    "and the observed communication could not be confidently "
                    "attributed to the CRM customer."
                ),
                diagnosis_type="unverified_communication",
                evidence=primary_evidence,
                confidence="high",
                recommendation=(
                    "No follow-up action is indicated by this detection."
                ),
            )

        if communication is None:
            if primary_detected:
                return CrossSystemDiagnosis(
                    opportunity_id=opportunity.id,
                    diagnosis=(
                        "The CRM indicates a follow-up gap, but external "
                        "communication data is unavailable."
                    ),
                    diagnosis_type="external_data_unavailable",
                    evidence=primary_evidence,
                    confidence="medium",
                    recommendation=(
                        "Follow up with the opportunity owner and record "
                        "that external communication data was unavailable."
                    ),
                )

            return CrossSystemDiagnosis(
                opportunity_id=opportunity.id,
                diagnosis=(
                    "No cross-system follow-up gap is currently detected."
                ),
                diagnosis_type="no_finding",
                evidence=primary_evidence,
                confidence="high",
                recommendation=(
                    "No follow-up action is indicated by this detection."
                ),
            )

        communication_evidence = EvidenceItem(
            source="COMMUNICATION",
            event="customer_communication",
            entity_type="customer",
            entity_id=communication.customer_id,
            timestamp=communication.timestamp.isoformat(),
            detail=(
                f"{communication.direction} {communication.channel} "
                f"communication about {communication.topic}."
            ),
        )

        evidence = primary_evidence + (communication_evidence,)

        if communication.direction == "inbound":
            content = communication.content.lower()

            # Explicitly identified different-work-item communication must
            # not be interpreted as evidence about the current opportunity.
            if any(
                phrase in content
                for phrase in (
                    "different project",
                    "separate project",
                    "another project",
                    "different work item",
                    "different opportunity",
                )
            ):
                return CrossSystemDiagnosis(
                    opportunity_id=opportunity.id,
                    diagnosis=(
                        "The available communication explicitly concerns "
                        "a different work item rather than the opportunity "
                        "under review."
                    ),
                    diagnosis_type="unrelated_communication",
                    evidence=evidence,
                    confidence="high",
                    recommendation=(
                        "Verify the opportunity status and follow up with "
                        "the opportunity owner."
                    ),
                )

            if communication.topic == "quote":
                if any(
                    phrase in content
                    for phrase in (
                        "wait",
                        "later",
                        "end of month",
                        "next month",
                        "delay",
                        "not ready",
                    )
                ):
                    return CrossSystemDiagnosis(
                        opportunity_id=opportunity.id,
                        diagnosis=(
                            "The customer requested a delay regarding the "
                            "quote, so the CRM follow-up gap does not by "
                            "itself indicate that immediate follow-up is "
                            "required."
                        ),
                        diagnosis_type="customer_delay",
                        evidence=evidence,
                        confidence="high",
                        recommendation=(
                            "No follow-up action is indicated by this "
                            "detection."
                        ),
                    )

                if primary_detected:
                    return CrossSystemDiagnosis(
                        opportunity_id=opportunity.id,
                        diagnosis=(
                            "The customer recently engaged about the quote, "
                            "while the CRM shows no corresponding recent "
                            "internal activity. The primary-system "
                            "follow-up gap therefore appears more "
                            "consistent with an internal activity or "
                            "follow-up gap than customer inactivity."
                        ),
                        diagnosis_type="internal_activity_gap",
                        evidence=evidence,
                        confidence="high",
                        recommendation=(
                            "Verify the communication and follow up with "
                            "the opportunity owner."
                        ),
                    )

                return CrossSystemDiagnosis(
                    opportunity_id=opportunity.id,
                    diagnosis=(
                        "The customer recently engaged about the quote, "
                        "providing external evidence that the opportunity "
                        "requires follow-up even though the primary CRM "
                        "detection did not identify a follow-up gap."
                    ),
                    diagnosis_type="followup_gap",
                    evidence=evidence,
                    confidence="high",
                    recommendation=(
                        "Verify the communication and follow up with "
                        "the opportunity owner."
                    ),
                )

            if communication.topic == "invoice":
                return CrossSystemDiagnosis(
                    opportunity_id=opportunity.id,
                    diagnosis=(
                        "The opportunity has a CRM follow-up gap, but the "
                        "available communication concerns an unrelated "
                        "invoice rather than the quote."
                    ),
                    diagnosis_type="unrelated_communication",
                    evidence=evidence,
                    confidence="high",
                    recommendation=(
                        "Verify the opportunity status and follow up with "
                        "the opportunity owner."
                    ),
                )

            return CrossSystemDiagnosis(
                opportunity_id=opportunity.id,
                diagnosis=(
                    "The opportunity has a CRM follow-up gap, but the "
                    "external communication does not establish that the "
                    "communication concerns the quote."
                ),
                diagnosis_type="unverified_communication",
                evidence=evidence,
                confidence="low",
                recommendation=(
                    "Verify the communication context before taking "
                    "follow-up action."
                ),
            )

        if primary_detected:
            return CrossSystemDiagnosis(
                opportunity_id=opportunity.id,
                diagnosis=(
                    "The opportunity has a CRM follow-up gap, and the "
                    "available communication does not establish recent "
                    "customer engagement."
                ),
                diagnosis_type="followup_gap",
                evidence=evidence,
                confidence="high",
                recommendation=(
                    "Verify the opportunity status and follow up with "
                    "the opportunity owner."
                ),
            )

        return CrossSystemDiagnosis(
            opportunity_id=opportunity.id,
            diagnosis=(
                "No cross-system follow-up gap is currently detected."
            ),
            diagnosis_type="no_finding",
            evidence=evidence,
            confidence="high",
            recommendation=(
                "No follow-up action is indicated by this detection."
            ),
        )