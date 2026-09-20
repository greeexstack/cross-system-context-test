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


from test_dwi_event_frame_status_anti_bleed_battery import CASES
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


def test_status_anti_bleed():
    print("\n=== EVENT-FRAME STATUS ANTI-BLEED ===")

    correct = 0

    for (
        case_id,
        text,
        target,
        expected_status,
    ) in CASES:
        frame = extract_event_frame(text)

        argument = _find_argument(frame, target)

        actual_status = (
            argument["status"]
            if argument is not None
            else None
        )

        exact = actual_status == expected_status

        if exact:
            correct += 1

        print(
            {
                "case": case_id,
                "text": text,
                "target": target,
                "expected": expected_status,
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

    assert len(CASES) == 8