from experiment.analysis.primary_only import PrimaryOnlyAnalysis
from experiment.diagnosis.cross_system import CrossSystemDiagnosis
from experiment.evaluation.ground_truth import ExpectedAnalysis
from experiment.evaluation.result import AnalysisEvaluation


class AnalysisEvaluator:
    def evaluate_primary_only(
        self,
        actual: PrimaryOnlyAnalysis,
        expected: ExpectedAnalysis,
    ) -> AnalysisEvaluation:
        return self._evaluate(
            actual_finding=actual.detection.detected,
            actual_diagnosis=actual.diagnosis.diagnosis_type,
            actual_confidence=actual.diagnosis.confidence,
            actual_recommendation=self._recommendation_class(
                actual.diagnosis.recommendation
            ),
            actual_evidence=actual.diagnosis.evidence,
            expected=expected,
        )

    def evaluate_cross_system(
        self,
        actual_diagnosis: CrossSystemDiagnosis,
        expected: ExpectedAnalysis,
    ) -> AnalysisEvaluation:
        return self._evaluate(
            actual_finding=self._finding_from_diagnosis(
                actual_diagnosis
            ),
            actual_diagnosis=actual_diagnosis.diagnosis_type,
            actual_confidence=actual_diagnosis.confidence,
            actual_recommendation=self._recommendation_class(
                actual_diagnosis.recommendation
            ),
            actual_evidence=actual_diagnosis.evidence,
            expected=expected,
        )

    @staticmethod
    def _evaluate(
        actual_finding: bool,
        actual_diagnosis: str,
        actual_confidence: str,
        actual_recommendation: str,
        actual_evidence,
        expected: ExpectedAnalysis,
    ) -> AnalysisEvaluation:
        finding_correct = (
            actual_finding == expected.finding
        )

        diagnosis_correct = (
            actual_diagnosis == expected.diagnosis_class
            and actual_confidence == expected.confidence
        )

        evidence_sufficient = len(actual_evidence) > 0

        recommendation_appropriate = (
            actual_recommendation
            == expected.recommendation_class
        )

        return AnalysisEvaluation(
            finding_correct=finding_correct,
            diagnosis_correct=diagnosis_correct,
            evidence_sufficient=evidence_sufficient,
            recommendation_appropriate=recommendation_appropriate,
        )

    @staticmethod
    def _recommendation_class(
        recommendation: str,
    ) -> str:
        text = recommendation.lower()

        if "no follow-up action" in text:
            return "none"

        if (
            "verify the communication and follow up"
            in text
        ):
            return "verify_communication_and_owner_followup"

        if (
            "verify the communication context"
            in text
        ):
            return "verify_communication_context"

        if (
            "external communication data was unavailable"
            in text
        ):
            return "owner_followup_and_record_unavailability"
        if (
            "verify the crm follow-up status"
            in text
        ):
            return "verify_crm_followup_status"
        if (
            "verify the opportunity status and follow up"
            in text
        ):
            return "owner_followup"

        return "unknown"

    @staticmethod
    def _finding_from_diagnosis(
        diagnosis: CrossSystemDiagnosis,
    ) -> bool:
        return diagnosis.diagnosis_type not in {
    "no_finding",
    "customer_delay",
}