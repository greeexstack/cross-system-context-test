"""
Quarantine persistence and recovery.

Candidate test-layer contract:

- A computed quarantine state can be persisted and reconstructed.
- Rehydration must preserve quarantined/accepted partition exactly.
- Restart must not clear quarantine.
- Replayed evidence after restart must not change the result unexpectedly.
- Duplicate snapshots are idempotent.
- Partial/corrupt persistence must fail closed rather than silently accept
  a quarantined identity.
- A valid explicit release must survive restart.
- A stale release must remain invalid after restart.
- Serialization order must not affect the recovered state.

This is intentionally test-layer work. No production behavior is changed.
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


def _payload(item):
    return (
        item.confirms_completion,
        item.requests_next_step,
        item.requests_followup,
    )


def _fingerprint(items, identity):
    return tuple(
        sorted(
            {
                _payload(item)
                for item in items
                if item.evidence_id == identity
            }
        )
    )


def _evaluate(items):
    items = tuple(items)

    by_id = {}
    parents_by_id = {}

    for item in items:
        by_id.setdefault(item.evidence_id, []).append(item)
        parents_by_id.setdefault(
            item.evidence_id,
            set(),
        ).update(item.parent_ids)

    quarantined = {
        identity
        for identity, members in by_id.items()
        if len({_payload(member) for member in members}) > 1
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
    result.quarantined_ids = frozenset(quarantined)
    result.accepted_ids = accepted
    return result


def _snapshot(result):
    return {
        "quarantined_ids": tuple(
            sorted(result.quarantined_ids)
        ),
        "accepted_ids": tuple(
            sorted(result.accepted_ids)
        ),
        "version": 1,
    }


def _restore(snapshot):
    if not isinstance(snapshot, dict):
        raise ValueError("invalid snapshot")

    if snapshot.get("version") != 1:
        raise ValueError("unsupported snapshot version")

    quarantined = snapshot.get("quarantined_ids")
    accepted = snapshot.get("accepted_ids")

    if not isinstance(quarantined, (tuple, list)):
        raise ValueError("invalid quarantine set")

    if not isinstance(accepted, (tuple, list)):
        raise ValueError("invalid accepted set")

    quarantined = frozenset(quarantined)
    accepted = set(accepted)

    if quarantined & accepted:
        raise ValueError("overlapping state partitions")

    class State:
        pass

    state = State()
    state.quarantined_ids = quarantined
    state.accepted_ids = accepted
    return state


def _apply_release(state, identity):
    quarantined = set(state.quarantined_ids)
    accepted = set(state.accepted_ids)

    if identity in quarantined:
        quarantined.remove(identity)
        accepted.add(identity)

    class State:
        pass

    result = State()
    result.quarantined_ids = frozenset(quarantined)
    result.accepted_ids = accepted
    return result


def _merge_recovered_with_new_state(snapshot, items):
    persisted = _restore(snapshot)
    current = _evaluate(items)

    # Persisted quarantine is sticky across recovery, while newly observed
    # quarantine is added to it.
    quarantined = set(
        persisted.quarantined_ids
        | current.quarantined_ids
    )

    # Newly observed clean evidence is allowed to become accepted.
    # Anything that is currently quarantined is always excluded.
    accepted = set(current.accepted_ids) - quarantined

    class State:
        pass

    result = State()
    result.quarantined_ids = frozenset(quarantined)
    result.accepted_ids = accepted
    return result


def test_snapshot_round_trip_preserves_quarantine_state():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
        _item("E2", requests_followup=True),
    ]

    result = _evaluate(items)
    snapshot = _snapshot(result)
    restored = _restore(snapshot)

    assert restored.quarantined_ids == result.quarantined_ids
    assert restored.accepted_ids == result.accepted_ids


def test_restart_does_not_clear_quarantine():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]

    before_restart = _evaluate(items)
    after_restart = _restore(
        _snapshot(before_restart)
    )

    assert before_restart.quarantined_ids == {"E1"}
    assert after_restart.quarantined_ids == {"E1"}
    assert "E1" not in after_restart.accepted_ids


def test_restart_preserves_clean_identity():
    clean = [
        _item("E1", confirms_completion=True),
    ]

    result = _evaluate(clean)
    restored = _restore(_snapshot(result))

    assert restored.quarantined_ids == frozenset()
    assert restored.accepted_ids == {"E1"}


def test_restart_preserves_lineage_quarantine():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
        _item("E2", parent_ids=("E1",)),
        _item("E3", parent_ids=("E2",)),
    ]

    result = _evaluate(items)
    restored = _restore(_snapshot(result))

    assert restored.quarantined_ids == {
        "E1",
        "E2",
        "E3",
    }
    assert restored.accepted_ids == set()


def test_snapshot_is_order_independent():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
        _item("E2", requests_followup=True),
    ]

    result = _evaluate(items)
    snapshot = _snapshot(result)

    reordered_snapshot = {
        "version": 1,
        "quarantined_ids": tuple(
            reversed(snapshot["quarantined_ids"])
        ),
        "accepted_ids": tuple(
            reversed(snapshot["accepted_ids"])
        ),
    }

    restored_a = _restore(snapshot)
    restored_b = _restore(reordered_snapshot)

    assert restored_a.quarantined_ids == restored_b.quarantined_ids
    assert restored_a.accepted_ids == restored_b.accepted_ids


def test_duplicate_snapshot_restore_is_idempotent():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]

    result = _evaluate(items)
    snapshot = _snapshot(result)

    first = _restore(snapshot)
    second = _restore(snapshot)

    assert first.quarantined_ids == second.quarantined_ids
    assert first.accepted_ids == second.accepted_ids


def test_replayed_evidence_after_restart_does_not_resurrect_identity():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]

    before = _evaluate(items)
    restored = _restore(_snapshot(before))

    replayed = _evaluate(
        items + [
            _item("E1", confirms_completion=True),
        ]
    )

    assert restored.quarantined_ids == {"E1"}
    assert replayed.quarantined_ids == {"E1"}
    assert "E1" not in replayed.accepted_ids


def test_new_benign_evidence_after_restart_does_not_clear_quarantine():
    initial = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]

    initial_state = _evaluate(initial)
    snapshot = _snapshot(initial_state)

    after_restart = _merge_recovered_with_new_state(
        snapshot,
        initial + [
            _item("E2", requests_followup=True),
        ],
    )

    assert after_restart.quarantined_ids == {"E1"}
    assert after_restart.accepted_ids == {"E2"}


def test_recovery_can_retain_independent_clean_branch():
    initial = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
        _item("E2", confirms_completion=True),
        _item("E3", parent_ids=("E2",)),
    ]

    initial_state = _evaluate(initial)
    restored = _restore(_snapshot(initial_state))

    assert restored.quarantined_ids == {"E1"}
    assert restored.accepted_ids == {"E2", "E3"}


def test_release_survives_restart():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]

    quarantined = _evaluate(items)

    released = _apply_release(
        _restore(_snapshot(quarantined)),
        "E1",
    )

    restarted = _restore(
        _snapshot(released)
    )

    assert released.quarantined_ids == frozenset()
    assert restarted.quarantined_ids == frozenset()
    assert restarted.accepted_ids == {"E1"}


def test_stale_state_cannot_be_cleansed_by_restart():
    old_items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]

    old_state = _evaluate(old_items)
    old_snapshot = _snapshot(old_state)

    current_items = old_items + [
        _item("E1", requests_followup=True),
    ]

    merged = _merge_recovered_with_new_state(
        old_snapshot,
        current_items,
    )

    assert merged.quarantined_ids == {"E1"}
    assert merged.accepted_ids == set()


def test_partial_snapshot_fails_closed():
    with_errors = [
        {
            "version": 1,
            "quarantined_ids": ("E1",),
        },
        {
            "version": 1,
            "accepted_ids": ("E1",),
        },
        {
            "quarantined_ids": ("E1",),
            "accepted_ids": (),
        },
    ]

    for snapshot in with_errors:
        try:
            restored = _restore(snapshot)
        except ValueError:
            continue

        assert restored.quarantined_ids & {"E1"}
        assert "E1" not in restored.accepted_ids


def test_overlapping_snapshot_partitions_fail_closed():
    snapshot = {
        "version": 1,
        "quarantined_ids": ("E1",),
        "accepted_ids": ("E1",),
    }

    try:
        _restore(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "overlapping partitions must be rejected"
    )


def test_unknown_snapshot_version_is_rejected():
    snapshot = {
        "version": 999,
        "quarantined_ids": ("E1",),
        "accepted_ids": (),
    }

    try:
        _restore(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "unknown snapshot version must be rejected"
    )


def test_non_dict_snapshot_is_rejected():
    for value in (None, [], (), "snapshot", 42):
        try:
            _restore(value)
        except ValueError:
            continue

        raise AssertionError(
            "non-dict snapshot must be rejected"
        )


def test_recovery_is_monotonic_for_quarantine():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]

    before = _evaluate(items)
    snapshot = _snapshot(before)

    after = _merge_recovered_with_new_state(
        snapshot,
        items + [
            _item("E2", requests_followup=True),
        ],
    )

    assert before.quarantined_ids <= after.quarantined_ids
    assert after.quarantined_ids == {"E1"}


def test_recovery_does_not_import_unrelated_quarantine():
    initial = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]

    snapshot = _snapshot(_evaluate(initial))

    current = [
        _item("E2", confirms_completion=True),
    ]

    recovered = _merge_recovered_with_new_state(
        snapshot,
        current,
    )

    assert recovered.quarantined_ids == {"E1"}
    assert recovered.accepted_ids == {"E2"}


def test_recovered_state_is_partitioned():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
        _item("E2", requests_followup=True),
    ]

    state = _restore(
        _snapshot(_evaluate(items))
    )

    assert state.quarantined_ids.isdisjoint(
        state.accepted_ids
    )

    assert (
        state.quarantined_ids
        | state.accepted_ids
        == {"E1", "E2"}
    )


def test_many_restart_cycles_preserve_state():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
        _item("E2", requests_followup=True),
        _item("E3", confirms_completion=True),
    ]

    state = _evaluate(items)

    for _ in range(10):
        state = _restore(_snapshot(state))

    assert state.quarantined_ids == {"E1"}
    assert state.accepted_ids == {"E2", "E3"}


def test_release_then_new_conflict_after_restart_is_quarantined_again():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]

    first = _evaluate(items)
    released = _apply_release(
        _restore(_snapshot(first)),
        "E1",
    )

    restarted = _restore(
        _snapshot(released)
    )

    changed = _evaluate(
        items + [
            _item("E1", requests_followup=True),
        ]
    )

    assert restarted.quarantined_ids == frozenset()
    assert restarted.accepted_ids == {"E1"}

    assert changed.quarantined_ids == {"E1"}
    assert changed.accepted_ids == set()


def test_snapshot_recovery_is_deterministic():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
        _item("E2", confirms_completion=True),
        _item("E3", parent_ids=("E2",)),
    ]

    result = _evaluate(items)

    snapshots = [
        _snapshot(result),
        _snapshot(result),
        {
            "version": 1,
            "quarantined_ids": tuple(
                sorted(result.quarantined_ids)
            ),
            "accepted_ids": tuple(
                sorted(result.accepted_ids)
            ),
        },
    ]

    restored = [
        _restore(snapshot)
        for snapshot in snapshots
    ]

    assert all(
        state.quarantined_ids == restored[0].quarantined_ids
        for state in restored
    )
    assert all(
        state.accepted_ids == restored[0].accepted_ids
        for state in restored
    )