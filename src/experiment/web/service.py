from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from experiment.v02.engine import ReasoningResult
from experiment.v02.runner import V02Runner

from .models import (
    CaseResult,
    DimensionResult,
    EvaluationListItem,
    EvaluationResult,
    ReasoningSnapshot,
)


DIMENSIONS = (
    "context_sensitivity",
    "context_resistance",
    "direction_correctness",
    "evidence_validity",
    "identity_integrity",
    "temporal_integrity",
    "ambiguity_handling",
    "missing_data_handling",
    "generalization",
)


def reasoning_snapshot(result: ReasoningResult) -> ReasoningSnapshot:
    return ReasoningSnapshot(
        pair_id=result.pair_id,
        phase=result.phase,
        interpretation_class=result.interpretation_class,
        support_level=result.support_level,
        decision_strength=result.decision_strength,
        identity_match=result.identity_match,
        temporal_status=result.temporal_status,
        availability=result.availability,
        reversion=result.reversion,
        recommended_focus=result.recommended_focus,
        evidence_ids=list(result.evidence_ids),
        evidence_valid=result.evidence_valid,
        notes=list(result.notes),
    )


class EvaluationService:
    def __init__(self, fixture_root: str | Path) -> None:
        self.fixture_root = Path(fixture_root)
        self.runner = V02Runner(self.fixture_root)
        self._runs: dict[str, EvaluationResult] = {}

    def run_v02(self) -> EvaluationResult:
        started_at = datetime.now(timezone.utc)

        case_results: list[CaseResult] = []
        dimension_pass_counts = {
            dimension: 0 for dimension in DIMENSIONS
        }

        for case in self.runner.scenarios:
            expected = (
                self.runner.dev_gt
                if case["split"] == "development"
                else self.runner.eval_gt
            )

            expected_case = next(
                item
                for item in expected["cases"]
                if item["pair_id"] == case["pair_id"]
            )

            base = self.runner.engine.evaluate(case, phase="base")
            variant = self.runner.engine.evaluate(case, phase="variant")

            score = self.runner.evaluator.score(
                case,
                base,
                variant,
                expected_case,
            )

            dimensions = {
                dimension: getattr(score, dimension)
                for dimension in DIMENSIONS
            }

            for dimension, passed in dimensions.items():
                if passed:
                    dimension_pass_counts[dimension] += 1

            case_results.append(
                CaseResult(
                    pair_id=score.pair_id,
                    split=score.split,
                    passed=score.passed,
                    dimensions=dimensions,
                    base=reasoning_snapshot(base),
                    variant=reasoning_snapshot(variant),
                )
            )

        total_cases = len(case_results)
        passed_cases = sum(
            1 for case in case_results if case.passed
        )

        result = EvaluationResult(
            run_id=str(uuid4()),
            evaluation_version="v0.2",
            source="frozen-fixtures",
            status="completed",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            total_cases=total_cases,
            passed_cases=passed_cases,
            dimensions={
                dimension: DimensionResult(
                    passed=dimension_pass_counts[dimension],
                    total=total_cases,
                )
                for dimension in DIMENSIONS
            },
            cases=case_results,
        )

        self._runs[result.run_id] = result
        return result

    def get(self, run_id: str) -> EvaluationResult | None:
        return self._runs.get(run_id)

    def list_runs(self) -> list[EvaluationListItem]:
        return [
            EvaluationListItem(
                run_id=result.run_id,
                evaluation_version=result.evaluation_version,
                source=result.source,
                status=result.status,
                started_at=result.started_at,
                completed_at=result.completed_at,
                total_cases=result.total_cases,
                passed_cases=result.passed_cases,
            )
            for result in reversed(list(self._runs.values()))
        ]
