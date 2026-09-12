from pathlib import Path

from experiment.adapters.communication import CommunicationAdapter
from experiment.adapters.crm import CRMAdapter
from experiment.adapters.experiment import ExperimentConfigAdapter
from experiment.evaluation.ground_truth import GroundTruthLoader
from experiment.evaluation.scenario_runner import (
    ScenarioEvaluationRunner,
)


PROJECT_ROOT = Path(__file__).resolve().parent


def make_runner() -> ScenarioEvaluationRunner:
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
    )


def print_check(label: str, value: bool) -> None:
    status = "PASS" if value else "FAIL"
    print(f"  {label:<34} {status}")


def main() -> None:
    runner = make_runner()

    scenarios = [
        "normal",
        "stalled",
        "hidden_engagement",
        "long_cycle",
        "irrelevant_communication",
        "duplicate_identity",
        "incorrect_identity",
        "missing_external_data",
        "false_positive",
        "false_negative",
        "ambiguous_communication",
    ]

    total_checks = 0
    passed_checks = 0

    for scenario_id in scenarios:
        result = runner.run(scenario_id)

        scenario_checks = [
            (
                "Primary finding",
                result.primary_only.finding_correct,
            ),
            (
                "Primary diagnosis",
                result.primary_only.diagnosis_correct,
            ),
            (
                "Primary evidence",
                result.primary_only.evidence_sufficient,
            ),
            (
                "Primary recommendation",
                result.primary_only.recommendation_appropriate,
            ),
            (
                "Cross-system finding",
                result.cross_system.finding_correct,
            ),
            (
                "Cross-system diagnosis",
                result.cross_system.diagnosis_correct,
            ),
            (
                "Cross-system evidence",
                result.cross_system.evidence_sufficient,
            ),
            (
                "Cross-system recommendation",
                result.cross_system.recommendation_appropriate,
            ),
            (
                "Incremental information",
                result.incremental_information_correct,
            ),
        ]

        total_checks += len(scenario_checks)
        passed_checks += sum(
            1 for _, passed in scenario_checks if passed
        )

        print("=" * 80)
        print(f"SCENARIO: {result.scenario_id}")
        print("-" * 80)

        print("Primary-only:")
        print_check(
            "Finding",
            result.primary_only.finding_correct,
        )
        print_check(
            "Diagnosis",
            result.primary_only.diagnosis_correct,
        )
        print_check(
            "Evidence",
            result.primary_only.evidence_sufficient,
        )
        print_check(
            "Recommendation",
            result.primary_only.recommendation_appropriate,
        )

        print()
        print("Cross-system:")
        print_check(
            "Finding",
            result.cross_system.finding_correct,
        )
        print_check(
            "Diagnosis",
            result.cross_system.diagnosis_correct,
        )
        print_check(
            "Evidence",
            result.cross_system.evidence_sufficient,
        )
        print_check(
            "Recommendation",
            result.cross_system.recommendation_appropriate,
        )

        print()
        print_check(
            "Incremental information",
            result.incremental_information_correct,
        )

        scenario_passed = all(
            passed for _, passed in scenario_checks
        )

        print()
        print(
            f"SCENARIO RESULT: "
            f"{'PASS' if scenario_passed else 'FAIL'}"
        )

    print("=" * 80)
    print("EXPERIMENT COMPLETE")
    print("-" * 80)
    print(f"Passed checks: {passed_checks}/{total_checks}")

    if total_checks:
        percentage = (
            passed_checks / total_checks
        ) * 100

        print(
            f"Overall check rate: {percentage:.1f}%"
        )

    all_passed = (
        passed_checks == total_checks
    )

    print(
        f"Overall result: "
        f"{'PASS' if all_passed else 'FAIL'}"
    )


if __name__ == "__main__":
    main()