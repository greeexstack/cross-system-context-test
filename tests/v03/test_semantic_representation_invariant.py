from __future__ import annotations

from dataclasses import asdict

from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)

from test_independent_paraphrase_battery import (
    BATTERY,
    FIXED_CUSTOMER_ID,
    FIXED_RECORD_ID,
    FIXED_SOURCE,
    FIXED_TIMESTAMP,
)


SEMANTIC_FIELDS = (
    "topic",
    "polarity",
    "negated_concepts",
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
        evidence_id=FIXED_RECORD_ID,
        content=text,
        source_system=FIXED_SOURCE,
        record_id=FIXED_RECORD_ID,
        occurred_at=FIXED_TIMESTAMP,
        customer_id=FIXED_CUSTOMER_ID,
    ).evidence


def _semantic_fingerprint(text: str) -> tuple:
    semantics = _extract(text).semantics

    return tuple(
        getattr(semantics, field)
        for field in SEMANTIC_FIELDS
    )


def _metadata_fingerprint(text: str) -> tuple:
    evidence = _extract(text)

    return (
        evidence.provenance.source_system,
        evidence.provenance.record_id,
        evidence.provenance.occurred_at,
        evidence.identity.customer_id,
        evidence.identity.quality,
    )


def test_paraphrase_metadata_invariant_holds() -> None:
    for family_id, _primary, texts in BATTERY:
        original_metadata = _metadata_fingerprint(
            texts[0]
        )

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            variant_metadata = _metadata_fingerprint(
                text
            )

            assert variant_metadata == original_metadata, (
                f"{family_id} variant {variant_index}: "
                "metadata changed under paraphrase"
            )


def test_evidence_representation_contains_only_factual_semantics() -> None:
    for _family_id, _primary, texts in BATTERY:
        evidence = _extract(texts[0])
        semantics = asdict(evidence.semantics)

        forbidden = {
            "expected_transition",
            "ground_truth",
            "benchmark_family",
            "pair_id",
            "support_level",
            "interpretation_class",
            "decision_strength",
        }

        assert forbidden.isdisjoint(
            semantics.keys()
        )


def test_semantic_representation_invariant_is_measured() -> None:
    total_pairs = 0
    invariant_pairs = 0
    drift_pairs = 0

    drift_records = []

    for family_id, _primary, texts in BATTERY:
        original = _semantic_fingerprint(texts[0])

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            total_pairs += 1

            variant = _semantic_fingerprint(text)

            if variant == original:
                invariant_pairs += 1
            else:
                drift_pairs += 1

                drift_fields = tuple(
                    field
                    for field, old, new in zip(
                        SEMANTIC_FIELDS,
                        original,
                        variant,
                    )
                    if old != new
                )

                drift_records.append(
                    {
                        "family": family_id,
                        "variant": variant_index,
                        "fields": drift_fields,
                    }
                )

    invariant_rate = (
        invariant_pairs / total_pairs
    )

    print(
        "\n=== SEMANTIC REPRESENTATION INVARIANT ==="
    )
    print(
        {
            "total_pairs": total_pairs,
            "representation_invariant_pairs": (
                invariant_pairs
            ),
            "representation_drift_pairs": (
                drift_pairs
            ),
            "representation_invariance_rate": (
                invariant_rate
            ),
        }
    )

    for record in drift_records:
        print(record)

    # Measurement-phase assertions only.
    assert total_pairs == 15
    assert (
        invariant_pairs + drift_pairs
        == total_pairs
    )
    assert (
        0.0 <= invariant_rate <= 1.0
    )