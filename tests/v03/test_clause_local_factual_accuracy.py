from __future__ import annotations

from experiment.v03.clause_local_extractor import (
    ClauseLocalEventFrameExtractor,
)

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


def test_clause_local_development_exact_fact_accuracy() -> None:
    total = 0
    exact = 0
    partial = 0
    missed = 0
    false_positive_variants = 0

    print("\n=== CLAUSE-LOCAL DEVELOPMENT FACTUAL ACCURACY ===")

    for family_id, _primary_state, variants in DEVELOPMENT_BATTERY:
        for variant_index, (text, expected_facts) in enumerate(
            variants,
            start=0,
        ):
            total += 1

            observed = _core_facts(
                _extract(text).frames,
            )

            extra = observed - expected_facts
            missing = expected_facts - observed

            if not missing and not extra:
                exact += 1
            elif expected_facts.intersection(observed) and not extra:
                partial += 1
            else:
                missed += 1

            if extra:
                false_positive_variants += 1

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "expected": sorted(expected_facts),
                    "observed": sorted(observed),
                    "missing": sorted(missing),
                    "extra": sorted(extra),
                    "exact": not missing and not extra,
                }
            )

    print(
        {
            "total_variants": total,
            "exact_variants": exact,
            "partial_variants": partial,
            "non_exact_variants": missed,
            "exact_rate": exact / total,
            "false_positive_variants": false_positive_variants,
        }
    )

    assert total == 20
    assert exact + partial + missed == total


def test_clause_local_development_family_recall() -> None:
    family_results: dict[str, dict[str, int]] = {}

    print("\n=== CLAUSE-LOCAL DEVELOPMENT FAMILY RECALL ===")

    for family_id, _primary_state, variants in DEVELOPMENT_BATTERY:
        complete = 0
        partial = 0
        missed = 0

        for text, expected_facts in variants:
            observed = _core_facts(
                _extract(text).frames,
            )

            if expected_facts.issubset(observed):
                complete += 1
            elif expected_facts.intersection(observed):
                partial += 1
            else:
                missed += 1

        family_results[family_id] = {
            "complete": complete,
            "partial": partial,
            "missed": missed,
        }

        print(
            {
                "family": family_id,
                "complete": complete,
                "partial": partial,
                "missed": missed,
            }
        )

    assert set(family_results) == {
        "D1-followup",
        "D2-supporting",
        "D3-contradictory",
        "D4-irrelevant",
        "D5-service-next-step",
    }


def test_clause_local_irrelevant_negative_control_is_factually_clean() -> None:
    variants = next(
        variants
        for family_id, _primary_state, variants in DEVELOPMENT_BATTERY
        if family_id == "D4-irrelevant"
    )

    print("\n=== CLAUSE-LOCAL NEGATIVE CONTROL FACTUAL CHECK ===")

    unexpected = []

    for variant_index, (text, expected_facts) in enumerate(
        variants,
        start=0,
    ):
        observed = _core_facts(
            _extract(text).frames,
        )

        extra = observed - expected_facts

        print(
            {
                "variant": variant_index,
                "expected": sorted(expected_facts),
                "observed": sorted(observed),
                "extra": sorted(extra),
            }
        )

        if extra:
            unexpected.append(
                (
                    variant_index,
                    sorted(extra),
                )
            )

    print(
        {
            "variants": 4,
            "variants_with_unexpected_facts": len(unexpected),
            "unexpected": unexpected,
        }
    )

    assert len(unexpected) >= 0