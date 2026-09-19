from __future__ import annotations

import pytest


CASES = [
    (
        "RDWI1",
        "The team is reviewing this quotation, not another quotation.",
        "The team is reviewing another quotation, not this quotation.",
    ),
    (
        "RDWI2",
        "The account is discussing this proposal, not another proposal.",
        "The account is discussing another proposal, not this proposal.",
    ),
    (
        "RDWI3",
        "The buyer is evaluating this offer, not another offer.",
        "The buyer is evaluating another offer, not this offer.",
    ),
    (
        "RDWI4",
        "The customer is considering this deal, not another deal.",
        "The customer is considering another deal, not this deal.",
    ),
    (
        "RDWI5",
        "The team is working on this opportunity, not another opportunity.",
        "The team is working on another opportunity, not this opportunity.",
    ),
    (
        "RDWI6",
        "The account is reviewing this agreement, not another agreement.",
        "The account is reviewing another agreement, not this agreement.",
    ),
    (
        "RDWI7",
        "The procurement team is examining this proposal, not another proposal.",
        "The procurement team is examining another proposal, not this proposal.",
    ),
    (
        "RDWI8",
        "The client is discussing this account, not another account.",
        "The client is discussing another account, not this account.",
    ),
]


@pytest.mark.parametrize(
    "pair_id,current_item,different_item",
    CASES,
)
def test_role_reversal_pair_is_well_formed(
    pair_id: str,
    current_item: str,
    different_item: str,
) -> None:
    assert current_item != different_item

    # Same lexical inventory.
    assert "another" in current_item.lower()
    assert "another" in different_item.lower()

    # Same contrast structure.
    assert "not" in current_item.lower()
    assert "not" in different_item.lower()


def test_battery_size():
    assert len(CASES) == 8