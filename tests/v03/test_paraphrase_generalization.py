from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, "src")

from experiment.v02.engine import ContextReasoningEngine, EngineConfig


FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "fixtures_package"


def _load_fixture(name: str):
    with (FIXTURE_ROOT / name).open("r", encoding="utf-8") as file:
        return json.load(file)


def _build_engine(
    customers: list[dict],
    opportunities: list[dict],
    communications: list[dict],
) -> ContextReasoningEngine:
    engine = ContextReasoningEngine(EngineConfig())
    engine.initialize_indexes(
        customers,
        opportunities,
        communications,
        "2026-09-13T12:00:00Z",
    )
    return engine


def _observable_state(result) -> tuple:
    """Compare behavioral output, excluding explanatory notes."""
    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.reversion,
        result.recommended_focus,
    )


PARAPHRASE_CASES = (
    (
        "F01-D1",
        "M001",
        "The customer is assessing the proposal and would like another "
        "discussion next week.",
        True,
    ),
    (
        "F02-D1",
        "M002",
        "The customer has budget approval for the quoted amount and says "
        "procurement is progressing.",
        True,
    ),
    (
        "F03-D1",
        "M004",
        "The customer says the revised commercial terms are unacceptable "
        "and wants the proposal reconsidered.",
        True,
    ),
    (
        "F04-D1",
        "M005",
        "The customer is discussing a different store rollout and says "
        "nothing about this quoted opportunity.",
        False,
    ),
    (
        "F10-D1",
        "M007",
        "The customer confirms the migration workshop is finished and asks "
        "what happens in the following handoff.",
        True,
    ),
)


@pytest.fixture()
def fixture_data():
    return (
        _load_fixture("fixtures/customers.json"),
        _load_fixture("fixtures/opportunities.json"),
        _load_fixture("fixtures/communications.json"),
        {
            case["pair_id"]: case
            for case in _load_fixture("fixtures/scenario_pairs.json")
        },
    )


@pytest.mark.parametrize(
    "pair_id,communication_id,paraphrase,known_v02_failure",
    PARAPHRASE_CASES,
)
def test_semantic_paraphrase_preserves_behavior(
    fixture_data,
    pair_id: str,
    communication_id: str,
    paraphrase: str,
    known_v02_failure: bool,
) -> None:
    customers, opportunities, communications, scenarios = fixture_data

    case = deepcopy(scenarios[pair_id])

    communication = next(
        item
        for item in communications
        if item["communication_id"] == communication_id
    )

    original_summary = communication["summary"]

    try:
        original_engine = _build_engine(
            customers,
            opportunities,
            communications,
        )
        original_result = original_engine.evaluate(
            case,
            phase="variant",
        )
        original_state = _observable_state(original_result)

        communication["summary"] = paraphrase

        paraphrase_engine = _build_engine(
            customers,
            opportunities,
            communications,
        )
        paraphrase_result = paraphrase_engine.evaluate(
            case,
            phase="variant",
        )
        paraphrase_state = _observable_state(paraphrase_result)

    finally:
        communication["summary"] = original_summary

    same_behavior = paraphrase_state == original_state

    if known_v02_failure:
        if same_behavior:
            pytest.fail(
                f"{pair_id}: v0.2 unexpectedly passed a previously "
                f"observed lexical-generalization failure"
            )

        pytest.xfail(
            "Known v0.2 lexical-generalization failure; "
            "this case becomes a v0.3 acceptance test after redesign."
        )

    assert same_behavior, (
        f"{pair_id}: semantic-preserving paraphrase changed behavior\n"
        f"original={original_state}\n"
        f"paraphrase={paraphrase_state}"
    )


def test_paraphrase_battery_contains_positive_and_negative_controls() -> None:
    expected = {
        "F01-D1",
        "F02-D1",
        "F03-D1",
        "F04-D1",
        "F10-D1",
    }

    observed = {
        pair_id
        for pair_id, _, _, _ in PARAPHRASE_CASES
    }

    assert observed == expected
    assert "F04-D1" in observed


def test_paraphrase_probe_uses_only_existing_fixture_cases() -> None:
    scenario_ids = {
        case["pair_id"]
        for case in _load_fixture("fixtures/scenario_pairs.json")
    }

    communication_ids = {
        communication["communication_id"]
        for communication in _load_fixture("fixtures/communications.json")
    }

    for pair_id, communication_id, _, _ in PARAPHRASE_CASES:
        assert pair_id in scenario_ids
        assert communication_id in communication_ids