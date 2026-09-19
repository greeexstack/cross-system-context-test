from __future__ import annotations

from datetime import datetime

from experiment.v03.event_frame_adapter import frames_to_semantics
from experiment.v03.event_frames import CanonicalEventFrameExtractor
from experiment.v03.clause_local_extractor_v2 import (
    ClauseLocalRelationalEventFrameExtractor,
)
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

from test_event_frame_holdout import HOLDOUT
from test_independent_paraphrase_battery import EVALUATION_AT


V1_NAME = "event_frame_v1"
V2_NAME = "clause_local_v2"


def _extract_v1(text: str):
    return CanonicalEventFrameExtractor().extract(
        content=text,
    )


def _extract_v2(text: str):
    return ClauseLocalRelationalEventFrameExtractor().extract(
        content=text,
    )


def _core_facts(frames) -> set[str]:
    facts: set[str] = set()

    for frame in frames:
        if (
            frame.action == "request"
            and frame.object == "followup_conversation"
            and frame.state == "requested"
            and frame.polarity.value == "positive"
        ):
            facts.add("followup_request")

        if (
            frame.action == "confirm"
            and frame.object == "quote"
            and frame.state == "budget_approved"
            and frame.polarity.value == "positive"
        ):
            facts.add("budget_approved")

        if (
            frame.action == "report"
            and frame.object == "procurement"
            and frame.state == "progressing"
            and frame.polarity.value == "positive"
        ):
            facts.add("procurement_progressing")

        if (
            frame.action == "accept"
            and frame.object == "commercial_terms"
            and frame.state == "rejected"
            and frame.polarity.value == "negative"
        ):
            facts.add("commercial_terms_rejected")

        if (
            frame.action == "confirm"
            and frame.object == "service"
            and frame.state == "completed"
            and frame.polarity.value == "positive"
        ):
            facts.add("service_completed")

        if (
            frame.action == "request"
            and frame.object in {"handoff", "next_step"}
            and frame.state == "next_step"
            and frame.polarity.value == "positive"
        ):
            facts.add("next_step_requested")

        if frame.relevance == "different_work_item":
            facts.add("different_work_item")

    return facts


def _behavior(
    primary: PrimaryState,
    text: str,
    frames,
) -> tuple:
    semantics = frames_to_semantics(frames)

    evidence = SemanticEvidence(
        evidence_id="HOLDOUT",
        content=text,
        provenance=EvidenceProvenance(
            source_system="holdout_comparison",
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


def _candidate_data(
    candidate: str,
    primary: PrimaryState,
    text: str,
):
    if candidate == V1_NAME:
        frames = _extract_v1(text).frames
    elif candidate == V2_NAME:
        frames = _extract_v2(text).frames
    else:
        raise ValueError(
            f"Unknown candidate: {candidate}"
        )

    return (
        _core_facts(frames),
        _behavior(primary, text, frames),
    )


def _measure_factual_accuracy(candidate: str) -> dict[str, object]:
    total = 0
    exact = 0
    partial = 0
    missed = 0
    false_positive_variants = 0

    family_results: dict[str, dict[str, int]] = {}

    for family_id, primary, texts, expected_facts in HOLDOUT:
        family_complete = 0
        family_partial = 0
        family_missed = 0

        for text in texts:
            total += 1

            observed, _behavior_state = _candidate_data(
                candidate,
                primary,
                text,
            )

            missing = expected_facts - observed
            extra = observed - expected_facts

            if not missing and not extra:
                exact += 1
                family_complete += 1
            elif expected_facts.intersection(observed) and not extra:
                partial += 1
                family_partial += 1
            else:
                missed += 1
                family_missed += 1

            if extra:
                false_positive_variants += 1

            print(
                {
                    "candidate": candidate,
                    "family": family_id,
                    "text": text,
                    "expected": sorted(expected_facts),
                    "observed": sorted(observed),
                    "missing": sorted(missing),
                    "extra": sorted(extra),
                    "exact": not missing and not extra,
                }
            )

        family_results[family_id] = {
            "complete": family_complete,
            "partial": family_partial,
            "missed": family_missed,
        }

    return {
        "candidate": candidate,
        "total_variants": total,
        "exact_variants": exact,
        "partial_variants": partial,
        "non_exact_variants": missed,
        "exact_rate": exact / total,
        "false_positive_variants": false_positive_variants,
        "family_results": family_results,
    }


def _measure_behavior(candidate: str) -> dict[str, object]:
    total_pairs = 0
    consistent_pairs = 0
    inconsistent_pairs = 0

    by_family: dict[str, dict[str, int]] = {}

    for family_id, primary, texts, _expected_facts in HOLDOUT:
        baseline_facts, baseline_behavior = _candidate_data(
            candidate,
            primary,
            texts[0],
        )

        del baseline_facts

        family_consistent = 0
        family_inconsistent = 0

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            total_pairs += 1

            _facts, variant_behavior = _candidate_data(
                candidate,
                primary,
                text,
            )

            consistent = variant_behavior == baseline_behavior

            if consistent:
                consistent_pairs += 1
                family_consistent += 1
            else:
                inconsistent_pairs += 1
                family_inconsistent += 1

            print(
                {
                    "candidate": candidate,
                    "family": family_id,
                    "variant": variant_index,
                    "consistent": consistent,
                    "baseline": baseline_behavior,
                    "variant_behavior": variant_behavior,
                }
            )

        by_family[family_id] = {
            "consistent": family_consistent,
            "inconsistent": family_inconsistent,
        }

    return {
        "candidate": candidate,
        "total_pairs": total_pairs,
        "consistent_pairs": consistent_pairs,
        "inconsistent_pairs": inconsistent_pairs,
        "behavioral_consistency": (
            consistent_pairs / total_pairs
        ),
        "family_results": by_family,
    }


def _measure_negative_control(candidate: str) -> dict[str, object]:
    family = next(
        item
        for item in HOLDOUT
        if item[0] == "H4-irrelevant"
    )

    family_id, primary, texts, _expected_facts = family

    states = [
        _candidate_data(
            candidate,
            primary,
            text,
        )[1]
        for text in texts
    ]

    consistent_pairs = sum(
        state == states[0]
        for state in states[1:]
    )

    return {
        "candidate": candidate,
        "family": family_id,
        "pairs": 3,
        "consistent_pairs": consistent_pairs,
        "consistency_rate": consistent_pairs / 3,
    }


def test_holdout_v1_vs_v2_factual_accuracy() -> None:
    v1 = _measure_factual_accuracy(V1_NAME)
    v2 = _measure_factual_accuracy(V2_NAME)

    print("\n=== HOLDOUT FACTUAL ACCURACY COMPARISON ===")
    print(v1)
    print(v2)

    print(
        {
            "metric": "exact_rate",
            "v1": v1["exact_rate"],
            "v2": v2["exact_rate"],
            "v2_minus_v1": (
                v2["exact_rate"]
                - v1["exact_rate"]
            ),
        }
    )

    assert v1["total_variants"] == 20
    assert v2["total_variants"] == 20


def test_holdout_v1_vs_v2_behavioral_consistency() -> None:
    print("\n=== HOLDOUT BEHAVIORAL COMPARISON ===")

    v1 = _measure_behavior(V1_NAME)
    v2 = _measure_behavior(V2_NAME)

    print(v1)
    print(v2)

    print(
        {
            "metric": "behavioral_consistency",
            "v1": v1["behavioral_consistency"],
            "v2": v2["behavioral_consistency"],
            "v2_minus_v1": (
                v2["behavioral_consistency"]
                - v1["behavioral_consistency"]
            ),
        }
    )

    assert v1["total_pairs"] == 15
    assert v2["total_pairs"] == 15


def test_holdout_v1_vs_v2_negative_control() -> None:
    v1 = _measure_negative_control(V1_NAME)
    v2 = _measure_negative_control(V2_NAME)

    print("\n=== HOLDOUT NEGATIVE CONTROL COMPARISON ===")
    print(v1)
    print(v2)

    print(
        {
            "metric": "H4_consistency",
            "v1": v1["consistency_rate"],
            "v2": v2["consistency_rate"],
            "v2_minus_v1": (
                v2["consistency_rate"]
                - v1["consistency_rate"]
            ),
        }
    )

    assert v1["pairs"] == 3
    assert v2["pairs"] == 3


def test_holdout_comparison_runs_are_deterministic() -> None:
    factual_v1_a = _measure_factual_accuracy(V1_NAME)
    factual_v1_b = _measure_factual_accuracy(V1_NAME)

    factual_v2_a = _measure_factual_accuracy(V2_NAME)
    factual_v2_b = _measure_factual_accuracy(V2_NAME)

    assert factual_v1_a == factual_v1_b
    assert factual_v2_a == factual_v2_b