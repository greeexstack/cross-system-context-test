from __future__ import annotations

from experiment.v03.clause_local_extractor_v2 import (
    ClauseLocalRelationalEventFrameExtractor,
)

from test_clause_local_construction_battery import (
    CONSTRUCTION_BATTERY,
)


def _extract(text: str):
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

    return facts


def test_construction_generalization_is_measured() -> None:
    total = 0
    exact = 0
    partial = 0
    missed = 0
    false_positive_variants = 0

    print("\n=== CONSTRUCTION GENERALIZATION ===")

    for family_id, _primary_state, variants in CONSTRUCTION_BATTERY:
        family_exact = 0
        family_partial = 0
        family_missed = 0

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
                family_exact += 1
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
                    "family": family_id,
                    "variant": variant_index,
                    "text": text,
                    "expected": sorted(expected_facts),
                    "observed": sorted(observed),
                    "missing": sorted(missing),
                    "extra": sorted(extra),
                    "exact": not missing and not extra,
                }
            )

        print(
            {
                "family": family_id,
                "exact": family_exact,
                "partial": family_partial,
                "missed": family_missed,
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


def test_construction_generalization_has_no_unexpected_facts() -> None:
    unexpected: list[dict[str, object]] = []

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

    print(
        "\n=== CONSTRUCTION FALSE-POSITIVE CHECK ==="
    )
    print(
        {
            "unexpected_variants": len(unexpected),
            "details": unexpected,
        }
    )

    assert not unexpected


def test_construction_failure_examples_are_explicit() -> None:
    failures: list[tuple[str, int, str]] = []

    for family_id, _primary_state, variants in CONSTRUCTION_BATTERY:
        for variant_index, (text, expected_facts) in enumerate(
            variants,
            start=0,
        ):
            observed = _core_facts(
                _extract(text).frames,
            )

            if not expected_facts.issubset(observed):
                failures.append(
                    (
                        family_id,
                        variant_index,
                        text,
                    )
                )

    print(
        "\n=== CONSTRUCTION FAILURES ==="
    )
    print(
        {
            "failure_count": len(failures),
            "failures": failures,
        }
    )

    assert len(failures) >= 0