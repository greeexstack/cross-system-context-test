from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from experiment.v03.event_frame_adapter import frames_to_semantics
from experiment.v03.evidence import (
    EvidenceCondition,
    EvidenceIdentity,
    EvidenceProvenance,
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)

from test_event_frame_holdout import HOLDOUT, _extract
from test_independent_paraphrase_battery import EVALUATION_AT


TARGET_FIELDS = (
    "requests_followup",
    "confirms_approval",
    "expresses_rejection",
    "confirms_completion",
    "requests_next_step",
    "concerns_same_work_item",
)


# Only facts explicitly represented by the holdout expectations are used.
# "expresses_acceptance" is deliberately excluded because the holdout
# does not independently establish that fact as distinct from approval.
FAMILY_SEMANTIC_TRUTH: dict[str, dict[str, bool]] = {
    "H1-followup": {
        "requests_followup": True,
        "concerns_same_work_item": True,
    },
    "H2-supporting": {
        "confirms_approval": True,
        "concerns_same_work_item": True,
    },
    "H3-contradictory": {
        "expresses_rejection": True,
        "concerns_same_work_item": True,
    },
    "H4-irrelevant": {
        "concerns_same_work_item": False,
    },
    "H5-service-next-step": {
        "confirms_completion": True,
        "requests_next_step": True,
        "concerns_same_work_item": True,
    },
}


def _truth_for_family(
    family_id: str,
    field: str,
) -> bool:
    return FAMILY_SEMANTIC_TRUTH[family_id].get(field, False)


def _behavior_from_semantics(
    primary: PrimaryState,
    text: str,
    semantics: EvidenceSemantics,
) -> tuple:
    evidence = SemanticEvidence(
        evidence_id="HOLDOUT",
        content=text,
        provenance=EvidenceProvenance(
            source_system="event_frame_holdout",
            record_id="HOLDOUT",
            occurred_at=datetime.fromisoformat(
                "2026-09-12T10:00:00+00:00"
            ),
        ),
        identity=EvidenceIdentity(
            customer_id="HOLDOUT-CUSTOMER",
            quality=IdentityQuality.CONFIRMED,
        ),
        semantics=semantics,
    )

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


def _candidate_semantics(text: str) -> EvidenceSemantics:
    return frames_to_semantics(
        _extract(text).frames,
    )


def _candidate_behavior(
    primary: PrimaryState,
    text: str,
) -> tuple:
    return _behavior_from_semantics(
        primary,
        text,
        _candidate_semantics(text),
    )


def _repaired_behavior(
    family_id: str,
    primary: PrimaryState,
    text: str,
    repaired_fields: tuple[str, ...],
) -> tuple:
    semantics = _candidate_semantics(text)

    updates = {
        field: _truth_for_family(family_id, field)
        for field in repaired_fields
    }

    repaired = replace(
        semantics,
        **updates,
    )

    return _behavior_from_semantics(
        primary,
        text,
        repaired,
    )


def _measure_candidate() -> dict[tuple[str, int], bool]:
    consistency: dict[tuple[str, int], bool] = {}

    for family_id, primary, texts, _expected_facts in HOLDOUT:
        baseline = _candidate_behavior(
            primary,
            texts[0],
        )

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            variant = _candidate_behavior(
                primary,
                text,
            )

            consistency[
                (family_id, variant_index)
            ] = variant == baseline

    return consistency


def _measure_field(
    field: str,
) -> dict[str, object]:
    candidate_consistency = _measure_candidate()

    repaired_consistency: dict[tuple[str, int], bool] = {}

    for family_id, primary, texts, _expected_facts in HOLDOUT:
        baseline = _repaired_behavior(
            family_id,
            primary,
            texts[0],
            (field,),
        )

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            variant = _repaired_behavior(
                family_id,
                primary,
                text,
                (field,),
            )

            repaired_consistency[
                (family_id, variant_index)
            ] = variant == baseline

    candidate_failures = {
        pair
        for pair, consistent in candidate_consistency.items()
        if not consistent
    }

    candidate_successes = {
        pair
        for pair, consistent in candidate_consistency.items()
        if consistent
    }

    repaired_failures = {
        pair
        for pair, consistent in repaired_consistency.items()
        if not consistent
    }

    repaired_successes = {
        pair
        for pair, consistent in repaired_consistency.items()
        if consistent
    }

    genuine_repairs = (
        candidate_failures
        & repaired_successes
    )

    regressions = (
        candidate_successes
        & repaired_failures
    )

    unchanged_failures = (
        candidate_failures
        & repaired_failures
    )

    unchanged_successes = (
        candidate_successes
        & repaired_successes
    )

    return {
        "field": field,
        "candidate_pbc": (
            sum(candidate_consistency.values())
            / len(candidate_consistency)
        ),
        "repaired_pbc": (
            sum(repaired_consistency.values())
            / len(repaired_consistency)
        ),
        "candidate_failures": len(candidate_failures),
        "genuine_repairs": len(genuine_repairs),
        "regressions": len(regressions),
        "unchanged_failures": len(unchanged_failures),
        "unchanged_successes": len(unchanged_successes),
        "genuine_repair_pairs": sorted(genuine_repairs),
        "regression_pairs": sorted(regressions),
        "remaining_failure_pairs": sorted(unchanged_failures),
    }


def _measure_full_oracle() -> dict[str, object]:
    candidate_consistency = _measure_candidate()

    repaired_consistency: dict[tuple[str, int], bool] = {}

    for family_id, primary, texts, _expected_facts in HOLDOUT:
        baseline = _repaired_behavior(
            family_id,
            primary,
            texts[0],
            TARGET_FIELDS,
        )

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            variant = _repaired_behavior(
                family_id,
                primary,
                text,
                TARGET_FIELDS,
            )

            repaired_consistency[
                (family_id, variant_index)
            ] = variant == baseline

    candidate_failures = {
        pair
        for pair, consistent in candidate_consistency.items()
        if not consistent
    }

    repaired_successes = {
        pair
        for pair, consistent in repaired_consistency.items()
        if consistent
    }

    repaired_failures = {
        pair
        for pair, consistent in repaired_consistency.items()
        if not consistent
    }

    return {
        "candidate_pbc": (
            sum(candidate_consistency.values())
            / len(candidate_consistency)
        ),
        "oracle_pbc": (
            sum(repaired_consistency.values())
            / len(repaired_consistency)
        ),
        "genuine_repairs": len(
            candidate_failures & repaired_successes
        ),
        "remaining_failures": len(repaired_failures),
        "genuine_repair_pairs": sorted(
            candidate_failures & repaired_successes
        ),
    }


def test_holdout_counterfactual_field_repairs() -> None:
    candidate_consistency = _measure_candidate()

    assert len(candidate_consistency) == 15
    assert sum(candidate_consistency.values()) == 8

    print("\n=== CORRECTED HOLDOUT COUNTERFACTUAL FIELD REPAIR ===")
    print(
        {
            "candidate_pairs": 15,
            "candidate_consistent_pairs": sum(
                candidate_consistency.values()
            ),
            "candidate_pbc": (
                sum(candidate_consistency.values())
                / 15
            ),
        }
    )

    for field in TARGET_FIELDS:
        result = _measure_field(field)

        print(result)

        assert result["candidate_failures"] == 7
        assert (
            result["genuine_repairs"]
            + result["unchanged_failures"]
            == 7
        )
        assert (
            result["genuine_repairs"]
            + result["regressions"]
            + result["unchanged_failures"]
            + result["unchanged_successes"]
            == 15
        )

    oracle = _measure_full_oracle()

    print("\n=== FULL SEMANTIC ORACLE ===")
    print(oracle)

    assert oracle["oracle_pbc"] == 1.0
    assert oracle["remaining_failures"] == 0
    assert oracle["genuine_repairs"] == 7


def test_holdout_counterfactual_field_repair_matrix_is_deterministic() -> None:
    first = [
        _measure_field(field)
        for field in TARGET_FIELDS
    ]

    second = [
        _measure_field(field)
        for field in TARGET_FIELDS
    ]

    assert first == second