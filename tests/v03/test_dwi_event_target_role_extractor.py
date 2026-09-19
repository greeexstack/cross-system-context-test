from __future__ import annotations

import sys
from pathlib import Path

import pytest

from test_embedding_dwi_role_reversal_battery import CASES


V03_SRC = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "experiment"
    / "v03"
)

if str(V03_SRC) not in sys.path:
    sys.path.insert(0, str(V03_SRC))

from dwi_event_target_extractor import extract_event_target


@pytest.mark.parametrize(
    "pair_id,current_item,different_item",
    CASES,
)
def test_event_target_role_reversal(
    pair_id,
    current_item,
    different_item,
):
    current = extract_event_target(current_item)
    different = extract_event_target(different_item)

    print(f"\n=== {pair_id} ===")
    print("CURRENT:")
    print(current_item)
    print(current)

    print("DIFFERENT:")
    print(different_item)
    print(different)

    assert current["target_status"] == "CURRENT"
    assert different["target_status"] == "DIFFERENT"


def test_battery_size():
    assert len(CASES) == 8