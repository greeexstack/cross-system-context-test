from __future__ import annotations

from dataclasses import replace

from experiment.v03.evidence import EvidenceCondition
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)

from test_independent_paraphrase_battery import (
    BATTERY,
    EVALUATION_AT,
    FIXED_CUSTOMER_ID,
    FIXED_RECORD_ID,
    FIXED_SOURCE,
    FIXED_TIMESTAMP,
)


EXTRACTOR = LexicalNormalizationSemanticExtractor()
REASONER = V03Reasoner(
    ReasonerConfig(
        evaluation_at=EVALUATION_AT,
        stale_after_days=30,
    )
)


def _extract(text: str):
    return EXTRACTOR.extract(
        evidence_id=FIXED_RECORD_ID,
        content=text,
        source_system=FIXED_SOURCE,
        record_id=FIXED_RECORD_ID,
        occurred_at=FIXED_TIMESTAMP,
        customer_id=FIXED_CUSTOMER_ID,
    ).evidence


def _evaluate(primary: PrimaryState, evidence):
    condition = EvidenceCondition(
        availability="available",
        items=(evidence,),
    )
    return REASONER.evaluate(primary, condition)


def _observable_state(result) -> tuple:
    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def _measure() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for family_id, primary, texts in BATTERY:
        original_text = texts[0]
        original_evidence = _extract(original_text)
        original_result = _evaluate(primary, original_evidence)
        original_state = _observable_state(original_result)

        for variant_index, variant_text in enumerate(texts[1:], start=1):
            variant_evidence = _extract(variant_text)
            variant_result = _evaluate(primary, variant_evidence)
            variant_state = _observable_state(variant_result)

            restored_evidence = replace(
                variant_evidence,
                semantics=original_evidence.semantics,
            )

            restored_result = _evaluate(
                primary,
                restored_evidence,
            )
            restored_state = _observable_state(restored_result)

            representation_changed = (
                variant_evidence.semantics
                != original_evidence.semantics
            )

            behavior_changed = (
                variant_state != original_state
            )

            restoration_returned = (
                restored_state == original_state
            )

            restoration_followed_variant = (
                restored_state == variant_state
            )

            if not representation_changed:
                classification = "no_representation_change"
            elif not behavior_changed:
                classification = "behaviorally_masked"
            elif restoration_returned:
                classification = "representation_mediated"
            else:
                classification = "representation_insufficient"

            rows.append(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "representation_changed": representation_changed,
                    "behavior_changed": behavior_changed,
                    "restoration_returned_to_original": (
                        restoration_returned
                    ),
                    "restoration_followed_variant": (
                        restoration_followed_variant
                    ),
                    "classification": classification,
                    "original_state": original_state,
                    "variant_state": variant_state,
                    "restored_state": restored_state,
                }
            )

    return rows


def test_development_representation_restoration() -> None:
    rows = _measure()

    print("\n=== DEVELOPMENT REPRESENTATION RESTORATION ===")

    for row in rows:
        print(row)

    assert len(rows) == 15

    assert all(
        {
            "family",
            "variant",
            "representation_changed",
            "behavior_changed",
            "restoration_returned_to_original",
            "classification",
        }.issubset(row)
        for row in rows
    )


def test_development_representation_restoration_is_deterministic() -> None:
    assert _measure() == _measure()