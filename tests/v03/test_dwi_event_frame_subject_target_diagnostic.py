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


from test_dwi_event_frame_subject_target_battery import CASES
from dwi_event_frame_extractor import extract_event_frame


def _find_argument(frame, target):
    for argument in frame["arguments"]:
        if argument.get("target") == target:
            return argument

    for event in frame["subevents"]:
        for argument in event["arguments"]:
            if argument.get("target") == target:
                return argument

    return None


def test_subject_target_extractor():
    print("\n=== SUBJECT-TARGET EXTRACTOR DIAGNOSTIC ===")

    correct = 0

    for (
        case_id,
        text,
        expected_target,
        expected_status,
    ) in CASES:
        frame = extract_event_frame(text)

        argument = _find_argument(
            frame,
            expected_target,
        )

        actual_status = (
            argument["status"]
            if argument is not None
            else None
        )

        exact = (
            argument is not None
            and actual_status == expected_status
        )

        if exact:
            correct += 1

        print(
            {
                "case": case_id,
                "text": text,
                "expected_target": expected_target,
                "expected_status": expected_status,
                "actual": argument,
                "exact": exact,
                "frame": frame,
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

    assert len(CASES) == 12