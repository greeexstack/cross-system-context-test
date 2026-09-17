"""
Quarantine inheritance through derived lineage.

These tests define a safety invariant for the composition boundary:

Once an evidence identity is quarantined, a derived identity that depends
on that quarantined evidence must not be treated as clean/accepted.

This is intentionally a test-layer experiment. Production code is unchanged.
"""


def _item(
    evidence_id,
    *,
    parent_ids=(),
    confirms_completion=False,
    requests_next_step=False,
    requests_followup=False,
):
    class Item:
        pass

    item = Item()
    item.evidence_id = evidence_id
    item.parent_ids = tuple(parent_ids)
    item.confirms_completion = confirms_completion
    item.requests_next_step = requests_next_step
    item.requests_followup = requests_followup
    return item


def _quarantine_with_lineage(items):
    """
    Candidate quarantine model.

    Step 1: identify directly conflicting identities from semantic payload.
    Step 2: propagate quarantine to any descendant whose parent lineage
            contains a quarantined identity.
    """
    items = tuple(items)

    by_id = {}
    parents_by_id = {}

    for item in items:
        identity = item.evidence_id
        payload = (
            item.confirms_completion,
            item.requests_next_step,
            item.requests_followup,
        )

        by_id.setdefault(identity, set()).add(payload)
        parents_by_id.setdefault(identity, set()).update(item.parent_ids)

    quarantined = {
        identity
        for identity, payloads in by_id.items()
        if len(payloads) > 1
    }

    changed = True
    while changed:
        changed = False

        for identity, parent_ids in parents_by_id.items():
            if identity in quarantined:
                continue

            if parent_ids & quarantined:
                quarantined.add(identity)
                changed = True

    accepted = set(by_id) - quarantined

    class Result:
        pass

    result = Result()
    result.accepted_ids = accepted
    result.quarantined_ids = frozenset(quarantined)
    return result


def test_direct_conflict_still_seeds_quarantine():
    clean = _item("E1", confirms_completion=True)
    conflict = _item("E1", requests_next_step=True)

    result = _quarantine_with_lineage([clean, conflict])

    assert result.quarantined_ids == {"E1"}
    assert "E1" not in result.accepted_ids


def test_child_of_quarantined_identity_is_also_quarantined():
    clean = _item("E1", confirms_completion=True)
    conflict = _item("E1", requests_next_step=True)
    child = _item(
        "E2",
        parent_ids=("E1",),
        requests_followup=True,
    )

    result = _quarantine_with_lineage([clean, conflict, child])

    assert result.quarantined_ids == {"E1", "E2"}
    assert "E2" not in result.accepted_ids


def test_grandchild_of_quarantined_identity_is_quarantined():
    clean = _item("E1", confirms_completion=True)
    conflict = _item("E1", requests_next_step=True)
    child = _item("E2", parent_ids=("E1",))
    grandchild = _item("E3", parent_ids=("E2",))

    result = _quarantine_with_lineage(
        [clean, conflict, child, grandchild]
    )

    assert result.quarantined_ids == {"E1", "E2", "E3"}
    assert result.accepted_ids == set()


def test_clean_branch_remains_accepted_when_other_branch_is_quarantined():
    e1a = _item("E1", confirms_completion=True)
    e1b = _item("E1", requests_next_step=True)

    clean_parent = _item("E2", confirms_completion=True)
    clean_child = _item(
        "E3",
        parent_ids=("E2",),
        requests_followup=True,
    )

    result = _quarantine_with_lineage(
        [e1a, e1b, clean_parent, clean_child]
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == {"E2", "E3"}


def test_multi_parent_child_is_quarantined_when_any_parent_is_quarantined():
    e1a = _item("E1", confirms_completion=True)
    e1b = _item("E1", requests_next_step=True)
    e2 = _item("E2", confirms_completion=True)

    child = _item(
        "E3",
        parent_ids=("E1", "E2"),
        requests_followup=True,
    )

    result = _quarantine_with_lineage(
        [e1a, e1b, e2, child]
    )

    assert result.quarantined_ids == {"E1", "E3"}
    assert "E2" in result.accepted_ids
    assert "E3" not in result.accepted_ids


def test_parent_order_does_not_change_inheritance():
    e1a = _item("E1", confirms_completion=True)
    e1b = _item("E1", requests_next_step=True)
    clean = _item("E2", confirms_completion=True)

    forward = _item(
        "E3",
        parent_ids=("E1", "E2"),
        requests_followup=True,
    )
    reverse = _item(
        "E4",
        parent_ids=("E2", "E1"),
        requests_followup=True,
    )

    result = _quarantine_with_lineage(
        [e1a, e1b, clean, forward, reverse]
    )

    assert result.quarantined_ids == {"E1", "E3", "E4"}
    assert "E2" in result.accepted_ids


def test_duplicate_child_does_not_escape_parent_quarantine():
    e1a = _item("E1", confirms_completion=True)
    e1b = _item("E1", requests_next_step=True)

    child1 = _item(
        "E2",
        parent_ids=("E1",),
        requests_followup=True,
    )
    child2 = _item(
        "E2",
        parent_ids=("E1",),
        requests_followup=True,
    )

    result = _quarantine_with_lineage(
        [e1a, e1b, child1, child2]
    )

    assert result.quarantined_ids == {"E1", "E2"}
    assert "E2" not in result.accepted_ids


def test_metadata_free_child_cannot_hide_quarantined_parent():
    e1a = _item("E1", confirms_completion=True)
    e1b = _item("E1", requests_next_step=True)

    child = _item(
        "E2",
        parent_ids=("E1",),
    )

    result = _quarantine_with_lineage([e1a, e1b, child])

    assert "E1" in result.quarantined_ids
    assert "E2" in result.quarantined_ids
    assert result.accepted_ids == set()


def test_independent_child_does_not_inherit_unrelated_quarantine():
    e1a = _item("E1", confirms_completion=True)
    e1b = _item("E1", requests_next_step=True)

    e2 = _item("E2", confirms_completion=True)
    independent = _item(
        "E3",
        parent_ids=("E2",),
        requests_followup=True,
    )

    result = _quarantine_with_lineage(
        [e1a, e1b, e2, independent]
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == {"E2", "E3"}


def test_late_arriving_parent_conflict_invalidates_existing_descendant():
    parent = _item("E1", confirms_completion=True)
    child = _item(
        "E2",
        parent_ids=("E1",),
        requests_followup=True,
    )

    initial = _quarantine_with_lineage([parent, child])

    conflicting_parent = _item(
        "E1",
        requests_next_step=True,
    )

    expanded = _quarantine_with_lineage(
        [parent, child, conflicting_parent]
    )

    assert initial.quarantined_ids == frozenset()
    assert initial.accepted_ids == {"E1", "E2"}

    assert expanded.quarantined_ids == {"E1", "E2"}
    assert expanded.accepted_ids == set()


def test_recomputation_is_idempotent_for_quarantine_inheritance():
    e1a = _item("E1", confirms_completion=True)
    e1b = _item("E1", requests_next_step=True)
    e2 = _item("E2", parent_ids=("E1",))
    e3 = _item("E3", parent_ids=("E2",))

    items = [e1a, e1b, e2, e3]

    first = _quarantine_with_lineage(items)
    second = _quarantine_with_lineage(items)
    third = _quarantine_with_lineage(
        [e3, e2, e1b, e1a]
    )

    assert first.quarantined_ids == second.quarantined_ids
    assert second.quarantined_ids == third.quarantined_ids

    assert first.accepted_ids == second.accepted_ids
    assert second.accepted_ids == third.accepted_ids


def test_unrelated_quarantine_does_not_cross_into_sibling_branch():
    e1a = _item("E1", confirms_completion=True)
    e1b = _item("E1", requests_next_step=True)

    left = _item("E2", parent_ids=("E1",))
    right = _item("E3", confirms_completion=True)
    right_child = _item(
        "E4",
        parent_ids=("E3",),
        requests_followup=True,
    )

    result = _quarantine_with_lineage(
        [e1a, e1b, left, right, right_child]
    )

    assert result.quarantined_ids == {"E1", "E2"}
    assert result.accepted_ids == {"E3", "E4"}