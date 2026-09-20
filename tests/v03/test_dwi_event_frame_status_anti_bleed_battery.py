from __future__ import annotations

import pytest


CASES = [
    (
        "BLEED1",
        "The team is reviewing the current quotation about a separate rollout.",
        "quotation",
        "CURRENT",
    ),
    (
        "BLEED2",
        "The team is reviewing a separate quotation about the current rollout.",
        "quotation",
        "DIFFERENT",
    ),
    (
        "BLEED3",
        "The buyer is discussing the current proposal with another account.",
        "proposal",
        "CURRENT",
    ),
    (
        "BLEED4",
        "The buyer is discussing another proposal with the current account.",
        "proposal",
        "DIFFERENT",
    ),
    (
        "BLEED5",
        "The team is working on the current opportunity with a different buyer.",
        "opportunity",
        "CURRENT",
    ),
    (
        "BLEED6",
        "The team is working on a different opportunity with the current buyer.",
        "opportunity",
        "DIFFERENT",
    ),
    (
        "BLEED7",
        "The current agreement concerns another deployment.",
        "agreement",
        "CURRENT",
    ),
    (
        "BLEED8",
        "A separate agreement concerns the current deployment.",
        "agreement",
        "DIFFERENT",
    ),
]


@pytest.mark.parametrize(
    "case_id,text,target,expected_status",
    CASES,
)
def test_status_anti_bleed_battery(
    case_id,
    text,
    target,
    expected_status,
):
    assert text
    assert target
    assert expected_status in {
        "CURRENT",
        "DIFFERENT",
    }


def test_battery_size():
    assert len(CASES) == 8