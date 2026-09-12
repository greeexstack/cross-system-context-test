from experiment.evaluation.result import (
    AnalysisEvaluation,
    ScenarioEvaluation,
)


def test_analysis_evaluation_stores_all_evaluation_dimensions():
    result = AnalysisEvaluation(
        finding_correct=True,
        diagnosis_correct=True,
        evidence_sufficient=True,
        recommendation_appropriate=False,
    )

    assert result.finding_correct is True
    assert result.diagnosis_correct is True
    assert result.evidence_sufficient is True
    assert result.recommendation_appropriate is False


def test_scenario_evaluation_contains_primary_cross_system_and_incremental_results():
    primary = AnalysisEvaluation(
        finding_correct=True,
        diagnosis_correct=False,
        evidence_sufficient=True,
        recommendation_appropriate=True,
    )

    cross_system = AnalysisEvaluation(
        finding_correct=True,
        diagnosis_correct=True,
        evidence_sufficient=True,
        recommendation_appropriate=True,
    )

    result = ScenarioEvaluation(
        scenario_id="hidden_engagement",
        primary_only=primary,
        cross_system=cross_system,
        incremental_information_correct=True,
    )

    assert result.scenario_id == "hidden_engagement"
    assert result.primary_only.diagnosis_correct is False
    assert result.cross_system.diagnosis_correct is True
    assert result.incremental_information_correct is True