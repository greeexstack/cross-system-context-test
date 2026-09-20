from __future__ import annotations

import sys
from pathlib import Path


SRC_V03 = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "experiment"
    / "v03"
)

if str(SRC_V03) not in sys.path:
    sys.path.insert(0, str(SRC_V03))


from dwi_event_frame_extractor import extract_event_frame


CASES = [
    (
        "LOCAL1",
        "The team is speaking with another buyer about the current quotation.",
        "quotation",
        "CURRENT",
        "buyer",
        "DIFFERENT",
    ),
    (
        "LOCAL2",
        "The team is speaking with the buyer about a separate quotation.",
        "quotation",
        "DIFFERENT",
        "buyer",
        "UNKNOWN",
    ),
    (
        "LOCAL3",
        "The customer contacted another buyer about the current proposal.",
        "proposal",
        "CURRENT",
        "buyer",
        "DIFFERENT",
    ),
    (
        "LOCAL4",
        "The customer contacted the buyer about a different proposal.",
        "proposal",
        "DIFFERENT",
        "buyer",
        "UNKNOWN",
    ),
    (
        "LOCAL5",
        "The team met with another procurement group after reviewing the current offer.",
        "offer",
        "CURRENT",
        "group",
        "DIFFERENT",
    ),
    (
        "LOCAL6",
        "The team met with procurement after reviewing a different offer.",
        "offer",
        "DIFFERENT",
        "procurement",
        "UNKNOWN",
    ),
]


def _find_argument(frame, target):
    for argument in frame["arguments"]:
        if argument.get("target") == target:
            return argument

    for event in frame["subevents"]:
        for argument in event["arguments"]:
            if argument.get("target") == target:
                return argument

    return None


def test_status_is_local_to_each_argument():
    print("\n=== EVENT-FRAME STATUS LOCALITY ===")

    correct = 0

    for (
        case_id,
        text,
        expected_work_item,
        expected_work_item_status,
        expected_participant,
        expected_participant_status,
    ) in CASES:
        frame = extract_event_frame(text)

        work_item = _find_argument(
            frame,
            expected_work_item,
        )

        participant = _find_argument(
            frame,
            expected_participant,
        )

        work_item_ok = (
            work_item is not None
            and work_item["status"]
            == expected_work_item_status
        )

        participant_ok = (
            participant is not None
            and participant["status"]
            == expected_participant_status
        )

        exact = work_item_ok and participant_ok

        if exact:
            correct += 1

        print(
            {
                "case": case_id,
                "text": text,
                "work_item": work_item,
                "participant": participant,
                "expected_work_item_status":
                    expected_work_item_status,
                "expected_participant_status":
                    expected_participant_status,
                "exact": exact,
            }
        )

    print("\n=== SUMMARY ===")
    print(
        {
            "exact": correct,
            "total": len(CASES),
            "accuracy": round(
                correct / len(CASES),
                4,
            ),
        }
    )

    assert len(CASES) == 6