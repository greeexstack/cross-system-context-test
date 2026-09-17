"""
Quarantine behavior under partial observability.

These tests probe how quarantine should behave when some evidence sources
are unavailable, fail, recover, or contribute only partial information.

This remains a test-layer experiment. No production code is changed.
"""


def _item(
    evidence_id,
    *,
    source_system,
    source_status="available",
    confirms_completion=False,
    requests_next_step=False,
    requests_followup=False,
    parent_ids=(),
):
    class Item:
        pass

    item = Item()
    item.evidence_id = evidence_id
    item.source_system = source_system
    item.source_status = source_status
    item.confirms_completion = confirms_completion
    item.requests_next_step = requests_next_step
    item.requests_followup = requests_followup
    item.parent_ids = tuple(parent_ids)
    return item


def _evaluate(items):
    """
    Candidate test-layer contract:

    1. Direct semantic conflicts quarantine an identity.
    2. Quarantine propagates through lineage.
    3. Source availability/failure does not erase an already-established
       quarantine.
    4. Unrelated healthy evidence remains independently usable.
    5. Recovery may add evidence but does not retroactively cleanse a
       conflicting identity.
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


def test_source_failure_does_not_clear_existing_quarantine():
    a = _item(
        "E1",
        source_system="source-a",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        source_system="source-b",
        requests_next_step=True,
    )

    initial = _evaluate([a, b])

    failed_b = _item(
        "E1",
        source_system="source-b",
        source_status="failed",
        requests_next_step=True,
    )

    degraded = _evaluate([a, failed_b])

    assert initial.quarantined_ids == {"E1"}
    assert degraded.quarantined_ids == {"E1"}
    assert "E1" not in degraded.accepted_ids


def test_unavailable_source_does_not_resurrect_quarantined_identity():
    a = _item(
        "E1",
        source_system="source-a",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        source_system="source-b",
        requests_next_step=True,
    )

    first = _evaluate([a, b])

    unavailable_b = _item(
        "E1",
        source_system="source-b",
        source_status="unavailable",
        requests_next_step=True,
    )

    later = _evaluate([a, unavailable_b])

    assert first.quarantined_ids == {"E1"}
    assert later.quarantined_ids == {"E1"}
    assert "E1" not in later.accepted_ids


def test_partial_source_set_does_not_make_conflicting_identity_accepted():
    a = _item(
        "E1",
        source_system="source-a",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        source_system="source-b",
        requests_next_step=True,
    )

    result = _evaluate([a, b])

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_healthy_unrelated_source_remains_accepted_during_failure():
    conflict_a = _item(
        "E1",
        source_system="source-a",
        confirms_completion=True,
    )
    conflict_b = _item(
        "E1",
        source_system="source-b",
        requests_next_step=True,
    )
    unrelated = _item(
        "E2",
        source_system="source-c",
        requests_followup=True,
    )

    failed = _item(
        "E1",
        source_system="source-b",
        source_status="failed",
        requests_next_step=True,
    )

    result = _evaluate(
        [conflict_a, failed, unrelated]
    )

    assert result.quarantined_ids == {"E1"}
    assert "E1" not in result.accepted_ids
    assert "E2" in result.accepted_ids


def test_child_of_quarantined_identity_stays_quarantined_when_parent_source_fails():
    parent_a = _item(
        "E1",
        source_system="source-a",
        confirms_completion=True,
    )
    parent_b = _item(
        "E1",
        source_system="source-b",
        requests_next_step=True,
    )
    child = _item(
        "E2",
        source_system="source-c",
        parent_ids=("E1",),
        requests_followup=True,
    )

    failed_parent = _item(
        "E1",
        source_system="source-b",
        source_status="failed",
        requests_next_step=True,
    )

    result = _evaluate(
        [parent_a, failed_parent, child]
    )

    assert result.quarantined_ids == {"E1", "E2"}
    assert result.accepted_ids == set()


def test_unrelated_lineage_remains_clean_when_one_branch_fails():
    conflict_a = _item(
        "E1",
        source_system="source-a",
        confirms_completion=True,
    )
    conflict_b = _item(
        "E1",
        source_system="source-b",
        requests_next_step=True,
    )
    poisoned_child = _item(
        "E2",
        source_system="source-c",
        parent_ids=("E1",),
    )

    clean_parent = _item(
        "E3",
        source_system="source-d",
        confirms_completion=True,
    )
    clean_child = _item(
        "E4",
        source_system="source-e",
        parent_ids=("E3",),
        requests_followup=True,
    )

    failed_conflict = _item(
        "E1",
        source_system="source-b",
        source_status="failed",
        requests_next_step=True,
    )

    result = _evaluate(
        [
            conflict_a,
            failed_conflict,
            poisoned_child,
            clean_parent,
            clean_child,
        ]
    )

    assert result.quarantined_ids == {"E1", "E2"}
    assert result.accepted_ids == {"E3", "E4"}


def test_source_recovery_does_not_remove_existing_quarantine():
    a = _item(
        "E1",
        source_system="source-a",
        confirms_completion=True,
    )
    failed_b = _item(
        "E1",
        source_system="source-b",
        source_status="failed",
        requests_next_step=True,
    )

    degraded = _evaluate([a, failed_b])

    recovered_b = _item(
        "E1",
        source_system="source-b",
        source_status="available",
        requests_next_step=True,
    )

    recovered = _evaluate([a, recovered_b])

    assert degraded.quarantined_ids == {"E1"}
    assert recovered.quarantined_ids == {"E1"}
    assert "E1" not in recovered.accepted_ids


def test_recovery_can_add_unrelated_evidence_without_cleansing_quarantine():
    a = _item(
        "E1",
        source_system="source-a",
        confirms_completion=True,
    )
    conflict = _item(
        "E1",
        source_system="source-b",
        requests_next_step=True,
    )

    recovery_evidence = _item(
        "E2",
        source_system="source-b",
        source_status="available",
        requests_followup=True,
    )

    result = _evaluate(
        [a, conflict, recovery_evidence]
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == {"E2"}


def test_repeated_source_failure_is_idempotent():
    a = _item(
        "E1",
        source_system="source-a",
        confirms_completion=True,
    )
    failed = _item(
        "E1",
        source_system="source-b",
        source_status="failed",
        requests_next_step=True,
    )

    first = _evaluate([a, failed])
    second = _evaluate([a, failed, failed])

    assert first.quarantined_ids == {"E1"}
    assert second.quarantined_ids == {"E1"}
    assert first.accepted_ids == second.accepted_ids == set()


def test_source_failure_does_not_spread_quarantine_without_lineage():
    a = _item(
        "E1",
        source_system="source-a",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        source_system="source-b",
        requests_next_step=True,
    )
    unrelated = _item(
        "E2",
        source_system="source-c",
        source_status="failed",
        requests_followup=True,
    )

    result = _evaluate([a, b, unrelated])

    assert result.quarantined_ids == {"E1"}
    assert "E2" in result.accepted_ids


def test_empty_observable_set_has_no_quarantine():
    result = _evaluate([])

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == set()


def test_all_known_results_remain_partitioned_under_partial_observability():
    e1a = _item(
        "E1",
        source_system="source-a",
        confirms_completion=True,
    )
    e1b = _item(
        "E1",
        source_system="source-b",
        requests_next_step=True,
    )
    e2 = _item(
        "E2",
        source_system="source-c",
        requests_followup=True,
    )
    e3 = _item(
        "E3",
        source_system="source-d",
        confirms_completion=True,
    )

    failed_e1b = _item(
        "E1",
        source_system="source-b",
        source_status="failed",
        requests_next_step=True,
    )

    result = _evaluate(
        [e1a, failed_e1b, e2, e3]
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == {"E2", "E3"}
    assert (
        result.quarantined_ids.isdisjoint(
            result.accepted_ids
        )
    )
    assert (
        result.quarantined_ids
        | result.accepted_ids
        == {"E1", "E2", "E3"}
    )