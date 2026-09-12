from pathlib import Path

from experiment.adapters.communication import CommunicationAdapter
from experiment.adapters.crm import CRMAdapter
from experiment.adapters.experiment import ExperimentConfigAdapter
from experiment.evaluation.evaluator import AnalysisEvaluator
from experiment.evaluation.ground_truth import GroundTruthLoader
from experiment.evaluation.scenario_runner import (
    ScenarioEvaluationRunner,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def make_runner():
    return ScenarioEvaluationRunner(
        crm_adapter=CRMAdapter(
            PROJECT_ROOT / "scenarios" / "data" / "crm.json"
        ),
        communication_adapter=CommunicationAdapter(
            PROJECT_ROOT
            / "scenarios"
            / "data"
            / "communications.json"
        ),
        experiment_config_adapter=ExperimentConfigAdapter(
            PROJECT_ROOT / "scenarios" / "experiment.json"
        ),
        ground_truth_loader=GroundTruthLoader(
            PROJECT_ROOT / "scenarios"
        ),
        evaluator=AnalysisEvaluator(),
    )


def test_hidden_engagement_evaluation_shows_cross_system_value():
    result = make_runner().run("hidden_engagement")

    assert result.scenario_id == "hidden_engagement"

    assert result.primary_only.finding_correct is True
    assert result.primary_only.diagnosis_correct is True
    assert result.primary_only.evidence_sufficient is True
    assert result.primary_only.recommendation_appropriate is True

    assert result.cross_system.finding_correct is True
    assert result.cross_system.diagnosis_correct is True
    assert result.cross_system.evidence_sufficient is True
    assert result.cross_system.recommendation_appropriate is True

    assert result.incremental_information_correct is True


def test_irrelevant_communication_does_not_create_incremental_finding():
    result = make_runner().run(
        "irrelevant_communication"
    )

    assert result.primary_only.finding_correct is True
    assert result.cross_system.finding_correct is True

    assert result.primary_only.diagnosis_correct is True
    assert result.cross_system.diagnosis_correct is True

    assert result.incremental_information_correct is True


def test_long_cycle_opportunity_is_not_flagged():
    result = make_runner().run("long_cycle")

    assert result.primary_only.finding_correct is True
    assert result.cross_system.finding_correct is True

    assert result.primary_only.diagnosis_correct is True
    assert result.cross_system.diagnosis_correct is True

    assert result.incremental_information_correct is True