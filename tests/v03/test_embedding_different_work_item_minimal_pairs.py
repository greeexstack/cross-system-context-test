from __future__ import annotations


DWI_FOLLOWUP_MINIMAL_PAIRS = (
    (
        "MP1",
        (
            (
                "The customer wants another discussion about this quotation.",
                {"followup_request"},
            ),
            (
                "The customer wants another discussion about a separate quotation.",
                {"different_work_item"},
            ),
        ),
    ),
    (
        "MP2",
        (
            (
                "The buyer asked to resume the proposal discussion.",
                {"followup_request"},
            ),
            (
                "The buyer asked to resume the discussion on another proposal.",
                {"different_work_item"},
            ),
        ),
    ),
    (
        "MP3",
        (
            (
                "The client requested a further meeting about the current offer.",
                {"followup_request"},
            ),
            (
                "The client requested a further meeting about a different offer.",
                {"different_work_item"},
            ),
        ),
    ),
    (
        "MP4",
        (
            (
                "The purchaser wants to continue the discussion about this deal.",
                {"followup_request"},
            ),
            (
                "The purchaser wants to continue the discussion about another deal.",
                {"different_work_item"},
            ),
        ),
    ),
    (
        "MP5",
        (
            (
                "The account team asked for another conversation concerning this opportunity.",
                {"followup_request"},
            ),
            (
                "The account team asked for another conversation concerning a separate opportunity.",
                {"different_work_item"},
            ),
        ),
    ),
    (
        "MP6",
        (
            (
                "The customer wants to revisit the quotation after review.",
                {"followup_request"},
            ),
            (
                "The customer wants to revisit another quotation after review.",
                {"different_work_item"},
            ),
        ),
    ),
    (
        "MP7",
        (
            (
                "The buyer requested that the commercial discussion continue.",
                {"followup_request"},
            ),
            (
                "The buyer requested that the discussion on another account continue.",
                {"different_work_item"},
            ),
        ),
    ),
    (
        "MP8",
        (
            (
                "The client asked for a further exchange about the current proposal.",
                {"followup_request"},
            ),
            (
                "The client asked for a further exchange about a separate proposal.",
                {"different_work_item"},
            ),
        ),
    ),
)


def test_minimal_pair_shape():
    assert len(DWI_FOLLOWUP_MINIMAL_PAIRS) == 8

    texts = []

    for pair_id, variants in DWI_FOLLOWUP_MINIMAL_PAIRS:
        assert len(variants) == 2

        for text, facts in variants:
            assert len(facts) == 1
            texts.append(text)

    assert len(texts) == 16
    assert len(set(texts)) == 16


def test_minimal_pairs_have_opposing_targets():
    for pair_id, variants in DWI_FOLLOWUP_MINIMAL_PAIRS:
        first_facts = variants[0][1]
        second_facts = variants[1][1]

        assert first_facts == {"followup_request"}
        assert second_facts == {"different_work_item"}


def test_minimal_pairs_use_both_semantic_classes():
    followup = 0
    dwi = 0

    for _pair_id, variants in DWI_FOLLOWUP_MINIMAL_PAIRS:
        for _text, facts in variants:
            if facts == {"followup_request"}:
                followup += 1
            elif facts == {"different_work_item"}:
                dwi += 1

    assert followup == 8
    assert dwi == 8