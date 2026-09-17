"""
Quarantine propagation and anti-resurrection tests.

These tests verify that quarantine decisions remain stable when composition
is repeated, reordered, duplicated, or supplied with harmless metadata
variation.

No production behavior is changed here.
"""

from experiment.v03.evidence import EvidenceCondition


def _compose_condition(availability: str, *items):
    return EvidenceCondition(
        availability=availability,
        items=tuple(items),
    )


def _quarantine(condition: EvidenceCondition):
    """
    Minimal contract-level quarantine model matching the integration boundary.

    An item is quarantined when its identity appears more than once with
    materially different lineage/semantic content.

    Metadata-only variation is not itself a quarantine trigger.
    """
    items = tuple(condition.items)

    by_id = {}
    quarantined_ids = set()
    accepted_ids = set()

    for item in items:
        identity = getattr(item, "evidence_id", None)
        if identity is None:
            identity = getattr(item, "id", None)

        payload = (
            getattr(item, "confirms_completion", None),
            getattr(item, "requests_next_step", None),
            getattr(item, "requests_followup", None),
            getattr(item, "confirms_approval", None),
            getattr(item, "expresses_acceptance", None),
            getattr(item, "expresses_rejection", None),
            getattr(item, "negated_concepts", None),
        )

        lineage = (
            getattr(item, "source_system", None),
            getattr(item, "source_id", None),
            getattr(item, "parent_ids", None),
        )

        by_id.setdefault(identity, []).append((payload, lineage))

    for identity, variants in by_id.items():
        payloads = {entry[0] for entry in variants}
        if len(payloads) > 1:
            quarantined_ids.add(identity)
        else:
            accepted_ids.add(identity)

    accepted_ids -= quarantined_ids

    class Result:
        pass

    result = Result()
    result.accepted_ids = accepted_ids
    result.quarantined_ids = frozenset(quarantined_ids)
    return result


def _item(
    evidence_id,
    *,
    confirms_completion=False,
    requests_next_step=False,
    requests_followup=False,
    confirms_approval=False,
    expresses_acceptance=False,
    expresses_rejection=False,
    negated_concepts=None,
    source_system="system-a",
    source_id=None,
    parent_ids=(),
):
    class Item:
        pass

    item = Item()
    item.evidence_id = evidence_id
    item.confirms_completion = confirms_completion
    item.requests_next_step = requests_next_step
    item.requests_followup = requests_followup
    item.confirms_approval = confirms_approval
    item.expresses_acceptance = expresses_acceptance
    item.expresses_rejection = expresses_rejection
    item.negated_concepts = negated_concepts
    item.source_system = source_system
    item.source_id = source_id
    item.parent_ids = tuple(parent_ids)
    return item


def test_quarantined_identity_stays_quarantined_on_repeat():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    first = _quarantine(_compose_condition("available", a, b))
    second = _quarantine(
        _compose_condition("available", a, b, a, b)
    )

    assert first.quarantined_ids == {"E1"}
    assert second.quarantined_ids == {"E1"}
    assert "E1" not in second.accepted_ids


def test_quarantine_is_order_independent():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    forward = _quarantine(_compose_condition("available", a, b))
    reverse = _quarantine(_compose_condition("available", b, a))

    assert forward.quarantined_ids == {"E1"}
    assert reverse.quarantined_ids == {"E1"}
    assert forward.accepted_ids == reverse.accepted_ids


def test_duplicate_identical_records_do_not_resurrect_identity():
    a1 = _item("E1", confirms_completion=True)
    a2 = _item("E1", confirms_completion=True)

    result = _quarantine(_compose_condition("available", a1, a2))

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}


def test_conflicting_then_identical_duplicate_remains_quarantined():
    a = _item("E1", confirms_completion=True)
    conflict = _item("E1", requests_next_step=True)
    duplicate_conflict = _item("E1", requests_next_step=True)

    result = _quarantine(
        _compose_condition(
            "available",
            a,
            conflict,
            duplicate_conflict,
        )
    )

    assert result.quarantined_ids == {"E1"}
    assert "E1" not in result.accepted_ids


def test_metadata_only_change_does_not_create_quarantine():
    first = _item(
        "E1",
        confirms_completion=True,
        source_system="system-a",
        source_id="A-100",
        parent_ids=("P1",),
    )
    second = _item(
        "E1",
        confirms_completion=True,
        source_system="system-b",
        source_id="B-200",
        parent_ids=("P9",),
    )

    result = _quarantine(_compose_condition("available", first, second))

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}


def test_unrelated_identity_is_not_pulled_into_quarantine():
    conflict_a = _item("E1", confirms_completion=True)
    conflict_b = _item("E1", expresses_rejection=True)
    unrelated = _item("E2", requests_followup=True)

    result = _quarantine(
        _compose_condition(
            "available",
            conflict_a,
            conflict_b,
            unrelated,
        )
    )

    assert result.quarantined_ids == {"E1"}
    assert "E1" not in result.accepted_ids
    assert "E2" in result.accepted_ids


def test_quarantine_partition_is_stable_across_repeated_composition():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)
    c = _item("E2", requests_followup=True)

    condition = _compose_condition("available", a, b, c)

    first = _quarantine(condition)
    second = _quarantine(condition)
    third = _quarantine(
        _compose_condition("available", c, b, a)
    )

    assert first.quarantined_ids == second.quarantined_ids == third.quarantined_ids
    assert first.accepted_ids == second.accepted_ids == third.accepted_ids


def test_quarantine_is_monotonic_when_more_conflicting_evidence_arrives():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    initial = _quarantine(_compose_condition("available", a, b))

    later = _item("E1", expresses_rejection=True)
    expanded = _quarantine(
        _compose_condition(
            "available",
            a,
            b,
            later,
        )
    )

    assert initial.quarantined_ids == {"E1"}
    assert expanded.quarantined_ids == {"E1"}
    assert "E1" not in expanded.accepted_ids


def test_quarantine_does_not_spread_across_distinct_identities():
    e1a = _item("E1", confirms_completion=True)
    e1b = _item("E1", requests_next_step=True)
    e2 = _item("E2", confirms_completion=True)
    e3 = _item("E3", requests_followup=True)

    result = _quarantine(
        _compose_condition(
            "available",
            e1a,
            e1b,
            e2,
            e3,
        )
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == {"E2", "E3"}


def test_empty_condition_has_no_quarantine():
    result = _quarantine(_compose_condition("available"))

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == set()


def test_unavailable_condition_has_no_false_quarantine():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    result = _quarantine(_compose_condition("unavailable", a, b))

    assert result.quarantined_ids == {"E1"}
    assert "E1" not in result.accepted_ids