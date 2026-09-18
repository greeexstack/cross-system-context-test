from __future__ import annotations

from test_event_frame_holdout import HOLDOUT, _extract
from test_event_frame_holdout_comparison import (
    _candidate_behavior,
    _old_behavior,
)


def test_print_holdout_failure_mechanisms() -> None:
    old_total = 0
    old_consistent = 0
    candidate_total = 0
    candidate_consistent = 0

    print("\n=== HOLDOUT FAILURE ANALYSIS ===")

    for family_id, primary, texts, expected_facts in HOLDOUT:
        old_original = _old_behavior(primary, texts[0])
        candidate_original = _candidate_behavior(
            primary,
            texts[0],
        )

        family_old_consistent = 0
        family_candidate_consistent = 0

        for variant_index, text in enumerate(
            texts[1:],
            start=1,
        ):
            old_total += 1
            candidate_total += 1

            old_variant = _old_behavior(primary, text)
            candidate_variant = _candidate_behavior(
                primary,
                text,
            )

            old_same = old_variant == old_original
            candidate_same = (
                candidate_variant
                == candidate_original
            )

            if old_same:
                old_consistent += 1
                family_old_consistent += 1

            if candidate_same:
                candidate_consistent += 1
                family_candidate_consistent += 1

            if (
                not old_same
                or not candidate_same
            ):
                
                

                # Use the candidate's actual event-frame extractor
                # for inspection rather than treating core-fact labels
                # as engine inputs.
                from experiment.v03.event_frames import (
                    CanonicalEventFrameExtractor,
                )

                candidate_extracted = (
                    CanonicalEventFrameExtractor().extract(
                        content=text,
                    )
                )

                print(
                    {
                        "family": family_id,
                        "variant": variant_index,
                        "expected_core_facts": sorted(
                            expected_facts
                        ),
                        "old_same_as_original": old_same,
                        "candidate_same_as_original": (
                            candidate_same
                        ),
                        "old_original": old_original,
                        "old_variant": old_variant,
                        "candidate_original": (
                            candidate_original
                        ),
                        "candidate_variant": (
                            candidate_variant
                        ),
                        
                        "candidate_frames": (
                            candidate_extracted.frames
                        ),
                    }
                )

        print(
            {
                "family": family_id,
                "old_consistent_pairs": (
                    family_old_consistent
                ),
                "candidate_consistent_pairs": (
                    family_candidate_consistent
                ),
            }
        )

    print(
        "\n=== HOLDOUT SUMMARY ==="
    )
    print(
        {
            "old_consistent_pairs": old_consistent,
            "old_pairs": old_total,
            "old_rate": (
                old_consistent / old_total
            ),
            "candidate_consistent_pairs": (
                candidate_consistent
            ),
            "candidate_pairs": candidate_total,
            "candidate_rate": (
                candidate_consistent
                / candidate_total
            ),
        }
    )

    assert old_total == 15
    assert candidate_total == 15