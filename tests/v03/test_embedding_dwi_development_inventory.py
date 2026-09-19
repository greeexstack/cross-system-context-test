from __future__ import annotations

from test_embedding_target_confounder_enriched_v3 import (
    _all_development_examples,
)


DWI_FACT = "different_work_item"


def _unpack_example(example):
    if len(example) == 4:
        family_id, variant, text, facts = example
        return family_id, variant, text, facts

    if len(example) == 3:
        family_id, text, facts = example
        return family_id, 0, text, facts

    if len(example) == 2:
        text, facts = example
        return "unknown", 0, text, facts

    raise AssertionError(
        f"Unexpected example: {example!r}"
    )


def test_print_dwi_development_inventory():
    examples = [
        _unpack_example(example)
        for example in _all_development_examples()
    ]

    dwi_examples = [
        example
        for example in examples
        if DWI_FACT in example[3]
    ]

    print("\n=== DWI DEVELOPMENT INVENTORY ===")
    print(
        {
            "total_development_examples": len(examples),
            "dwi_positive_examples": len(dwi_examples),
        }
    )

    for family_id, variant, text, facts in dwi_examples:
        print(
            {
                "family": family_id,
                "variant": variant,
                "text": text,
                "facts": sorted(facts),
            }
        )

    assert len(dwi_examples) == 10