from experiment.analysis.primary_only import PrimaryOnlyAnalysis
from experiment.baseline.quote_followup import QuoteFollowupBaselineEvaluator
from experiment.detection.followup_gap import FollowupGapDetector
from experiment.diagnosis.primary_only import PrimaryOnlyDiagnoser
from experiment.domain.models import Opportunity


class PrimaryOnlyAnalysisRunner:
    def __init__(
        self,
        baseline_evaluator: QuoteFollowupBaselineEvaluator | None = None,
        detector: FollowupGapDetector | None = None,
        diagnoser: PrimaryOnlyDiagnoser | None = None,
    ):
        self.baseline_evaluator = (
            baseline_evaluator or QuoteFollowupBaselineEvaluator()
        )
        self.detector = detector or FollowupGapDetector()
        self.diagnoser = diagnoser or PrimaryOnlyDiagnoser()

    def run(
        self,
        opportunity: Opportunity,
        evaluation_at,
    ) -> PrimaryOnlyAnalysis:
        baseline = self.baseline_evaluator.evaluate(
            opportunity,
            evaluation_at,
        )

        detection = self.detector.detect(baseline)

        diagnosis = self.diagnoser.diagnose(
            opportunity,
            baseline,
            detection,
        )

        return PrimaryOnlyAnalysis(
            opportunity_id=opportunity.id,
            baseline=baseline,
            detection=detection,
            diagnosis=diagnosis,
        )