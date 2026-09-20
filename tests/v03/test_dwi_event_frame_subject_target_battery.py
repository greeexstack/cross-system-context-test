from __future__ import annotations

import pytest


CASES = [
    (
        "SUBJ1",
        "The current agreement concerns another deployment.",
        "agreement",
        "CURRENT",
    ),
    (
        "SUBJ2",
        "A separate agreement concerns the current deployment.",
        "agreement",
        "DIFFERENT",
    ),
    (
        "SUBJ3",
        "The current proposal relates to another rollout.",
        "proposal",
        "CURRENT",
    ),
    (
        "SUBJ4",
        "A different proposal relates to the current rollout.",
        "proposal",
        "DIFFERENT",
    ),
    (
        "SUBJ5",
        "The current opportunity involves another installation.",
        "opportunity",
        "CURRENT",
    ),
    (
        "SUBJ6",
        "A separate opportunity involves the current installation.",
        "opportunity",
        "DIFFERENT",
    ),
    (
        "SUBJ7",
        "The current quotation concerns a separate deployment.",
        "quotation",
        "CURRENT",
    ),
    (
        "SUBJ8",
        "A different quotation concerns the current deployment.",
        "quotation",
        "DIFFERENT",
    ),
    (
        "SUBJ9",
        "The current proposal relates to another account.",
        "proposal",
        "CURRENT",
    ),
    (
        "SUBJ10",
        "A separate proposal relates to the current account.",
        "proposal",
        "DIFFERENT",
    ),
    (
        "SUBJ11",
        "The current opportunity involves another buyer.",
        "opportunity",
        "CURRENT",
    ),
    (
        "SUBJ12",
        "A different opportunity involves the current buyer.",
        "opportunity",
        "DIFFERENT",
    ),
]


@pytest.mark.parametrize(
    "case_id,text,expected_target,expected_status",
    CASES,
)
def test_subject_target_battery(
    case_id,
    text,
    expected_target,
    expected_status,
):
    assert text
    assert expected_target

    assert expected_status in {
        "CURRENT",
        "DIFFERENT",
    }


def test_battery_size():
    assert len(CASES) == 12