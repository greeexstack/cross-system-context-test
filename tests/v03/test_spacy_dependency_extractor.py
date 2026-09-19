from __future__ import annotations

from experiment.v03.spacy_dependency_extractor import (
    SpacyDependencyEventFrameExtractor,
)

from test_clause_local_construction_battery import (
    CONSTRUCTION_BATTERY,
)


def _extract(text: str):
    return SpacyDependencyEventFrameExtractor().extract(
        content=text,
    )


def _core_facts(frames) -> set[str]:
    facts: set[str] = set()

    for frame in frames:
        if (
            frame.action == "request"
            and frame.object == "followup_conversation"
            and frame.state == "requested"
        ):
            facts.add("followup_request")

        if (
            frame.action == "confirm"
            and frame.object == "quote"
            and frame.state == "budget_approved"
        ):
            facts.add("budget_approved")

        if (
            frame.action == "report"
            and frame.object == "procurement"
            and frame.state == "progressing"
        ):
            facts.add("procurement_progressing")

        if (
            frame.action == "accept"
            and frame.object == "commercial_terms"
            and frame.state == "rejected"
        ):
            facts.add("commercial_terms_rejected")

        if (
            frame.action == "confirm"
            and frame.object == "service"
            and frame.state == "completed"
        ):
            facts.add("service_completed")

        if (
            frame.action == "request"
            and frame.object in {"handoff", "next_step"}
            and frame.state == "next_step"
        ):
            facts.add("next_step_requested")

        if frame.relevance == "different_work_item":
            facts.add("different_work_item")

    return facts


def test_spacy_dependency_construction_accuracy() -> None:
    total = 0
    exact = 0
    partial = 0
    missed = 0
    false_positive_variants = 0

    print("\n=== SPACY DEPENDENCY CONSTRUCTION ACCURACY ===")

    for family_id, _primary_state, variants in CONSTRUCTION_BATTERY:
        for variant_index, (text, expected_facts) in enumerate(
            variants,
            start=0,
        ):
            total += 1

            observed = _core_facts(
                _extract(text).frames,
            )

            missing = expected_facts - observed
            extra = observed - expected_facts

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
            "missed_variants": missed,
            "exact_rate": exact / total,
            "false_positive_variants": false_positive_variants,
        }
    )

    assert total == 12
    assert exact + partial + missed == total


def test_spacy_dependency_construction_has_no_false_positive_facts() -> None:
    unexpected = []

    for family_id, _primary_state, variants in CONSTRUCTION_BATTERY:
        for variant_index, (text, expected_facts) in enumerate(
            variants,
            start=0,
        ):
            observed = _core_facts(
                _extract(text).frames,
            )

            extra = observed - expected_facts

            if extra:
                unexpected.append(
                    {
                        "family": family_id,
                        "variant": variant_index,
                        "extra": sorted(extra),
                    }
                )

    print("\n=== SPACY DEPENDENCY FALSE POSITIVE CHECK ===")
    print(
        {
            "unexpected_variants": len(unexpected),
            "details": unexpected,
        }
    )

    assert not unexpected
