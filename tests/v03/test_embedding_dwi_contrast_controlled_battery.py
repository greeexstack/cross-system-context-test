from __future__ import annotations

import pytest


CASES = [
    (
        "CDWI1",
        "The team is reviewing this quotation, not another quotation.",
        "The team is reviewing a separate quotation, not this quotation.",
    ),
    (
        "CDWI2",
        "The account is discussing this proposal, not another proposal.",
        "The account is discussing a different proposal, not this proposal.",
    ),
    (
        "CDWI3",
        "The buyer is evaluating this offer, not another offer.",
        "The buyer is evaluating a separate offer, not this offer.",
    ),
    (
        "CDWI4",
        "The customer is considering this deal, not another deal.",
        "The customer is considering a different deal, not this deal.",
    ),
    (
        "CDWI5",
        "The team is working on this opportunity, not another opportunity.",
        "The team is working on a separate opportunity, not this opportunity.",
    ),
    (
        "CDWI6",
        "The account is reviewing this agreement, not another agreement.",
        "The account is reviewing a different agreement, not this agreement.",
    ),
    (
        "CDWI7",
        "The procurement team is examining this proposal, not another proposal.",
        "The procurement team is examining a separate proposal, not this proposal.",
    ),
    (
        "CDWI8",
        "The client is discussing this account, not another account.",
        "The client is discussing a different account, not this account.",
    ),
]


@pytest.mark.parametrize(
    "pair_id,current_item,different_item",
    CASES,
)
def test_contrast_controlled_pair_is_well_formed(
    pair_id: str,
    current_item: str,
    different_item: str,
) -> None:
    assert current_item
    assert different_item
    assert current_item != different_item

    assert "not" in current_item.lower()
    assert "not" in different_item.lower()

    assert any(
        marker in different_item.lower()
        for marker in ("separate", "different", "another")
    )


def test_battery_size():
    assert len(CASES) == 8