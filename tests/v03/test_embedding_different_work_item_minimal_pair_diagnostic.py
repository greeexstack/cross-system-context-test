from __future__ import annotations

from collections import defaultdict

from test_embedding_different_work_item_minimal_pairs import (
    DWI_FOLLOWUP_MINIMAL_PAIRS,
)

from test_embedding_target_confounder_enriched_v3 import (
    _all_development_examples,
    _build_nested_target_model,
)

from test_embedding_followup_nextstep_targeted_enrichment_v2 import (
    TARGET_FACTS,
)

from test_embedding_followup_nextstep_targeted_enrichment import (
    _encode,
    _predict,
)


def _examples():
    rows = []

    for pair_id, variants in DWI_FOLLOWUP_MINIMAL_PAIRS:
        for variant_id, (
            text,
            expected_facts,
        ) in enumerate(variants):
            rows.append(
                (
                    pair_id,
                    variant_id,
                    text,
                    set(expected_facts),
                )
            )

    return rows


def _build_current_v3_model():
    examples = _all_development_examples()

    texts = [
        text
        for _family, _variant, text, _facts
        in examples
    ]

    expected = [
        facts
        for _family, _variant, _text, facts
        in examples
    ]

    embeddings = _encode(texts)

    indices = list(range(len(examples)))

    prototypes = _build_nested_target_model(
        embeddings,
        expected,
        len(examples),
    )[0]

    thresholds = {
        fact: 0.0
        for fact in TARGET_FACTS
    }

    return prototypes, thresholds


def test_current_v3_on_fresh_dwi_followup_minimal_pairs():
    prototypes, thresholds = (
        _build_current_v3_model()
    )

    totals = defaultdict(int)
    exact = defaultdict(int)

    print(
        "\n=== V3 ON FRESH DWI/FOLLOWUP MINIMAL PAIRS ==="
    )

    for (
        pair_id,
        variant_id,
        text,
        expected_facts,
    ) in _examples():
        embedding = _encode([text])[0]

        predicted, margins = _predict(
            embedding,
            prototypes,
            thresholds,
        )

        is_exact = (
            predicted
            == (
                expected_facts
                & set(TARGET_FACTS)
            )
        )

        family = next(
            iter(expected_facts)
        )

        totals[family] += 1
        exact[family] += int(is_exact)

        print(
            {
                "pair": pair_id,
                "variant": variant_id,
                "text": text,
                "expected": sorted(
                    expected_facts
                ),
                "target_predicted": sorted(
                    predicted
                ),
                "exact": is_exact,
                "followup_margin": round(
                    margins[
                        "followup_request"
                    ],
                    4,
                ),
                "next_step_margin": round(
                    margins[
                        "next_step_requested"
                    ],
                    4,
                ),
            }
        )

    print(
        "\n=== MINIMAL-PAIR SUMMARY ==="
    )

    for family in sorted(totals):
        print(
            {
                "family": family,
                "exact": exact[family],
                "total": totals[family],
                "accuracy": (
                    exact[family]
                    / totals[family]
                ),
            }
        )


def test_minimal_pair_results_are_deterministic():
    prototypes, thresholds = (
        _build_current_v3_model()
    )

    def run():
        output = []

        for (
            pair_id,
            variant_id,
            text,
            expected_facts,
        ) in _examples():
            embedding = _encode([text])[0]

            predicted, margins = _predict(
                embedding,
                prototypes,
                thresholds,
            )

            output.append(
                (
                    pair_id,
                    variant_id,
                    frozenset(predicted),
                    round(
                        margins[
                            "followup_request"
                        ],
                        6,
                    ),
                    round(
                        margins[
                            "next_step_requested"
                        ],
                        6,
                    ),
                )
            )

        return output

    assert run() == run()