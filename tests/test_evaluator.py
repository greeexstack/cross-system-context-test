from dataclasses import dataclass
from datetime import datetime, timedelta

from experiment.evaluation.evaluator import AnalysisEvaluator
from experiment.evaluation.ground_truth import ExpectedAnalysis
from experiment.evaluation.result import AnalysisEvaluation
from experiment.domain.models import Opportunity
from experiment.baseline.quote_followup import BaselineResult
from experiment.detection.followup_gap import FollowupGapDetection
from experiment.diagnosis.primary_only import PrimaryOnlyDiagnosis
from experiment.diagnosis.cross_system import CrossSystemDiagnosis
from experiment.evidence.primary_only import EvidenceItem


def make_opportunity() -> Opportunity:
    return Opportunity(
        id="opp_001",
        business_id="biz_001",
        customer_id="cust_001",
        owner_id="emp_001",
        stage="quote_sent",
        value=5000.0,
        quote_sent_at=datetime.fromisoformat(
            "2026-01-01T10:00:00"
        ),
        last_crm_activity_at=None,
    )


def make_evidence() -> tuple[EvidenceItem, ...]:
    return (
        EvidenceItem(
            source="CRM",
            event="quote_sent",
            entity_type="opportunity",
            entity_id="opp_001",
            timestamp="2026-01-01T10:00:00",
            detail="Quote sent to customer.",
        ),
    )


def make_baseline() -> BaselineResult:
    return BaselineResult(
        opportunity_id="opp_001",
        elapsed=timedelta(days=8),
        attention_threshold=timedelta(days=7),
        crossed=True,
        applicable=True,
        reason=(
            "Elapsed time since quote exceeded the research-derived "
            "experimental attention threshold."
        ),
    )


def make_detection() -> FollowupGapDetection:
    return FollowupGapDetection(
        opportunity_id="opp_001",
        detected=True,
        reason="Opportunity has crossed the follow-up attention threshold.",
    )


def make_primary_diagnosis() -> PrimaryOnlyDiagnosis:
    return PrimaryOnlyDiagnosis(
        opportunity_id="opp_001",
        diagnosis=(
            "The opportunity has exceeded the experimental follow-up "
            "attention threshold, and the CRM contains no recorded "
            "activity timestamp after the quote."
        ),
        diagnosis_type="internal_activity_gap",
        evidence=make_evidence(),
        confidence="medium",
        recommendation=(
            "Verify the opportunity status and follow up with "
            "the opportunity owner."
        ),
    )


def make_cross_system_diagnosis() -> CrossSystemDiagnosis:
    return CrossSystemDiagnosis(
        opportunity_id="opp_001",
        diagnosis=(
            "The customer recently engaged about the quote, while the "
            "CRM shows no corresponding recent internal activity. The "
            "primary-system follow-up gap therefore appears more "
            "consistent with an internal activity or follow-up gap "
            "than customer inactivity."
        ),
        diagnosis_type="internal_activity_gap",
        evidence=make_evidence(),
        confidence="high",
        recommendation=(
            "Verify the communication and follow up with "
            "the opportunity owner."
        ),
    )


def test_primary_only_evaluation_matches_expected_analysis():
    evaluator = AnalysisEvaluator()

    actual = type(
        "PrimaryAnalysis",
        (),
        {
            "detection": make_detection(),
            "diagnosis": make_primary_diagnosis(),
            "baseline": make_baseline(),
        },
    )()

    expected = ExpectedAnalysis(
        finding=True,
        diagnosis_class="internal_activity_gap",
        confidence="medium",
        recommendation_class="owner_followup",
    )

    result = evaluator.evaluate_primary_only(
        actual,
        expected,
    )

    assert result == AnalysisEvaluation(
        finding_correct=True,
        diagnosis_correct=True,
        evidence_sufficient=True,
        recommendation_appropriate=True,
    )


def test_cross_system_evaluation_matches_expected_analysis():
    evaluator = AnalysisEvaluator()

    actual = make_cross_system_diagnosis()

    expected = ExpectedAnalysis(
        finding=True,
        diagnosis_class="internal_activity_gap",
        confidence="high",
        recommendation_class="verify_communication_and_owner_followup",
    )

    result = evaluator.evaluate_cross_system(
        actual,
        expected,
    )

    assert result == AnalysisEvaluation(
        finding_correct=True,
        diagnosis_correct=True,
        evidence_sufficient=True,
        recommendation_appropriate=True,
    )


def test_incorrect_expected_diagnosis_is_detected():
    evaluator = AnalysisEvaluator()

    actual = make_cross_system_diagnosis()

    expected = ExpectedAnalysis(
        finding=True,
        diagnosis_class="customer_engaged_internal_activity_gap",
        confidence="high",
        recommendation_class="verify_communication_and_owner_followup",
    )

    result = evaluator.evaluate_cross_system(
        actual,
        expected,
    )

    assert result == AnalysisEvaluation(
        finding_correct=True,
        diagnosis_correct=False,
        evidence_sufficient=True,
        recommendation_appropriate=True,
    )