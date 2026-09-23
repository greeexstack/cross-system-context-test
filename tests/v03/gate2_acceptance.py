from __future__ import annotations

import json
import math
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from experiment.v02.engine import ContextReasoningEngine, EngineConfig
from experiment.v03.clause_local_extractor_v2 import (
    ClauseLocalRelationalEventFrameExtractor,
)
from experiment.v03.event_frame_adapter import frames_to_semantics
from experiment.v03.evidence import (
    EvidenceCondition,
    EvidenceIdentity,
    EvidenceProvenance,
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)

from gate2_acceptance_schema import (
    Gate2Case,
    load_suite,
)


REPO_ROOT = Path(__file__).resolve().parents[2]

V02_FREEZE = "v0.2.0"
V03_FREEZE = "05f8cbf"

V03_CANDIDATE_PATHS = (
    "src/experiment/v03/clause_local_extractor.py",
    "src/experiment/v03/clause_local_extractor_v2.py",
)

DECISION_FIELDS = (
    "interpretation_class",
    "support_level",
    "decision_strength",
    "recommended_focus",
)

EVALUATION_AT = datetime(
    2026,
    9,
    13,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)

STALE_AFTER_DAYS = 30


@dataclass(frozen=True)
class CandidateMeasurement:
    candidate: str
    total_pairs: int
    faithful_pairs: int
    errors: int
    fidelity: float
    negative_control_preserved: int
    negative_control_total: int
    family_results: dict[str, dict[str, Any]]

    @property
    def error_rate(self) -> float:
        return self.errors / self.total_pairs if self.total_pairs else 0.0


@dataclass(frozen=True)
class Gate2AcceptanceResult:
    passed: bool
    reason: str
    v02_errors: int
    v03_errors: int
    maximum_allowed_v03_errors: int | None
    v02_error_rate: float
    v03_error_rate: float
    v02_fidelity: float
    v03_fidelity: float
    v03_negative_control_preserved: int
    v03_negative_control_total: int


def decision_tuple(result: Any) -> tuple[Any, ...]:
    return tuple(
        getattr(result, field)
        for field in DECISION_FIELDS
    )


def _run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _assert_git_reference_exists(reference: str) -> None:
    result = _run_git("rev-parse", "--verify", reference)

    if result.returncode != 0:
        raise RuntimeError(
            f"Git reference {reference!r} is unavailable:\n"
            f"{result.stderr.strip()}"
        )


def _assert_paths_match_reference(
    reference: str,
    paths: tuple[str, ...],
) -> None:
    _assert_git_reference_exists(reference)

    result = _run_git(
        "diff",
        "--quiet",
        reference,
        "--",
        *paths,
    )

    if result.returncode == 0:
        return

    if result.returncode == 1:
        changed = "\n".join(paths)
        raise RuntimeError(
            f"Frozen-source violation: current files differ from "
            f"{reference}:\n{changed}"
        )

    raise RuntimeError(
        f"Could not compare current files with {reference}:\n"
        f"{result.stderr.strip()}"
    )


def verify_frozen_sources() -> None:
    _assert_paths_match_reference(
        V02_FREEZE,
        ("src/experiment/v02",),
    )

    _assert_paths_match_reference(
        V03_FREEZE,
        V03_CANDIDATE_PATHS,
    )


def _v02_primary_record(case: Gate2Case) -> dict[str, Any]:
    return dict(case.primary)


def _v02_customer(case: Gate2Case) -> dict[str, Any]:
    return dict(case.customer)


def _v02_communications(case: Gate2Case) -> tuple[
    dict[str, Any],
    ...,
]:
    communications: list[dict[str, Any]] = []

    for index, text in enumerate(case.texts):
        communications.append(
            {
                "communication_id": (
                    f"G2-{case.case_id}-TEXT-{index}"
                ),
                "customer_id": case.customer["customer_id"],
                "direction": "inbound",
                "channel": "email",
                "occurred_at": case.occurred_at,
                "subject": "Independent Gate-2 evaluation",
                "summary": text,
            }
        )

    return tuple(communications)


def _v02_engine(case: Gate2Case) -> ContextReasoningEngine:
    engine = ContextReasoningEngine(
        EngineConfig(
            stale_after_days=STALE_AFTER_DAYS,
        )
    )

    primary = _v02_primary_record(case)

    opportunity = {
        "opportunity_id": primary["record_id"],
        "customer_id": primary["customer_id"],
    }

    engine.initialize_indexes(
        [_v02_customer(case)],
        [opportunity],
        list(_v02_communications(case)),
        EVALUATION_AT.isoformat(),
    )

    return engine


def _v02_case_payload(
    case: Gate2Case,
    text_index: int,
) -> dict[str, Any]:
    communication_id = (
        f"G2-{case.case_id}-TEXT-{text_index}"
    )

    return {
        "pair_id": (
            f"G2-{case.case_id}-{text_index}"
        ),
        "family_id": case.role,
        "primary": _v02_primary_record(case),
        "base": {
            "secondary_evidence": [],
            "secondary_source_status": "available",
        },
        "variant_case": {
            "secondary_evidence": [communication_id],
            "secondary_source_status": "available",
        },
    }


def _measure_v02_case(
    case: Gate2Case,
) -> tuple[
    tuple[Any, ...],
    tuple[Any, ...],
    tuple[tuple[Any, ...], ...],
]:
    engine = _v02_engine(case)

    base_scenario = _v02_case_payload(case, 0)

    base_result = engine.evaluate(
        base_scenario,
        phase="base",
    )

    primary_only_state = decision_tuple(base_result)

    all_states: list[tuple[Any, ...]] = []

    for index in range(len(case.texts)):
        scenario = _v02_case_payload(case, index)

        result = engine.evaluate(
            scenario,
            phase="variant",
        )

        all_states.append(decision_tuple(result))

    return (
        primary_only_state,
        all_states[0],
        tuple(all_states[1:]),
    )
def _v03_primary(case: Gate2Case) -> PrimaryState:
    return PrimaryState(
        interpretation_class=case.primary_state[
            "interpretation_class"
        ],
        decision_strength=case.primary_state[
            "decision_strength"
        ],
    )


def _v03_reasoner() -> V03Reasoner:
    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=STALE_AFTER_DAYS,
        )
    )


def _v03_case_evaluator(
    case: Gate2Case,
) -> tuple[
    tuple[Any, ...],
    tuple[Any, ...],
    tuple[tuple[Any, ...], ...],
]:
    extractor = ClauseLocalRelationalEventFrameExtractor()
    reasoner = _v03_reasoner()
    primary = _v03_primary(case)

    base_result = reasoner.evaluate(
        primary,
        EvidenceCondition(
            availability="available",
            items=(),
        ),
    )

    primary_only_state = decision_tuple(base_result)

    all_states: list[tuple[Any, ...]] = []

    for index, text in enumerate(case.texts):
        frames = extractor.extract(
            content=text,
        ).frames

        semantics = frames_to_semantics(frames)

        evidence_id = f"G2-{case.case_id}-TEXT-{index}"

        evidence = SemanticEvidence(
            evidence_id=evidence_id,
            content=text,
            provenance=EvidenceProvenance(
                source_system="gate2_acceptance",
                record_id=evidence_id,
                occurred_at=datetime.fromisoformat(
                    case.occurred_at.replace(
                        "Z",
                        "+00:00",
                    )
                ),
            ),
            identity=EvidenceIdentity(
                customer_id=case.customer["customer_id"],
                quality=IdentityQuality.CONFIRMED,
            ),
            semantics=semantics,
        )

        result = reasoner.evaluate(
            primary,
            EvidenceCondition(
                availability="available",
                items=(evidence,),
            ),
        )

        all_states.append(decision_tuple(result))

    return (
        primary_only_state,
        all_states[0],
        tuple(all_states[1:]),
    )

def _measure_candidate(
    candidate_name: str,
    cases: tuple[Gate2Case, ...],
    evaluator: Callable[
        [Gate2Case],
        tuple[
            tuple[Any, ...],
            tuple[Any, ...],
            tuple[tuple[Any, ...], ...],
        ],
    ],
) -> CandidateMeasurement:
    total_pairs = 0
    faithful_pairs = 0
    negative_control_preserved = 0
    negative_control_total = 0

    family_results: dict[str, dict[str, Any]] = {}

    for case in cases:
        (
            primary_only_state,
            original_state,
            variant_states,
        ) = evaluator(case)

        faithful = [
            state == original_state
            for state in variant_states
        ]

        faithful_count = sum(faithful)

        total_pairs += len(variant_states)
        faithful_pairs += faithful_count

        if case.role == "irrelevant":
            negative_control_total += len(variant_states)
            negative_control_preserved += sum(
                state == primary_only_state
                for state in variant_states
            )

        family_results[case.case_id] = {
            "role": case.role,
            "primary_only_state": primary_only_state,
            "original_state": original_state,
            "variant_states": list(variant_states),
            "faithful_pairs": faithful_count,
            "total_pairs": len(variant_states),
        }

    return CandidateMeasurement(
        candidate=candidate_name,
        total_pairs=total_pairs,
        faithful_pairs=faithful_pairs,
        errors=total_pairs - faithful_pairs,
        fidelity=(
            faithful_pairs / total_pairs
            if total_pairs
            else 0.0
        ),
        negative_control_preserved=negative_control_preserved,
        negative_control_total=negative_control_total,
        family_results=family_results,
    )

def measure_suite(
    cases: tuple[Gate2Case, ...],
) -> tuple[
    CandidateMeasurement,
    CandidateMeasurement,
]:
    verify_frozen_sources()

    v02 = _measure_candidate(
        "v0.2",
        cases,
        _measure_v02_case,
    )

    v03 = _measure_candidate(
        "v0.3-clause-local-v2",
        cases,
        _v03_case_evaluator,
    )

    return v02, v03


def assess_gate2(
    v02: CandidateMeasurement,
    v03: CandidateMeasurement,
) -> Gate2AcceptanceResult:
    if v02.errors == 0:
        return Gate2AcceptanceResult(
            passed=False,
            reason=(
                "Gate 2 not demonstrated: frozen v0.2 produced "
                "zero paraphrase errors on the fresh fixture, so "
                "a relative error reduction cannot be demonstrated."
            ),
            v02_errors=v02.errors,
            v03_errors=v03.errors,
            maximum_allowed_v03_errors=None,
            v02_error_rate=v02.error_rate,
            v03_error_rate=v03.error_rate,
            v02_fidelity=v02.fidelity,
            v03_fidelity=v03.fidelity,
            v03_negative_control_preserved=(
                v03.negative_control_preserved
            ),
            v03_negative_control_total=(
                v03.negative_control_total
            ),
        )

    maximum_allowed_v03_errors = math.floor(
        v02.errors / 2
    )

    improvement_ok = (
        v03.errors <= maximum_allowed_v03_errors
    )

    if not improvement_ok:
        reason = (
            f"Gate 2 failed: v0.2 produced {v02.errors} "
            f"errors, so v0.3 may have at most "
            f"{maximum_allowed_v03_errors}; "
            f"v0.3 produced {v03.errors}."
        )
    else:
        reason = (
            "Gate 2 passed under the frozen acceptance protocol."
        )

    return Gate2AcceptanceResult(
        passed=improvement_ok,
        reason=reason,
        v02_errors=v02.errors,
        v03_errors=v03.errors,
        maximum_allowed_v03_errors=(
            maximum_allowed_v03_errors
        ),
        v02_error_rate=v02.error_rate,
        v03_error_rate=v03.error_rate,
        v02_fidelity=v02.fidelity,
        v03_fidelity=v03.fidelity,
        v03_negative_control_preserved=(
            v03.negative_control_preserved
        ),
        v03_negative_control_total=(
            v03.negative_control_total
        ),
    )


def run_acceptance(
    fixture_path: str | Path,
) -> dict[str, Any]:
    cases = load_suite(fixture_path)

    v02, v03 = measure_suite(cases)
    verdict = assess_gate2(v02, v03)

    return {
        "protocol": {
            "gate": "Gate 2 — Paraphrase robustness",
            "v02_freeze": V02_FREEZE,
            "v03_freeze": V03_FREEZE,
            "v03_candidate": (
                "ClauseLocalRelationalEventFrameExtractor"
            ),
            "decision_tuple": list(DECISION_FIELDS),
            "material_improvement_rule": (
                "E3 <= floor(E2 / 2)"
            ),
            "zero_error_baseline": (
                "Gate 2 not demonstrated"
            ),
        },
        "fixture": {
            "path": str(fixture_path),
            "cases": len(cases),
            "pairs": sum(
                len(case.texts) - 1
                for case in cases
            ),
        },
        "v0.2": asdict(v02),
        "v0.3": asdict(v03),
        "verdict": asdict(verdict),
    }


def write_result(
    result: dict[str, Any],
    path: str | Path,
) -> None:
    Path(path).write_text(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Run the frozen Gate-2 v0.2 versus clause-local-v2 "
            "acceptance evaluation."
        )
    )
    parser.add_argument(
        "--fixture",
        required=True,
        help="Path to the independently authored Gate-2 fixture JSON.",
    )
    parser.add_argument(
        "--json-out",
        help="Optional path for the machine-readable result.",
    )

    args = parser.parse_args()

    result = run_acceptance(args.fixture)

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )

    if args.json_out:
        write_result(
            result,
            args.json_out,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())