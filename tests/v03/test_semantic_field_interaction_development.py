from __future__ import annotations

from dataclasses import replace
from typing import Any

from experiment.v03.event_frame_adapter import frames_to_semantics
from experiment.v03.event_frames import CanonicalEventFrameExtractor
from experiment.v03.evidence import EvidenceCondition, EvidenceSemantics
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)

from test_independent_paraphrase_battery import EVALUATION_AT
from fixtures.semantic_cases import (
    F01_EQUIVALENT_A,
    F01_EQUIVALENT_B,
    F02_EQUIVALENT_A,
    F02_EQUIVALENT_B,
    F03_EQUIVALENT_A,
    F03_EQUIVALENT_B,
    F10_EQUIVALENT_A,
    F10_EQUIVALENT_B,
)


TARGET_FIELDS = (
    "requests_followup",
    "confirms_approval",
    "expresses_rejection",
    "confirms_completion",
    "requests_next_step",
    "concerns_same_work_item",
)


DEVELOPMENT_PAIRS = (
    (
        "F01",
        PrimaryState("quote_pending_decision"),
        F01_EQUIVALENT_A,
        F01_EQUIVALENT_B,
    ),
    (
        "F02",
        PrimaryState("quote_pending_decision"),
        F02_EQUIVALENT_A,
        F02_EQUIVALENT_B,
    ),
    (
        "F03",
        PrimaryState("negotiation_open"),
        F03_EQUIVALENT_A,
        F03_EQUIVALENT_B,
    ),
    (
        "F10",
        PrimaryState("service_completed_next_step_unrecorded"),
        F10_EQUIVALENT_A,
        F10_EQUIVALENT_B,
    ),
)


def _candidate_semantics(text: str) -> EvidenceSemantics:
    extractor = CanonicalEventFrameExtractor()
    extracted = extractor.extract(content=text)
    return frames_to_semantics(extracted.frames)


def _behavior(
    primary: PrimaryState,
    evidence,
):
    condition = EvidenceCondition(
        availability="available",
        items=(evidence,),
    )

    result = V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    ).evaluate(
        primary,
        condition,
    )

    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def _with_candidate_semantics(evidence, semantics: EvidenceSemantics):
    return replace(
        evidence,
        semantics=semantics,
    )


def _repair(
    candidate: EvidenceSemantics,
    oracle: EvidenceSemantics,
    repaired_fields: tuple[str, ...],
) -> EvidenceSemantics:
    updates: dict[str, Any] = {
        field: getattr(oracle, field)
        for field in repaired_fields
    }

    return replace(
        candidate,
        **updates,
    )


def _eligible_field_pairs(
    oracle: EvidenceSemantics,
) -> tuple[tuple[str, str], ...]:
    explicit_fields = tuple(
        field
        for field in TARGET_FIELDS
        if getattr(oracle, field) is not None
    )

    return tuple(
        (left, right)
        for index, left in enumerate(explicit_fields)
        for right in explicit_fields[index + 1 :]
    )


def _measure_pair(
    *,
    primary: PrimaryState,
    left_evidence,
    right_evidence,
    field_a: str,
    field_b: str,
) -> dict[str, Any]:
    left_candidate = _candidate_semantics(left_evidence.content)
    right_candidate = _candidate_semantics(right_evidence.content)

    oracle = left_evidence.semantics

    left_baseline = _behavior(
        primary,
        _with_candidate_semantics(
            left_evidence,
            left_candidate,
        ),
    )
    right_baseline = _behavior(
        primary,
        _with_candidate_semantics(
            right_evidence,
            right_candidate,
        ),
    )

    left_a = _behavior(
        primary,
        _with_candidate_semantics(
            left_evidence,
            _repair(
                left_candidate,
                oracle,
                (field_a,),
            ),
        ),
    )
    right_a = _behavior(
        primary,
        _with_candidate_semantics(
            right_evidence,
            _repair(
                right_candidate,
                oracle,
                (field_a,),
            ),
        ),
    )

    left_b = _behavior(
        primary,
        _with_candidate_semantics(
            left_evidence,
            _repair(
                left_candidate,
                oracle,
                (field_b,),
            ),
        ),
    )
    right_b = _behavior(
        primary,
        _with_candidate_semantics(
            right_evidence,
            _repair(
                right_candidate,
                oracle,
                (field_b,),
            ),
        ),
    )

    left_ab = _behavior(
        primary,
        _with_candidate_semantics(
            left_evidence,
            _repair(
                left_candidate,
                oracle,
                (field_a, field_b),
            ),
        ),
    )
    right_ab = _behavior(
        primary,
        _with_candidate_semantics(
            right_evidence,
            _repair(
                right_candidate,
                oracle,
                (field_a, field_b),
            ),
        ),
    )

    return {
        "field_a": field_a,
        "field_b": field_b,
        "baseline_consistent": left_baseline == right_baseline,
        "a_consistent": left_a == right_a,
        "b_consistent": left_b == right_b,
        "ab_consistent": left_ab == right_ab,
        "baseline_left": left_baseline,
        "baseline_right": right_baseline,
        "a_left": left_a,
        "a_right": right_a,
        "b_left": left_b,
        "b_right": right_b,
        "ab_left": left_ab,
        "ab_right": right_ab,
    }


def _measure_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for family_id, primary, left, right in DEVELOPMENT_PAIRS:
        for field_a, field_b in _eligible_field_pairs(
            left.semantics
        ):
            measurement = _measure_pair(
                primary=primary,
                left_evidence=left,
                right_evidence=right,
                field_a=field_a,
                field_b=field_b,
            )

            rows.append(
                {
                    "family": family_id,
                    **measurement,
                }
            )

    return rows


def test_development_semantic_field_interaction_matrix() -> None:
    matrix = _measure_matrix()

    print("\n=== DEVELOPMENT SEMANTIC FIELD INTERACTION ===")

    for row in matrix:
        print(row)

    assert matrix
    assert all(
        {
            "family",
            "field_a",
            "field_b",
            "baseline_consistent",
            "a_consistent",
            "b_consistent",
            "ab_consistent",
        }.issubset(row)
        for row in matrix
    )


def test_development_semantic_field_interaction_matrix_is_deterministic() -> None:
    first = _measure_matrix()
    second = _measure_matrix()

    assert first == second