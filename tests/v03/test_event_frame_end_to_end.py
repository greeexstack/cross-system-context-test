from __future__ import annotations

from experiment.v03.evidence import EvidenceCondition
from experiment.v03.event_frame_adapter import frames_to_semantics
from experiment.v03.event_frames import (
    CanonicalEventFrameExtractor,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)
from test_independent_paraphrase_battery import (
    BATTERY,
    EVALUATION_AT,
)


def _evaluate_with_event_frames(
    primary: PrimaryState,
    text: str,
):
    extractor = CanonicalEventFrameExtractor()

    extracted = extractor.extract(
        content=text,
    )

    semantics = frames_to_semantics(
        extracted.frames,
    )

    from experiment.v03.evidence import (
        EvidenceIdentity,
        EvidenceProvenance,
        SemanticEvidence,
        IdentityQuality,
    )

    evidence = SemanticEvidence(
        evidence_id="EVENT-FRAME",
        content=text,
        provenance=EvidenceProvenance(
            source_system="independent_paraphrase_battery",
            record_id="EVENT-FRAME",
            occurred_at=(
                __import__(
                    "datetime"
                ).datetime.fromisoformat(
                    "2026-09-12T10:00:00+00:00"
                )
            ),
        ),
        identity=EvidenceIdentity(
            customer_id="INDEPENDENT-CUSTOMER",
            quality=IdentityQuality.CONFIRMED,
        ),
        semantics=semantics,
    )

    condition = EvidenceCondition(
        availability="available",
        items=(evidence,),
    )

    reasoner = V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )

    return reasoner.evaluate(
        primary,
        condition,
    )


def _observable_state(result) -> tuple:
    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def test_event_frame_candidate_preserves_end_to_end_behavior() -> None:
    total_pairs = 0
    consistent_pairs = 0
    inconsistent_pairs = 0

    for family_id, primary, texts in BATTERY:
        original = _observable_state(
            _evaluate_with_event_frames(
                primary,
                texts[0],
            )
        )

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            total_pairs += 1

            variant = _observable_state(
                _evaluate_with_event_frames(
                    primary,
                    text,
                )
            )

            if variant == original:
                consistent_pairs += 1
            else:
                inconsistent_pairs += 1

                print(
                    f"\nBEHAVIOR DRIFT {family_id} "
                    f"variant={variant_index}"
                )
                print(f"original={original}")
                print(f"variant={variant}")

    print(
        "\n=== EVENT-FRAME END-TO-END ==="
    )
    print(
        {
            "total_pairs": total_pairs,
            "consistent_pairs": consistent_pairs,
            "inconsistent_pairs": inconsistent_pairs,
            "consistency_rate": (
                consistent_pairs / total_pairs
            ),
        }
    )

    assert total_pairs == 15
    assert (
        consistent_pairs + inconsistent_pairs
        == total_pairs
    )


def test_event_frame_candidate_preserves_negative_control() -> None:
    family = next(
        item
        for item in BATTERY
        if item[0] == "R4-irrelevant"
    )

    _family_id, primary, texts = family

    states = [
        _observable_state(
            _evaluate_with_event_frames(
                primary,
                text,
            )
        )
        for text in texts
    ]

    assert all(
        state == states[0]
        for state in states
    )

    assert all(
        state[0] == "quote_pending_decision"
        for state in states
    )