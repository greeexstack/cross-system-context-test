from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisEvaluation:
    finding_correct: bool
    diagnosis_correct: bool
    evidence_sufficient: bool
    recommendation_appropriate: bool


@dataclass(frozen=True)
class ScenarioEvaluation:
    scenario_id: str
    primary_only: AnalysisEvaluation
    cross_system: AnalysisEvaluation
    incremental_information_correct: bool