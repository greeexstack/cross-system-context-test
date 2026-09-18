from __future__ import annotations

from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)
from experiment.v03.reasoner import (
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
        evidence_id=FIXED_RECORD_ID,
        content=text,
        source_system=FIXED_SOURCE,
        record_id=FIXED_RECORD_ID,
        occurred_at=FIXED_TIMESTAMP,
        customer_id=FIXED_CUSTOMER_ID,
    ).evidence


def _feature_state(text: str) -> dict[str, object]:
    semantics = _extract(text).semantics

    return {
        feature: getattr(semantics, feature)
        for feature in FEATURES
    }


def _metadata_state(text: str) -> tuple:
    evidence = _extract(text)

    return (
        evidence.provenance.source_system,
        evidence.provenance.record_id,
        evidence.provenance.occurred_at,
        evidence.identity.customer_id,
    )


def _behavior_state(
    primary,
    text: str,
) -> tuple:
    evidence = _extract(text)

    from experiment.v03.evidence import EvidenceCondition

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

    result = reasoner.evaluate(
        primary,
        condition,
    )

    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def test_behavioral_changes_are_explained_by_feature_changes() -> None:
    behavioral_changes = 0
    representation_drifts = 0
    metadata_changes = 0
    masked_representation_drifts = 0

    observations = []

    for family_id, primary, texts in BATTERY:
        original_features = _feature_state(texts[0])
        original_metadata = _metadata_state(texts[0])
        original_behavior = _behavior_state(
            primary,
            texts[0],
        )

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            variant_features = _feature_state(text)
            variant_metadata = _metadata_state(text)
            variant_behavior = _behavior_state(
                primary,
                text,
            )

            feature_changes = {
                feature
                for feature in FEATURES
                if (
                    original_features[feature]
                    != variant_features[feature]
                )
            }

            metadata_changed = (
                variant_metadata
                != original_metadata
            )

            behavior_changed = (
                variant_behavior
                != original_behavior
            )

            if feature_changes:
                representation_drifts += 1

            if metadata_changed:
                metadata_changes += 1

            if behavior_changed:
                behavioral_changes += 1

                assert feature_changes, (
                    f"{family_id} variant {variant_index}: "
                    "behavior changed without a corresponding "
                    "semantic-feature change"
                )

            elif feature_changes:
                masked_representation_drifts += 1

            observations.append(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "feature_changes": tuple(
                        sorted(feature_changes)
                    ),
                    "behavior_changed": behavior_changed,
                    "metadata_changed": metadata_changed,
                }
            )

    print(
        "\n=== REPRESENTATION VS BEHAVIORAL DRIFT ==="
    )
    print(
        {
            "total_pairs": 15,
            "behavioral_change_pairs": behavioral_changes,
            "representation_drift_pairs": representation_drifts,
            "masked_representation_drift_pairs": (
                masked_representation_drifts
            ),
            "metadata_change_pairs": metadata_changes,
        }
    )

    for observation in observations:
        if (
            observation["behavior_changed"]
            or observation["feature_changes"]
        ):
            print(observation)

    assert behavioral_changes == 7
    assert representation_drifts == 8
    assert masked_representation_drifts == 1
    assert metadata_changes == 0


def test_known_behavioral_failures_are_all_lexical_representation_failures() -> None:
    behavioral_failures = []

    for family_id, primary, texts in BATTERY:
        original_features = _feature_state(texts[0])
        original_behavior = _behavior_state(
            primary,
            texts[0],
        )

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            variant_features = _feature_state(text)
            variant_behavior = _behavior_state(
                primary,
                text,
            )

            feature_changes = {
                feature
                for feature in FEATURES
                if (
                    original_features[feature]
                    != variant_features[feature]
                )
            }

            behavior_changed = (
                variant_behavior
                != original_behavior
            )

            if behavior_changed:
                behavioral_failures.append(
                    (
                        family_id,
                        variant_index,
                        tuple(sorted(feature_changes)),
                    )
                )

    assert len(behavioral_failures) == 7

    for family_id, variant_index, feature_changes in (
        behavioral_failures
    ):
        assert feature_changes, (
            f"{family_id} variant {variant_index}: "
            "behavioral failure was not traceable to "
            "semantic representation drift"
        )

        assert all(
            isinstance(feature, str)
            for feature in feature_changes
        )