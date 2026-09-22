from __future__ import annotations

from datetime import datetime

from experiment.v03.clause_local_extractor_v2 import (
    ClauseLocalRelationalEventFrameExtractor,
)
from experiment.v03.event_frame_adapter import frames_to_semantics
from experiment.v03.event_frames import CanonicalEventFrameExtractor
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

from test_fresh_holdout import FRESH_HOLDOUT, FreshHoldoutCase
from test_independent_paraphrase_battery import EVALUATION_AT


V1 = "event_frame_v1"
V2 = "clause_local_v2"

HOLDOUT_AT = datetime.fromisoformat("2026-09-12T10:00:00+00:00")


def _extract_v1(text: str):
    return CanonicalEventFrameExtractor().extract(
        content=text,
    )


def _extract_v2(text: str):
    return ClauseLocalRelationalEventFrameExtractor().extract(
        content=text,
    )


def _oracle_semantics(case: FreshHoldoutCase) -> EvidenceSemantics:
    values = {
        "topic": None,
        "requests_followup": None,
        "expresses_acceptance": None,
        "expresses_rejection": None,
        "confirms_approval": None,
        "confirms_completion": None,
        "requests_next_step": None,
        "concerns_same_work_item": None,
    }

    for field, value in case.expected_fields:
        values[field] = value

    return EvidenceSemantics(**values)


def _evaluate(
    case: FreshHoldoutCase,
    text: str,
    semantics: EvidenceSemantics,
) -> tuple:
    evidence = SemanticEvidence(
        evidence_id=f"FRESH-{case.family_id}",
        content=text,
        provenance=EvidenceProvenance(
            source_system="fresh_holdout_decision_fidelity",
            record_id=f"FRESH-{case.family_id}",
            occurred_at=HOLDOUT_AT,
        ),
        identity=EvidenceIdentity(
            customer_id="FRESH-HOLDOUT-CUSTOMER",
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
        PrimaryState(
            case.primary_interpretation,
            case.primary_decision_strength,
        ),
        condition,
    )

    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def _candidate_semantics(
    candidate: str,
    text: str,
) -> EvidenceSemantics:
    if candidate == V1:
        frames = _extract_v1(text).frames
    elif candidate == V2:
        frames = _extract_v2(text).frames
    else:
        raise ValueError(candidate)

    return frames_to_semantics(frames)


def _oracle_behavior(
    case: FreshHoldoutCase,
    text: str,
) -> tuple:
    return _evaluate(
        case,
        text,
        _oracle_semantics(case),
    )


def _candidate_behavior(
    candidate: str,
    case: FreshHoldoutCase,
    text: str,
) -> tuple:
    return _evaluate(
        case,
        text,
        _candidate_semantics(candidate, text),
    )


def _measure_decision_fidelity(
    candidate: str,
) -> dict[str, object]:
    total = 0
    exact = 0
    family_results: dict[str, dict[str, int]] = {}

    for case in FRESH_HOLDOUT:
        family_exact = 0

        for variant_index, text in enumerate(case.texts):
            expected = _oracle_behavior(case, text)
            observed = _candidate_behavior(candidate, case, text)
            matches = observed == expected

            total += 1

            if matches:
                exact += 1
                family_exact += 1

            print(
                {
                    "candidate": candidate,
                    "family": case.family_id,
                    "variant": variant_index,
                    "expected_decision": expected,
                    "observed_decision": observed,
                    "exact": matches,
                }
            )

        family_results[case.family_id] = {
            "exact": family_exact,
            "total": len(case.texts),
        }

    return {
        "candidate": candidate,
        "total_variants": total,
        "exact_decisions": exact,
        "decision_fidelity": exact / total,
        "family_results": family_results,
    }


def test_fresh_holdout_decision_fidelity_v1_vs_v2() -> None:
    print("\n=== FRESH HOLDOUT DECISION FIDELITY ===")

    v1 = _measure_decision_fidelity(V1)
    v2 = _measure_decision_fidelity(V2)

    print(v1)
    print(v2)

    print(
        {
            "metric": "decision_fidelity",
            "v1": v1["decision_fidelity"],
            "v2": v2["decision_fidelity"],
            "v2_minus_v1": (
                v2["decision_fidelity"]
                - v1["decision_fidelity"]
            ),
        }
    )

    assert v1["total_variants"] == 20
    assert v2["total_variants"] == 20


def test_fresh_holdout_is_measured_per_family() -> None:
    expected_families = {
        "FH1-followup",
        "FH2-supporting",
        "FH3-contradictory",
        "FH4-irrelevant",
        "FH5-service-next-step",
    }

    for candidate in (V1, V2):
        result = _measure_decision_fidelity(candidate)

        assert set(result["family_results"]) == expected_families
        assert sum(
            family["total"]
            for family in result["family_results"].values()
        ) == 20


def test_fresh_holdout_oracle_is_deterministic() -> None:
    first = [
        _oracle_behavior(case, case.texts[0])
        for case in FRESH_HOLDOUT
    ]

    second = [
        _oracle_behavior(case, case.texts[0])
        for case in FRESH_HOLDOUT
    ]

    assert first == second


def test_fresh_holdout_candidate_evaluation_is_deterministic() -> None:
    for candidate in (V1, V2):
        first = [
            _candidate_behavior(candidate, case, text)
            for case in FRESH_HOLDOUT
            for text in case.texts
        ]

        second = [
            _candidate_behavior(candidate, case, text)
            for case in FRESH_HOLDOUT
            for text in case.texts
        ]

        assert first == second