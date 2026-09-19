from __future__ import annotations

import pytest


CASES = [
    (
        "DWI1",
        "The team is reviewing the current quotation.",
        "The team is reviewing a separate quotation.",
    ),
    (
        "DWI2",
        "The account is discussing the current proposal internally.",
        "The account is discussing a separate proposal internally.",
    ),
    (
        "DWI3",
        "The buyer is evaluating the current offer.",
        "The buyer is evaluating a different offer.",
    ),
    (
        "DWI4",
        "The customer is considering the current deal.",
        "The customer is considering another deal.",
    ),
    (
        "DWI5",
        "The commercial team is working on the current opportunity.",
        "The commercial team is working on a separate opportunity.",
    ),
    (
        "DWI6",
        "The account is reviewing the current agreement.",
        "The account is reviewing another agreement.",
    ),
    (
        "DWI7",
        "The procurement team is examining the current proposal.",
        "The procurement team is examining a different proposal.",
    ),
    (
        "DWI8",
        "The client is discussing the current account.",
        "The client is discussing another account.",
    ),
]


@pytest.mark.parametrize(
    "pair_id,current_item,different_item",
    CASES,
)
def test_different_work_item_minimal_pair_is_well_formed(
    pair_id: str,
    current_item: str,
    different_item: str,
) -> None:
    assert current_item
    assert different_item
    assert current_item != different_item

    # The pair must differ specifically in the work-item referent.
    markers = (
        "separate",
        "different",
        "another",
    )
    assert any(marker in different_item.lower() for marker in markers)

    assert not any(
        marker in current_item.lower() for marker in markers
    )