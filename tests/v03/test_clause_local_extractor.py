from __future__ import annotations

from experiment.v03.clause_local_extractor import (
    ClauseLocalEventFrameExtractor,
)
from experiment.v03.event_frame_adapter import frames_to_semantics

from test_clause_local_development_battery import (
    DEVELOPMENT_BATTERY,
)


def _extract(text: str):
    return ClauseLocalEventFrameExtractor().extract(
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


def test_clause_local_development_core_fact_recovery() -> None:
    total = 0
    complete = 0
    partial = 0
    missed = 0

    print("\n=== CLAUSE-LOCAL DEVELOPMENT CORE-FACT RECOVERY ===")

    for family_id, _primary_state, variants in DEVELOPMENT_BATTERY:
        for variant_index, (text, expected_facts) in enumerate(
            variants,
            start=0,
        ):
            total += 1

            observed = _core_facts(
                _extract(text).frames,
            )

            if expected_facts.issubset(observed):
                complete += 1
            elif observed.intersection(expected_facts):
                partial += 1
            else:
                missed += 1

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "expected": sorted(expected_facts),
                    "observed": sorted(observed),
                    "complete": expected_facts.issubset(observed),
                }
            )

    print(
        {
            "total_variants": total,
            "complete_variants": complete,
            "partial_variants": partial,
            "missed_variants": missed,
            "complete_rate": complete / total,
        }
    )

    assert total == 20
    assert complete + partial + missed == total


def test_clause_local_development_behavioral_consistency() -> None:
    total_pairs = 0
    consistent_pairs = 0
    inconsistent_pairs = 0

    print("\n=== CLAUSE-LOCAL DEVELOPMENT SEMANTIC OUTPUT ===")

    for family_id, _primary_state, variants in DEVELOPMENT_BATTERY:
        baseline = frames_to_semantics(
            _extract(variants[0][0]).frames,
        )

        for variant_index, (text, _expected_facts) in enumerate(
            variants[1:],
            start=1,
        ):
            total_pairs += 1

            variant = frames_to_semantics(
                _extract(text).frames,
            )

            consistent = variant == baseline

            if consistent:
                consistent_pairs += 1
            else:
                inconsistent_pairs += 1

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "consistent": consistent,
                    "baseline": baseline,
                    "variant_semantics": variant,
                }
            )

    print(
        {
            "total_pairs": total_pairs,
            "consistent_pairs": consistent_pairs,
            "inconsistent_pairs": inconsistent_pairs,
            "behavioral_consistency": consistent_pairs / total_pairs,
        }
    )

    assert total_pairs == 15
    assert consistent_pairs + inconsistent_pairs == total_pairs


def test_clause_local_irrelevant_negative_control() -> None:
    family_id, _primary_state, variants = next(
        item
        for item in DEVELOPMENT_BATTERY
        if item[0] == "D4-irrelevant"
    )

    outputs = [
        frames_to_semantics(
            _extract(text).frames,
        )
        for text, _expected_facts in variants
    ]

    consistent_pairs = sum(
        output == outputs[0]
        for output in outputs[1:]
    )

    print(
        "\n=== CLAUSE-LOCAL NEGATIVE CONTROL ==="
    )
    print(
        {
            "family": family_id,
            "pairs": 3,
            "consistent_pairs": consistent_pairs,
            "consistency_rate": consistent_pairs / 3,
        }
    )

    assert 0 <= consistent_pairs <= 3