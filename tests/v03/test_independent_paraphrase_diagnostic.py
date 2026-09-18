from __future__ import annotations

import json

from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)

from test_independent_paraphrase_battery import BATTERY


FEATURES = (
    "requests_followup",
    "expresses_acceptance",
    "expresses_rejection",
    "confirms_approval",
    "confirms_completion",
    "requests_next_step",
    "concerns_same_work_item",
)


def _extract(text: str):
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id="DIAGNOSTIC",
        content=text,
        source_system="diagnostic",
        record_id="DIAGNOSTIC",
        occurred_at="2026-09-12T10:00:00Z",
        customer_id="INDEPENDENT-CUSTOMER",
    ).evidence.semantics


def test_print_independent_battery_semantic_diagnostics() -> None:
    for family_id, _primary, texts in BATTERY:
        print(f"\n=== {family_id} ===")

        for index, text in enumerate(texts):
            semantics = _extract(text)

            features = {
                feature: getattr(
                    semantics,
                    feature,
                )
                for feature in FEATURES
            }

            print(
                json.dumps(
                    {
                        "variant_index": index,
                        "text": text,
                        "features": features,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )