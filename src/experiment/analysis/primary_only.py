from dataclasses import dataclass

from experiment.baseline.quote_followup import BaselineResult
from experiment.detection.followup_gap import FollowupGapDetection
from experiment.diagnosis.primary_only import PrimaryOnlyDiagnosis


@dataclass(frozen=True)
class PrimaryOnlyAnalysis:
    opportunity_id: str
    baseline: BaselineResult
    detection: FollowupGapDetection
    diagnosis: PrimaryOnlyDiagnosis