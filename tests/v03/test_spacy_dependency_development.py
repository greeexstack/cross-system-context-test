from __future__ import annotations

from experiment.v03.spacy_dependency_extractor import (
    SpacyDependencyEventFrameExtractor,
)

from test_clause_local_development_battery import (
    DEVELOPMENT_BATTERY,
)


EXTRACTOR = SpacyDependencyEventFrameExtractor()


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


def test_spacy_dependency_existing_development_accuracy() -> None:
    total = 0
    exact = 0
    partial = 0
    missed = 0
    false_positive_variants = 0

    print("\n=== SPACY DEPENDENCY EXISTING DEVELOPMENT ACCURACY ===")

    for family_id, _primary_state, variants in DEVELOPMENT_BATTERY:
        for variant_index, (text, expected_facts) in enumerate(
            variants,
            start=0,
        ):
            total += 1

            observed = _core_facts(
                EXTRACTOR.extract(content=text).frames,
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

    assert total == 20


def test_spacy_dependency_existing_development_negative_control() -> None:
    variants = next(
        variants
        for family_id, _primary_state, variants in DEVELOPMENT_BATTERY
        if family_id == "D4-irrelevant"
    )

    print("\n=== SPACY DEPENDENCY EXISTING DEVELOPMENT NEGATIVE CONTROL ===")

    for variant_index, (text, expected_facts) in enumerate(
        variants,
        start=0,
    ):
        observed = _core_facts(
            EXTRACTOR.extract(content=text).frames,
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

        assert not extra
