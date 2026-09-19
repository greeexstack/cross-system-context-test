from __future__ import annotations

from typing import Dict, List, Tuple

from test_embedding_fact_threshold_calibration import (
    _build_full_development_prototypes,
    _calibrate_thresholds,
    _predict_facts,
)
from test_embedding_semantic_separation import MODEL
from test_embedding_holdout_decision_fidelity import (
    _embedding_behavior,
)

from test_independent_paraphrase_battery import BATTERY


def _predict(text: str) -> set[str]:
    prototypes = _build_full_development_prototypes()
    thresholds = _calibrate_thresholds()

    embedding = MODEL.encode(
        [text],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )[0]

    predicted_facts, _margins = _predict_facts(
        embedding,
        prototypes,
        thresholds,
    )

    return predicted_facts


def _fact_pair_results() -> List[dict]:
    records: List[dict] = []

    for family_id, _primary, texts in BATTERY:
        baseline_facts = _predict(texts[0])

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            variant_facts = _predict(text)

            records.append(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "baseline_facts": sorted(baseline_facts),
                    "variant_facts": sorted(variant_facts),
                    "consistent": (
                        variant_facts == baseline_facts
                    ),
                }
            )

    return records


def test_embedding_independent_paraphrase_fact_consistency() -> None:
    print(
        "\n=== EMBEDDING INDEPENDENT PARAPHRASE "
        "FACT CONSISTENCY ==="
    )

    records = _fact_pair_results()

    consistent = sum(
        int(record["consistent"])
        for record in records
    )

    total = len(records)
    pbc = consistent / total

    for record in records:
        print(record)

    print(
        {
            "pair_count": total,
            "consistent_pairs": consistent,
            "inconsistent_pairs": total - consistent,
            "paraphrase_behavioral_consistency": pbc,
        }
    )

    assert total == 15


def test_embedding_independent_paraphrase_decision_consistency() -> None:
    print(
        "\n=== EMBEDDING INDEPENDENT PARAPHRASE "
        "DECISION CONSISTENCY ==="
    )

    records: List[dict] = []

    for family_id, primary, texts in BATTERY:
        baseline = _embedding_behavior(
            primary,
            texts[0],
            _build_full_development_prototypes(),
            _calibrate_thresholds(),
        )

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            variant = _embedding_behavior(
                primary,
                text,
                _build_full_development_prototypes(),
                _calibrate_thresholds(),
            )

            consistent = variant == baseline

            records.append(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "baseline_decision": baseline,
                    "variant_decision": variant,
                    "consistent": consistent,
                }
            )

    consistent = sum(
        int(record["consistent"])
        for record in records
    )

    total = len(records)
    pbc = consistent / total

    for record in records:
        print(record)

    print(
        {
            "pair_count": total,
            "consistent_pairs": consistent,
            "inconsistent_pairs": total - consistent,
            "decision_paraphrase_consistency": pbc,
        }
    )

    assert total == 15


def test_embedding_independent_paraphrase_family_breakdown() -> None:
    fact_records = _fact_pair_results()

    by_family: Dict[str, List[dict]] = {}

    for record in fact_records:
        by_family.setdefault(
            record["family"],
            [],
        ).append(record)

    print(
        "\n=== EMBEDDING INDEPENDENT PARAPHRASE "
        "FAMILY BREAKDOWN ==="
    )

    for family_id, records in by_family.items():
        consistent = sum(
            int(record["consistent"])
            for record in records
        )

        print(
            {
                "family": family_id,
                "consistent": consistent,
                "total": len(records),
                "consistency": (
                    consistent / len(records)
                ),
            }
        )