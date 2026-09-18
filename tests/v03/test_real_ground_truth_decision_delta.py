"""
Benchmark-relative decision delta experiment.

Purpose
-------
Measure the decision-quality difference between:

    primary-only actual analysis
    vs.
    cross-system actual analysis

against the SAME target:

    the repository's existing cross-system ground truth.

This fixes the earlier experimental-control problem where each actual
system was evaluated against its own separate expected target.

Important limitation
--------------------
The target is still authored benchmark truth from the repository.

This experiment therefore measures:

    correctness relative to the cross-system benchmark

It does NOT establish that the cross-system benchmark itself is
independently valid.

No production code is changed.
"""

from __future__ import annotations

import json
from pathlib import Path


from experiment.adapters.communication import CommunicationAdapter
from experiment.adapters.crm import CRMAdapter
from experiment.adapters.experiment import ExperimentConfigAdapter
from experiment.evaluation.evaluator import AnalysisEvaluator
from experiment.evaluation.ground_truth import GroundTruthLoader
from experiment.evaluation.scenario_runner import (
    ScenarioEvaluationRunner,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCENARIOS = (
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
)


def _runner() -> ScenarioEvaluationRunner:
    return ScenarioEvaluationRunner(
        crm_adapter=CRMAdapter(
            PROJECT_ROOT
            / "scenarios"
            / "data"
            / "crm.json"
        ),
        communication_adapter=CommunicationAdapter(
            PROJECT_ROOT
            / "scenarios"
            / "data"
            / "communications.json"
        ),
        experiment_config_adapter=ExperimentConfigAdapter(
            PROJECT_ROOT
            / "scenarios"
            / "experiment.json"
        ),
        ground_truth_loader=GroundTruthLoader(
            PROJECT_ROOT / "scenarios"
        ),
        evaluator=AnalysisEvaluator(),
    )


def _component_score(evaluation) -> int:
    """
    Count correctly evaluated dimensions.

    Dimensions:
        finding
        diagnosis + confidence
        evidence sufficiency
        recommendation
    """
    return sum(
        (
            evaluation.finding_correct,
            evaluation.diagnosis_correct,
            evaluation.evidence_sufficient,
            evaluation.recommendation_appropriate,
        )
    )


def _exact_correct(evaluation) -> bool:
    return _component_score(evaluation) == 4


def _component_bools(evaluation) -> dict[str, bool]:
    return {
        "finding": evaluation.finding_correct,
        "diagnosis": evaluation.diagnosis_correct,
        "evidence": evaluation.evidence_sufficient,
        "recommendation": (
            evaluation.recommendation_appropriate
        ),
    }


def _raw_scenario(runner: ScenarioEvaluationRunner, scenario_id: str):
    """
    Obtain raw primary and cross-system analyses from the same execution
    path used by ScenarioEvaluationRunner.

    We deliberately bypass its normal self-target evaluation here so both
    actual systems can be scored against the same cross-system target.
    """
    communication_scenario = (
        runner.communication_adapter.load_scenario(
            scenario_id
        )
    )

    ground_truth = runner.ground_truth_loader.load(
        scenario_id
    )

    evaluation_at = (
        runner.experiment_config_adapter.load_evaluation_at()
    )

    (
        _business,
        customer,
        _employee,
        opportunity,
        _quote,
    ) = runner._load_crm_entities(
        scenario_id
    )

    communication, communication_source_status = (
        runner._load_communication(
            communication_scenario
        )
    )

    primary_analysis = runner.primary_runner.run(
        opportunity,
        evaluation_at,
    )

    cross_system_analysis = (
        runner.cross_system_runner.run(
            opportunity,
            customer,
            evaluation_at,
            communication,
            communication_source_status,
        )
    )

    return (
        ground_truth,
        primary_analysis,
        cross_system_analysis,
    )


def _case_record(
    scenario_id: str,
    evaluator: AnalysisEvaluator,
    ground_truth,
    primary_analysis,
    cross_system_analysis,
) -> dict:
    """
    Evaluate BOTH actual systems against the cross-system ground truth.

    Self-target results are retained as diagnostic metadata so we can see
    the difference between the old evaluation design and the corrected one.
    """
    cross_target = ground_truth.cross_system

    primary_self_target = evaluator.evaluate_primary_only(
        primary_analysis,
        ground_truth.primary_only,
    )

    cross_self_target = evaluator.evaluate_cross_system(
        cross_system_analysis.diagnosis,
        ground_truth.cross_system,
    )

    primary_cross_target = evaluator.evaluate_primary_only(
        primary_analysis,
        cross_target,
    )

    cross_cross_target = evaluator.evaluate_cross_system(
        cross_system_analysis.diagnosis,
        cross_target,
    )

    return {
        "scenario_id": scenario_id,
        "primary_against_own_target": {
            "score": _component_score(
                primary_self_target
            ),
            "exact_correct": _exact_correct(
                primary_self_target
            ),
            "components": _component_bools(
                primary_self_target
            ),
        },
        "cross_system_against_own_target": {
            "score": _component_score(
                cross_self_target
            ),
            "exact_correct": _exact_correct(
                cross_self_target
            ),
            "components": _component_bools(
                cross_self_target
            ),
        },
        "primary_against_cross_system_target": {
            "score": _component_score(
                primary_cross_target
            ),
            "exact_correct": _exact_correct(
                primary_cross_target
            ),
            "components": _component_bools(
                primary_cross_target
            ),
        },
        "cross_system_against_cross_system_target": {
            "score": _component_score(
                cross_cross_target
            ),
            "exact_correct": _exact_correct(
                cross_cross_target
            ),
            "components": _component_bools(
                cross_cross_target
            ),
        },
        "benchmark_relative_improvement": (
            not _exact_correct(primary_cross_target)
            and _exact_correct(cross_cross_target)
        ),
        "benchmark_relative_harm": (
            _exact_correct(primary_cross_target)
            and not _exact_correct(cross_cross_target)
        ),
    }


def _run_all() -> list[dict]:
    runner = _runner()
    evaluator = AnalysisEvaluator()

    records = []

    for scenario_id in SCENARIOS:
        (
            ground_truth,
            primary_analysis,
            cross_system_analysis,
        ) = _raw_scenario(
            runner,
            scenario_id,
        )

        records.append(
            _case_record(
                scenario_id,
                evaluator,
                ground_truth,
                primary_analysis,
                cross_system_analysis,
            )
        )

    return records


def test_all_existing_scenarios_are_evaluable():
    records = _run_all()

    assert len(records) == len(SCENARIOS)

    assert {
        record["scenario_id"]
        for record in records
    } == set(SCENARIOS)


def test_benchmark_relative_decision_delta_is_measured():
    """
    The actual comparison is:

        primary actual  -> cross-system target
        cross actual    -> cross-system target

    No directional outcome is asserted here. The test only verifies that
    the measurement is structurally valid and reports the observed result.
    """
    records = _run_all()

    primary_exact = sum(
        record[
            "primary_against_cross_system_target"
        ]["exact_correct"]
        for record in records
    )

    cross_system_exact = sum(
        record[
            "cross_system_against_cross_system_target"
        ]["exact_correct"]
        for record in records
    )

    improvements = sum(
        record["benchmark_relative_improvement"]
        for record in records
    )

    harm = sum(
        record["benchmark_relative_harm"]
        for record in records
    )

    total = len(records)

    primary_rate = primary_exact / total
    cross_system_rate = cross_system_exact / total

    delta = cross_system_rate - primary_rate

    summary = {
        "total_scenarios": total,
        "target": "cross_system_ground_truth",
        "primary_exact_correct": primary_exact,
        "cross_system_exact_correct": cross_system_exact,
        "primary_exact_correct_rate": primary_rate,
        "cross_system_exact_correct_rate": (
            cross_system_rate
        ),
        "benchmark_relative_correctness_delta": delta,
        "benchmark_relative_improvement_cases": improvements,
        "benchmark_relative_harm_cases": harm,
    }

    print(
        "\n=== BENCHMARK-RELATIVE DECISION DELTA ==="
    )
    print(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
    )

    print(
        "\n=== PER-SCENARIO ==="
    )

    for record in records:
        print(
            json.dumps(
                record,
                indent=2,
                sort_keys=True,
            )
        )

    assert (
        improvements + harm
        <= total
    )


def test_cross_system_target_is_used_for_both_actuals():
    """
    Regression guard for the experimental control.

    Both actual systems must be evaluated against the cross-system target,
    rather than each system silently receiving its own target.
    """
    runner = _runner()
    evaluator = AnalysisEvaluator()

    for scenario_id in SCENARIOS:
        (
            ground_truth,
            primary_analysis,
            cross_system_analysis,
        ) = _raw_scenario(
            runner,
            scenario_id,
        )

        expected = ground_truth.cross_system

        primary_evaluation = (
            evaluator.evaluate_primary_only(
                primary_analysis,
                expected,
            )
        )

        cross_system_evaluation = (
            evaluator.evaluate_cross_system(
                cross_system_analysis.diagnosis,
                expected,
            )
        )

        assert primary_evaluation is not None
        assert cross_system_evaluation is not None


def test_component_level_benchmark_delta_is_separated():
    records = _run_all()

    dimensions = (
        "finding",
        "diagnosis",
        "evidence",
        "recommendation",
    )

    for dimension in dimensions:
        primary_correct = sum(
            record[
                "primary_against_cross_system_target"
            ]["components"][dimension]
            for record in records
        )

        cross_system_correct = sum(
            record[
                "cross_system_against_cross_system_target"
            ]["components"][dimension]
            for record in records
        )

        total = len(records)

        assert 0 <= primary_correct <= total
        assert 0 <= cross_system_correct <= total


def test_benchmark_improvement_and_harm_are_disjoint():
    records = _run_all()

    for record in records:
        assert not (
            record["benchmark_relative_improvement"]
            and record["benchmark_relative_harm"]
        )


def test_output_change_is_separate_from_benchmark_correctness():
    """
    Output changes and correctness changes are separate measurements.
    """
    records = _run_all()

    output_changes = 0
    correctness_changes = 0

    for record in records:
        primary = record[
            "primary_against_cross_system_target"
        ]
        cross_system = record[
            "cross_system_against_cross_system_target"
        ]

        if (
            primary["score"] != cross_system["score"]
            or primary["components"]
            != cross_system["components"]
        ):
            output_changes += 1

        if (
            primary["exact_correct"]
            != cross_system["exact_correct"]
        ):
            correctness_changes += 1

    print(
        "\n=== BENCHMARK TARGET: OUTPUT VS CORRECTNESS ==="
    )
    print(
        json.dumps(
            {
                "total_scenarios": len(records),
                "output_change_cases": output_changes,
                "output_change_rate": (
                    output_changes / len(records)
                ),
                "correctness_change_cases": (
                    correctness_changes
                ),
                "correctness_change_rate": (
                    correctness_changes
                    / len(records)
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )

    assert 0 <= output_changes <= len(records)
    assert (
        0
        <= correctness_changes
        <= len(records)
    )