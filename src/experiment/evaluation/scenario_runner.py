
from datetime import datetime

from experiment.adapters.communication import CommunicationAdapter
from experiment.adapters.crm import CRMAdapter
from experiment.adapters.experiment import ExperimentConfigAdapter
from experiment.analysis.context import CommunicationSourceStatus
from experiment.analysis.cross_system_runner import CrossSystemAnalysisRunner
from experiment.analysis.runner import PrimaryOnlyAnalysisRunner
from experiment.domain.models import Communication
from experiment.evaluation.evaluator import AnalysisEvaluator
from experiment.evaluation.ground_truth import GroundTruthLoader
from experiment.evaluation.result import ScenarioEvaluation


class ScenarioEvaluationRunner:
    def __init__(
        self,
        crm_adapter: CRMAdapter,
        communication_adapter: CommunicationAdapter,
        experiment_config_adapter: ExperimentConfigAdapter,
        ground_truth_loader: GroundTruthLoader,
        primary_runner: PrimaryOnlyAnalysisRunner | None = None,
        cross_system_runner: CrossSystemAnalysisRunner | None = None,
        evaluator: AnalysisEvaluator | None = None,
    ):
        self.crm_adapter = crm_adapter
        self.communication_adapter = communication_adapter
        self.experiment_config_adapter = experiment_config_adapter
        self.ground_truth_loader = ground_truth_loader

        self.primary_runner = (
            primary_runner or PrimaryOnlyAnalysisRunner()
        )

        self.cross_system_runner = (
            cross_system_runner or CrossSystemAnalysisRunner()
        )

        self.evaluator = evaluator or AnalysisEvaluator()

    def run(
        self,
        scenario_id: str,
    ) -> ScenarioEvaluation:
        communication_scenario = (
            self.communication_adapter.load_scenario(
                scenario_id
            )
        )

        ground_truth = self.ground_truth_loader.load(
            scenario_id
        )

        evaluation_at = (
            self.experiment_config_adapter.load_evaluation_at()
        )

        (
            business,
            customer,
            employee,
            opportunity,
            quote,
        ) = self._load_crm_entities(
            scenario_id
        )

        communication, communication_source_status = (
            self._load_communication(
                communication_scenario
            )
        )

        primary_analysis = self.primary_runner.run(
            opportunity,
            evaluation_at,
        )

        cross_system_analysis = (
            self.cross_system_runner.run(
                opportunity,
                customer,
                evaluation_at,
                communication,
                communication_source_status,
            )
        )

        primary_evaluation = (
            self.evaluator.evaluate_primary_only(
                primary_analysis,
                ground_truth.primary_only,
            )
        )

        cross_system_evaluation = (
            self.evaluator.evaluate_cross_system(
                cross_system_analysis.diagnosis,
                ground_truth.cross_system,
            )
        )

        actual_incremental_information = (
            self._incremental_information(
                primary_analysis,
                cross_system_analysis,
            )
        )

        return ScenarioEvaluation(
            scenario_id=scenario_id,
            primary_only=primary_evaluation,
            cross_system=cross_system_evaluation,
            incremental_information_correct=(
                actual_incremental_information
                == ground_truth.incremental_information
            ),
        )

    def _load_crm_entities(self, scenario_id: str):
        for entities in self.crm_adapter.load_entities():
            opportunity = entities[3]

            if opportunity.id == f"opp_{self._scenario_number(scenario_id)}":
                return entities

        raise ValueError(
            f"CRM entities not found for scenario: {scenario_id}"
        )

    @staticmethod
    def _load_communication(
        scenario: dict,
    ) -> tuple[
        Communication | None,
        CommunicationSourceStatus,
    ]:
        communications = scenario.get("communications")

        if communications is None:
            return (
                None,
                CommunicationSourceStatus.UNAVAILABLE,
            )

        if not communications:
            return (
                None,
                CommunicationSourceStatus.AVAILABLE_NO_COMMUNICATION,
            )

        item = communications[0]
        customer = scenario["customer"]

        return (
            Communication(
                id=item["id"],
                business_id="biz_001",
                customer_id=customer["id"],
                direction=item["direction"],
                timestamp=datetime.fromisoformat(
                    item["timestamp"]
                ),
                channel=item["channel"],
                topic=item["topic"],
                content=item["content"],
                customer_name=customer.get("name"),
                customer_email=customer.get("email"),
                customer_phone=customer.get("phone"),
            ),
            CommunicationSourceStatus.COMMUNICATION_OBSERVED,
        )

    @staticmethod
    def _scenario_number(scenario_id: str) -> str:
        scenario_numbers = {
            "normal": "001",
            "stalled": "002",
            "hidden_engagement": "003",
            "long_cycle": "004",
            "irrelevant_communication": "005",
            "duplicate_identity": "006",
            "incorrect_identity": "007",
            "missing_external_data": "008",
            "false_positive": "009",
            "false_negative": "010",
            "ambiguous_communication": "011",
        }

        try:
            return scenario_numbers[scenario_id]
        except KeyError as exc:
            raise ValueError(
                f"Unknown scenario: {scenario_id}"
            ) from exc

    def _incremental_information(
        self,
        primary_analysis,
        cross_system_analysis,
    ) -> bool:
        primary_diagnosis = primary_analysis.diagnosis
        cross_system_diagnosis = cross_system_analysis.diagnosis

        # If the primary baseline does not apply, there is no
        # primary-system finding for external context to improve.
        if not primary_analysis.baseline.applicable:
            return False

        cross_diagnosis_type = (
            cross_system_diagnosis.diagnosis_type
        )

        # No finding means the external system did not change the
        # business interpretation.
        if cross_diagnosis_type == "no_finding":
            return False

        # Missing external data is not itself useful business context.
        if cross_diagnosis_type == "external_data_unavailable":
            return False
                # No communication means the external system provided no
        # additional business context.
        if cross_system_analysis.context.communication_source_status.value == (
            "available_no_communication"
        ):
            return False

        # Communication explicitly unrelated to the opportunity does
        # not provide incremental information about that opportunity.
        if cross_diagnosis_type == "unrelated_communication":
            return False

        # A communication belonging to a different customer must not
        # be treated as useful context for this opportunity.
        if cross_diagnosis_type == "unverified_communication":
            if (
                cross_system_analysis.context.customer_identity_status.value
                != "confident_match"
            ):
                return False

        # A genuinely changed business diagnosis is incremental
        # information, provided the new diagnosis is based on usable
        # external context.
        if (
            primary_diagnosis.diagnosis_type
            != cross_diagnosis_type
        ):
            return True

        # If the diagnosis is unchanged, external evidence only counts
        # when it materially strengthens the interpretation.
        #
        # Normal outbound communication is expected corroboration and
        # therefore is not treated as incremental information.
        communication_evidence = [
            evidence
            for evidence in cross_system_diagnosis.evidence
            if evidence.source == "COMMUNICATION"
        ]

        if not communication_evidence:
            return False

        if all(
            "outbound" in evidence.detail.lower()
            for evidence in communication_evidence
        ):
            return False

        return True
