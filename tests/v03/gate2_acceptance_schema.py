from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SEMANTIC_FIELDS = frozenset(
    {
        "topic",
        "polarity",
        "negated_concepts",
        "requests_followup",
        "expresses_acceptance",
        "expresses_rejection",
        "confirms_approval",
        "confirms_completion",
        "requests_next_step",
        "concerns_same_work_item",
    }
)

REQUIRED_ROLES = frozenset(
    {
        "relevant",
        "supporting",
        "contradictory",
        "irrelevant",
        "service-next-step",
    }
)


@dataclass(frozen=True)
class Gate2Case:
    case_id: str
    role: str
    primary: dict[str, Any]
    primary_state: dict[str, str]
    customer: dict[str, Any]
    occurred_at: str
    texts: tuple[str, ...]
    oracle: tuple[tuple[str, object], ...]


def _validate_semantic_oracle(
    oracle: tuple[tuple[str, object], ...],
) -> None:
    seen: set[str] = set()

    for field, value in oracle:
        assert field in SEMANTIC_FIELDS
        assert field not in seen
        seen.add(field)

        if field == "topic":
            assert value is None or isinstance(value, str)
        elif field == "polarity":
            assert isinstance(value, str)
        elif field == "negated_concepts":
            assert isinstance(value, tuple)
            assert all(isinstance(item, str) for item in value)
        else:
            assert value is None or isinstance(value, bool)


def validate_case(case: Gate2Case) -> None:
    assert case.case_id.strip()
    assert case.role in REQUIRED_ROLES

    assert len(case.texts) == 4
    assert all(
        isinstance(text, str) and text.strip()
        for text in case.texts
    )

    primary = case.primary

    assert primary["record_id"].strip()
    assert primary["record_type"].strip()
    assert primary["summary"].strip()
    assert primary["customer_id"].strip()

    primary_state = case.primary_state

    assert primary_state["interpretation_class"].strip()
    assert primary_state["decision_strength"].strip()

    customer = case.customer

    assert customer["customer_id"].strip()
    assert customer["customer_id"] == primary["customer_id"]
    assert customer["name"].strip()
    assert customer["email"].strip()
    assert customer["phone"].strip()

    assert case.occurred_at.strip()

    _validate_semantic_oracle(case.oracle)


def validate_suite(
    cases: tuple[Gate2Case, ...],
) -> None:
    assert len(cases) == 5

    case_ids = [case.case_id for case in cases]
    assert len(case_ids) == len(set(case_ids))

    roles = [case.role for case in cases]
    assert len(roles) == len(set(roles))
    assert set(roles) == REQUIRED_ROLES

    for case in cases:
        validate_case(case)


def _oracle_tuple(
    raw_oracle: dict[str, Any],
) -> tuple[tuple[str, object], ...]:
    items: list[tuple[str, object]] = []

    for field, value in raw_oracle.items():
        if field == "negated_concepts" and isinstance(value, list):
            value = tuple(value)

        items.append((field, value))

    return tuple(items)


def load_suite(
    path: str | Path,
) -> tuple[Gate2Case, ...]:
    fixture_path = Path(path)

    with fixture_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        raise ValueError("fixture root must be a JSON array")

    cases: list[Gate2Case] = []

    for raw in payload:
        if not isinstance(raw, dict):
            raise ValueError("each fixture case must be an object")

        cases.append(
            Gate2Case(
                case_id=raw["case_id"],
                role=raw["role"],
                primary=dict(raw["primary"]),
                primary_state=dict(raw["primary_state"]),
                customer=dict(raw["customer"]),
                occurred_at=raw["occurred_at"],
                texts=tuple(raw["texts"]),
                oracle=_oracle_tuple(raw["oracle"]),
            )
        )

    suite = tuple(cases)
    validate_suite(suite)
    return suite