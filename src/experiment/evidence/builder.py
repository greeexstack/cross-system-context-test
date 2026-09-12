from experiment.baseline.quote_followup import BaselineResult
from experiment.detection.followup_gap import FollowupGapDetection
from experiment.domain.models import Opportunity
from experiment.evidence.primary_only import (
    EvidenceItem,
    PrimaryOnlyEvidence,
)


class PrimaryOnlyEvidenceBuilder:
    def build(
        self,
        opportunity: Opportunity,
        baseline_result: BaselineResult,
        detection: FollowupGapDetection,
    ) -> PrimaryOnlyEvidence:
        items: list[EvidenceItem] = []

        if opportunity.quote_sent_at is not None:
            items.append(
                EvidenceItem(
                    source="CRM",
                    event="quote_sent",
                    entity_type="opportunity",
                    entity_id=opportunity.id,
                    timestamp=opportunity.quote_sent_at.isoformat(),
                    detail="Quote was sent.",
                )
            )

        if opportunity.last_crm_activity_at is not None:
            items.append(
                EvidenceItem(
                    source="CRM",
                    event="crm_activity",
                    entity_type="opportunity",
                    entity_id=opportunity.id,
                    timestamp=opportunity.last_crm_activity_at.isoformat(),
                    detail="CRM recorded the last activity at this time.",
                )
            )
        else:
            items.append(
                EvidenceItem(
                    source="CRM",
                    event="crm_activity_missing",
                    entity_type="opportunity",
                    entity_id=opportunity.id,
                    timestamp=None,
                    detail="CRM contains no recorded activity timestamp.",
                )
            )

        items.append(
            EvidenceItem(
                source="EXPERIMENTAL_BASELINE",
                event="followup_attention_threshold",
                entity_type="opportunity",
                entity_id=opportunity.id,
                timestamp=None,
                detail=(
                    "Experimental attention threshold: "
                    f"{baseline_result.attention_threshold}."
                ),
            )
        )

        items.append(
            EvidenceItem(
                source="DETECTION",
                event="followup_gap_detection",
                entity_type="opportunity",
                entity_id=opportunity.id,
                timestamp=None,
                detail=detection.reason,
            )
        )

        return PrimaryOnlyEvidence(
            opportunity_id=opportunity.id,
            items=tuple(items),
        )