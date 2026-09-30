from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from experiment.v02.engine import (
    ContextReasoningEngine,
    EngineConfig,
    ReasoningResult,
)
from experiment.v02.runner import V02Runner
from .models import (
    CaseResult,
    DimensionResult,
    EvaluationListItem,
    EvaluationResult,
    EvidenceItem,
    ReasoningSnapshot,
    UserEvaluationCreateRequest,
    UserEvaluationResult,
)
from .storage import UserEvaluationStore

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


def reasoning_snapshot(
    result: ReasoningResult,
    evidence_lookup: dict[str, dict],
) -> ReasoningSnapshot:
    evidence = []

    for evidence_id in result.evidence_ids:
        communication = evidence_lookup.get(evidence_id)

        if communication is None:
            continue

        evidence.append(
            EvidenceItem(
                evidence_id=communication["communication_id"],
                channel=communication["channel"],
                direction=communication["direction"],
                occurred_at=communication["occurred_at"],
                subject=communication["subject"],
                summary=communication["summary"],
            )
        )

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
        evidence=evidence,
        evidence_valid=result.evidence_valid,
        notes=list(result.notes),
    )


class EvaluationService:
    def __init__(
    self,
    fixture_root: str | Path,
    user_storage_path: str | Path = ":memory:",
) -> None:
        self.fixture_root = Path(fixture_root)

        # Frozen benchmark runner.
        # This path remains unchanged and continues to execute
        # the validated 20-case v0.2 fixture evaluation.
        self.runner = V02Runner(self.fixture_root)

        self.evidence_lookup = {
            communication["communication_id"]: communication
            for communication in self.runner.communications
        }

        self._runs: dict[str, EvaluationResult] = {}
        self.user_store = UserEvaluationStore(user_storage_path)

    def run_v02(self) -> EvaluationResult:
        started_at = datetime.now(timezone.utc)

        case_results: list[CaseResult] = []
        dimension_pass_counts = {
            dimension: 0
            for dimension in DIMENSIONS
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

            base = self.runner.engine.evaluate(
                case,
                phase="base",
            )

            variant = self.runner.engine.evaluate(
                case,
                phase="variant",
            )

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
                    base=reasoning_snapshot(
                        base,
                        self.evidence_lookup,
                    ),
                    variant=reasoning_snapshot(
                        variant,
                        self.evidence_lookup,
                    ),
                )
            )

        total_cases = len(case_results)

        passed_cases = sum(
            1
            for case in case_results
            if case.passed
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

    def run_user_evaluation(
        self,
        request: UserEvaluationCreateRequest,
    ) -> UserEvaluationResult:
        created_at = datetime.now(timezone.utc)

        primary_record_id = f"USER-PRIMARY-{uuid4().hex[:8]}"
        evidence_id = f"USER-EVIDENCE-{uuid4().hex[:8]}"

        customer_id = "USER-CUSTOMER"
        customer_email = "user-input@example.invalid"

        primary = {
            "record_id": primary_record_id,
            "record_type": request.record_type,
            "summary": request.primary_context,
        }

        secondary_timestamp = created_at.isoformat()

        communication = {
            "communication_id": evidence_id,
            "customer_id": customer_id,
            "channel": "user_input",
            "direction": "inbound",
            "occurred_at": secondary_timestamp,
            "subject": "User supplied context",
            "summary": request.additional_context,
        }

        engine = ContextReasoningEngine(
            EngineConfig(
                stale_after_days=30,
            )
        )

        engine.initialize_indexes(
            customers=[
                {
                    "customer_id": customer_id,
                    "email": customer_email,
                    "phone": None,
                    "name": "User supplied subject",
                }
            ],
            opportunities=[
                {
                    "opportunity_id": primary_record_id,
                    "customer_id": customer_id,
                }
            ],
            communications=[
                communication,
            ],
            evaluation_at=secondary_timestamp,
        )

        base_case = {
            "pair_id": "USER-EVALUATION",
            "primary": primary,
            "base": {
                "secondary_evidence": [],
                "secondary_source_status": "available",
            },
            "variant_case": {
                "secondary_evidence": [
                    {
                        "communication_id": evidence_id,
                    }
                ],
                "secondary_source_status": "available",
                "secondary_identity": {
                    "email": customer_email,
                    "phone": None,
                    "name": "User supplied subject",
                },
            },
        }

        base = engine.evaluate(
            base_case,
            phase="base",
        )

        variant = engine.evaluate(
            base_case,
            phase="variant",
        )

        user_evidence_lookup = {
            evidence_id: communication,
        }

        base_snapshot = reasoning_snapshot(
            base,
            user_evidence_lookup,
        )

        variant_snapshot = reasoning_snapshot(
            variant,
            user_evidence_lookup,
        )

        result = UserEvaluationResult(
            run_id=str(uuid4()),
            created_at=created_at,
            name=request.name.strip(),
            objective=request.objective.strip(),
            workflow=request.workflow.strip(),
            record_type=request.record_type,
            primary_context=request.primary_context.strip(),
            additional_context=request.additional_context.strip(),
            base=base_snapshot,
            variant=variant_snapshot,
            interpretation_changed=(
                base.interpretation_class
                != variant.interpretation_class
            ),
            support_changed=(
                base.support_level
                != variant.support_level
            ),
            decision_strength_changed=(
                base.decision_strength
                != variant.decision_strength
            ),
            assumptions=[
                (
                    "Identity was not supplied by the user; "
                    "the evaluation used an internal synthetic "
                    "matched identity so identity resolution could "
                    "be held constant."
                ),
                (
                    "This is a user-input reasoning result, not a "
                    "benchmark score against frozen ground truth."
                ),
            ],
        )

        self.user_store.save(result)

        return result

    def get(
        self,
        run_id: str,
    ) -> EvaluationResult | None:
        return self._runs.get(run_id)

    def get_user(
        self,
        run_id: str,
    ) -> UserEvaluationResult | None:
        return self.user_store.get(run_id)

    def list_user_evaluations(self) -> list[UserEvaluationResult]:
        return self.user_store.list_all()

    def delete_user_evaluation(
        self,
        run_id: str,
    ) -> bool:
        return self.user_store.delete(run_id)

    def set_user_evaluation_starred(
        self,
        run_id: str,
        starred: bool,
    ) -> UserEvaluationResult | None:
        return self.user_store.set_starred(
            run_id,
            starred,
        )

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
            for result in reversed(
                list(self._runs.values())
            )
        ]