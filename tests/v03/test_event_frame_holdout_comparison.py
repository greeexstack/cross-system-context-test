from __future__ import annotations

from experiment.v03.evidence import EvidenceCondition, SemanticEvidence
from experiment.v03.event_frame_adapter import frames_to_semantics
from experiment.v03.event_frames import CanonicalEventFrameExtractor
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)
from experiment.v03.reasoner import PrimaryState, ReasonerConfig, V03Reasoner

from test_event_frame_holdout import HOLDOUT
from test_independent_paraphrase_battery import EVALUATION_AT


TIMESTAMP = "2026-09-12T10:00:00+00:00"


def _reason_with_semantics(
    primary: PrimaryState,
    text: str,
    semantics,
):
    evidence = SemanticEvidence(
        evidence_id="HOLDOUT-COMPARISON",
        content=text,
        provenance=__import__(
            "experiment.v03.evidence",
            fromlist=["EvidenceProvenance"],
        ).EvidenceProvenance(
            source_system="holdout-comparison",
            record_id="HOLDOUT-COMPARISON",
            occurred_at=__import__(
                "datetime"
            ).datetime.fromisoformat(TIMESTAMP),
        ),
        identity=__import__(
            "experiment.v03.evidence",
            fromlist=["EvidenceIdentity", "IdentityQuality"],
        ).EvidenceIdentity(
            customer_id="HOLDOUT-CUSTOMER",
            quality=__import__(
                "experiment.v03.evidence",
                fromlist=["IdentityQuality"],
            ).IdentityQuality.CONFIRMED,
        ),
        semantics=semantics,
    )

    condition = EvidenceCondition(
        availability="available",
        items=(evidence,),
    )

    return V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    ).evaluate(
        primary,
        condition,
    )


def _old_behavior(
    primary: PrimaryState,
    text: str,
) -> tuple:
    extracted = LexicalNormalizationSemanticExtractor().extract(
        evidence_id="OLD",
        content=text,
        source_system="holdout",
        record_id="OLD",
        occurred_at=TIMESTAMP,
        customer_id="HOLDOUT-CUSTOMER",
    )

    result = _reason_with_semantics(
        primary,
        text,
        extracted.evidence.semantics,
    )

    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def _candidate_behavior(
    primary: PrimaryState,
    text: str,
) -> tuple:
    extracted = CanonicalEventFrameExtractor().extract(
        content=text,
    )

    semantics = frames_to_semantics(
        extracted.frames,
    )

    result = _reason_with_semantics(
        primary,
        text,
        semantics,
    )

    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def _consistency_rate(
    runner,
) -> tuple[int, int]:
    total_pairs = 0
    consistent_pairs = 0

    for _family_id, primary, texts, _expected in HOLDOUT:
        original = runner(
            primary,
            texts[0],
        )

        for text in texts[1:]:
            total_pairs += 1

            if runner(primary, text) == original:
                consistent_pairs += 1

    return consistent_pairs, total_pairs


def test_holdout_compares_old_and_candidate_without_tuning() -> None:
    old_consistent, total = _consistency_rate(
        _old_behavior
    )

    candidate_consistent, candidate_total = _consistency_rate(
        _candidate_behavior
    )

    assert total == 15
    assert candidate_total == 15

    print(
        "\n=== HOLDOUT OLD VS CANDIDATE ==="
    )
    print(
        {
            "pairs": total,
            "old_consistent_pairs": old_consistent,
            "old_consistency_rate": (
                old_consistent / total
            ),
            "candidate_consistent_pairs": (
                candidate_consistent
            ),
            "candidate_consistency_rate": (
                candidate_consistent / total
            ),
            "candidate_minus_old": (
                (candidate_consistent / total)
                - (old_consistent / total)
            ),
        }
    )

    assert 0 <= old_consistent <= total
    assert 0 <= candidate_consistent <= total


def test_holdout_negative_control_compares_old_and_candidate() -> None:
    family = next(
        item
        for item in HOLDOUT
        if item[0] == "H4-irrelevant"
    )

    _family_id, primary, texts, _expected = family

    old_states = [
        _old_behavior(primary, text)
        for text in texts
    ]

    candidate_states = [
        _candidate_behavior(primary, text)
        for text in texts
    ]

    old_consistent = sum(
        state == old_states[0]
        for state in old_states[1:]
    )

    candidate_consistent = sum(
        state == candidate_states[0]
        for state in candidate_states[1:]
    )

    print(
        "\n=== HOLDOUT NEGATIVE CONTROL COMPARISON ==="
    )
    print(
        {
            "pairs": 3,
            "old_consistent_pairs": old_consistent,
            "candidate_consistent_pairs": candidate_consistent,
        }
    )

    assert 0 <= old_consistent <= 3
    assert 0 <= candidate_consistent <= 3