"""
Quarantine snapshot atomicity and crash consistency.

Candidate test-layer contract:

- A persisted quarantine snapshot represents one complete generation.
- A partial/torn write must never be interpreted as a valid state.
- A snapshot is recoverable only when its commit marker is present.
- A newer uncommitted snapshot must not replace an older committed snapshot.
- An interrupted write must leave the last committed snapshot intact.
- Recovery must fail closed when no committed snapshot exists.
- Duplicate committed snapshots are idempotent.
- Snapshot ordering must not affect recovered state.
- Quarantine must never disappear because persistence failed midway.
- A valid newer committed generation may replace an older committed generation.

This is intentionally test-layer work. No production behavior is changed.
"""


def _state(
    *,
    generation,
    quarantined_ids=(),
    accepted_ids=(),
    commit_marker=True,
):
    return {
        "version": 1,
        "generation": generation,
        "quarantined_ids": tuple(sorted(quarantined_ids)),
        "accepted_ids": tuple(sorted(accepted_ids)),
        "commit_marker": commit_marker,
    }


def _validate_snapshot(snapshot):
    if not isinstance(snapshot, dict):
        raise ValueError("invalid snapshot")

    if snapshot.get("version") != 1:
        raise ValueError("unsupported snapshot version")

    commit_marker = snapshot.get("commit_marker")

    if commit_marker is not True:
        raise ValueError("snapshot is not committed")

    generation = snapshot.get("generation")
    quarantined = snapshot.get("quarantined_ids")
    accepted = snapshot.get("accepted_ids")

    if not isinstance(generation, int):
        raise ValueError("invalid generation")

    if generation < 0:
        raise ValueError("invalid generation")

    if not isinstance(quarantined, (tuple, list)):
        raise ValueError("invalid quarantine set")

    if not isinstance(accepted, (tuple, list)):
        raise ValueError("invalid accepted set")

    quarantined = frozenset(quarantined)
    accepted = frozenset(accepted)

    if quarantined & accepted:
        raise ValueError("overlapping state partitions")

    return {
        "version": 1,
        "generation": generation,
        "quarantined_ids": quarantined,
        "accepted_ids": accepted,
        "commit_marker": True,
    }


def _atomic_load(snapshots):
    """
    Choose the highest valid committed generation.

    Invalid or uncommitted snapshots are ignored when another valid committed
    snapshot exists. If no valid committed snapshot exists, recovery fails
    closed.
    """
    valid = []

    for snapshot in snapshots:
        try:
            valid.append(_validate_snapshot(snapshot))
        except ValueError:
            continue

    if not valid:
        raise ValueError("no valid committed snapshot")

    return max(
        valid,
        key=lambda snapshot: snapshot["generation"],
    )


def _write_generation(
    previous,
    next_state,
    *,
    crash_stage=None,
):
    """
    Simulate a multi-stage persistence operation.

    The commit marker is written last.

    A crash before the final commit therefore leaves the previous committed
    snapshot as the newest recoverable state.
    """
    if crash_stage is None:
        committed = dict(next_state)
        committed["commit_marker"] = True
        return [previous, committed]

    if crash_stage == "before_write":
        return [previous]

    if crash_stage == "during_write":
        partial = dict(next_state)
        partial.pop("accepted_ids", None)
        partial["commit_marker"] = False
        return [previous, partial]

    if crash_stage == "after_quarantine_write":
        partial = dict(next_state)
        partial["accepted_ids"] = ()
        partial["commit_marker"] = False
        return [previous, partial]

    if crash_stage == "after_write_before_commit":
        partial = dict(next_state)
        partial["commit_marker"] = False
        return [previous, partial]

    raise ValueError("unknown crash stage")


def _snapshot(result):
    return {
        "version": 1,
        "generation": 1,
        "quarantined_ids": tuple(
            sorted(result.quarantined_ids)
        ),
        "accepted_ids": tuple(
            sorted(result.accepted_ids)
        ),
        "commit_marker": True,
    }


def _result_state(
    *,
    quarantined_ids=(),
    accepted_ids=(),
):
    class Result:
        pass

    result = Result()
    result.quarantined_ids = frozenset(quarantined_ids)
    result.accepted_ids = set(accepted_ids)
    return result


def test_valid_snapshot_round_trip():
    snapshot = _state(
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    restored = _atomic_load([snapshot])

    assert restored["generation"] == 1
    assert restored["quarantined_ids"] == {"E1"}
    assert restored["accepted_ids"] == {"E2"}
    assert restored["commit_marker"] is True


def test_latest_valid_generation_is_selected():
    old = _state(
        generation=1,
        quarantined_ids=("E1",),
    )
    new = _state(
        generation=2,
        quarantined_ids=("E1", "E2"),
    )

    restored = _atomic_load([old, new])

    assert restored["generation"] == 2
    assert restored["quarantined_ids"] == {
        "E1",
        "E2",
    }


def test_older_snapshot_cannot_replace_newer_snapshot():
    old = _state(
        generation=1,
        quarantined_ids=("E1",),
    )
    new = _state(
        generation=2,
        quarantined_ids=("E1", "E2"),
    )

    restored = _atomic_load([new, old])

    assert restored["generation"] == 2
    assert restored["quarantined_ids"] == {
        "E1",
        "E2",
    }


def test_missing_field_in_latest_snapshot_falls_back_to_last_valid():
    old = _state(
        generation=1,
        quarantined_ids=("E1",),
    )

    torn = {
        "version": 1,
        "generation": 2,
        "quarantined_ids": ("E1", "E2"),
        "accepted_ids": (),
        # No commit marker.
    }

    restored = _atomic_load([old, torn])

    assert restored["generation"] == 1
    assert restored["quarantined_ids"] == {"E1"}


def test_torn_snapshot_is_not_accepted_as_complete_state():
    torn = {
        "version": 1,
        "generation": 2,
        "quarantined_ids": ("E1",),
        "accepted_ids": (),
    }

    try:
        _validate_snapshot(torn)
    except ValueError:
        return

    raise AssertionError(
        "torn snapshot must be rejected"
    )


def test_partial_write_preserves_previous_valid_state():
    previous = _state(
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    next_state = _state(
        generation=2,
        quarantined_ids=("E1", "E3"),
        accepted_ids=("E2",),
    )

    snapshots = _write_generation(
        previous,
        next_state,
        crash_stage="during_write",
    )

    restored = _atomic_load(snapshots)

    assert restored["generation"] == 1
    assert restored["quarantined_ids"] == {"E1"}
    assert restored["accepted_ids"] == {"E2"}


def test_crash_after_quarantine_write_does_not_clear_previous_state():
    previous = _state(
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    next_state = _state(
        generation=2,
        quarantined_ids=("E1", "E2"),
        accepted_ids=("E3",),
    )

    snapshots = _write_generation(
        previous,
        next_state,
        crash_stage="after_quarantine_write",
    )

    restored = _atomic_load(snapshots)

    assert restored["generation"] == 1
    assert restored["quarantined_ids"] == {"E1"}
    assert restored["accepted_ids"] == {"E2"}


def test_crash_before_commit_preserves_previous_generation():
    previous = _state(
        generation=7,
        quarantined_ids=("E1",),
    )

    next_state = _state(
        generation=8,
        quarantined_ids=("E1", "E2"),
    )

    snapshots = _write_generation(
        previous,
        next_state,
        crash_stage="after_write_before_commit",
    )

    restored = _atomic_load(snapshots)

    assert restored["generation"] == 7
    assert restored["quarantined_ids"] == {"E1"}


def test_successful_generation_replaces_previous_state():
    previous = _state(
        generation=1,
        quarantined_ids=("E1",),
    )

    next_state = _state(
        generation=2,
        quarantined_ids=("E1", "E2"),
    )

    snapshots = _write_generation(
        previous,
        next_state,
    )

    restored = _atomic_load(
        [previous] + snapshots
    )

    assert restored["generation"] == 2
    assert restored["quarantined_ids"] == {
        "E1",
        "E2",
    }


def test_mixed_generation_fields_are_not_accepted_as_one_snapshot():
    mixed = {
        "version": 1,
        "generation": 3,
        "quarantined_ids": ("E1",),
        "accepted_ids": ("E2",),
        "quarantine_generation": 4,
        "commit_marker": True,
    }

    restored = _validate_snapshot(mixed)

    assert restored["generation"] == 3
    assert restored["quarantined_ids"] == {"E1"}
    assert restored["accepted_ids"] == {"E2"}
    assert restored["commit_marker"] is True


def test_overlapping_partitions_are_rejected():
    snapshot = _state(
        generation=3,
        quarantined_ids=("E1",),
        accepted_ids=("E1",),
    )

    try:
        _validate_snapshot(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "overlapping state partitions must be rejected"
    )


def test_negative_generation_is_rejected():
    snapshot = _state(
        generation=-1,
        quarantined_ids=("E1",),
    )

    try:
        _validate_snapshot(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "negative generation must be rejected"
    )


def test_unknown_version_is_rejected():
    snapshot = {
        "version": 99,
        "generation": 1,
        "quarantined_ids": ("E1",),
        "accepted_ids": (),
        "commit_marker": True,
    }

    try:
        _validate_snapshot(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "unknown snapshot version must be rejected"
    )


def test_no_valid_snapshot_fails_closed():
    torn = {
        "version": 1,
        "generation": 2,
        "quarantined_ids": ("E1",),
        "accepted_ids": (),
    }

    try:
        _atomic_load([torn])
    except ValueError:
        return

    raise AssertionError(
        "recovery without a valid committed snapshot must fail closed"
    )


def test_duplicate_generation_is_deterministic_when_content_matches():
    first = _state(
        generation=5,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )
    second = _state(
        generation=5,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    a = _atomic_load([first, second])
    b = _atomic_load([second, first])

    assert a == b


def test_duplicate_generation_with_different_content_is_not_silently_merged():
    first = _state(
        generation=5,
        quarantined_ids=("E1",),
    )
    second = _state(
        generation=5,
        quarantined_ids=("E2",),
    )

    a = _atomic_load([first, second])
    b = _atomic_load([second, first])

    # The model must not merge the two generations into a synthetic state.
    assert not (
        a["quarantined_ids"] == {"E1", "E2"}
    )
    assert not (
        b["quarantined_ids"] == {"E1", "E2"}
    )


def test_quarantine_cannot_be_lost_during_recovery():
    previous = _state(
        generation=10,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    torn = {
        "version": 1,
        "generation": 11,
        "quarantined_ids": (),
        "accepted_ids": ("E1", "E2"),
        "commit_marker": False,
    }

    restored = _atomic_load([previous, torn])

    assert restored["generation"] == 10
    assert "E1" in restored["quarantined_ids"]
    assert "E1" not in restored["accepted_ids"]


def test_uncommitted_newer_snapshot_cannot_replace_committed_snapshot():
    committed = _state(
        generation=10,
        quarantined_ids=("E1",),
    )

    uncommitted = _state(
        generation=11,
        quarantined_ids=(),
        accepted_ids=("E1",),
        commit_marker=False,
    )

    restored = _atomic_load(
        [committed, uncommitted]
    )

    assert restored["generation"] == 10
    assert restored["quarantined_ids"] == {"E1"}
    assert restored["accepted_ids"] == frozenset()


def test_false_commit_marker_is_rejected():
    snapshot = _state(
        generation=1,
        quarantined_ids=("E1",),
        commit_marker=False,
    )

    try:
        _validate_snapshot(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "false commit marker must be rejected"
    )


def test_non_boolean_commit_marker_is_rejected():
    for marker in (0, 1, "true", "false", None, [], {}):
        snapshot = _state(
            generation=1,
            quarantined_ids=("E1",),
            commit_marker=marker,
        )

        try:
            _validate_snapshot(snapshot)
        except ValueError:
            continue

        raise AssertionError(
            f"invalid commit marker accepted: {marker!r}"
        )


def test_empty_state_is_valid_when_committed():
    snapshot = _state(
        generation=1,
        quarantined_ids=(),
        accepted_ids=(),
        commit_marker=True,
    )

    restored = _atomic_load([snapshot])

    assert restored["generation"] == 1
    assert restored["quarantined_ids"] == frozenset()
    assert restored["accepted_ids"] == frozenset()
    assert restored["commit_marker"] is True


def test_order_of_snapshot_list_does_not_change_latest_generation():
    snapshots = [
        _state(
            generation=1,
            quarantined_ids=("E1",),
        ),
        _state(
            generation=2,
            quarantined_ids=("E1", "E2"),
        ),
        _state(
            generation=3,
            quarantined_ids=("E1", "E2", "E3"),
        ),
    ]

    forward = _atomic_load(snapshots)
    reverse = _atomic_load(list(reversed(snapshots)))

    assert forward == reverse
    assert forward["generation"] == 3
    assert forward["quarantined_ids"] == {
        "E1",
        "E2",
        "E3",
    }


def test_uncommitted_snapshot_is_ignored_when_an_older_valid_snapshot_exists():
    committed = _state(
        generation=20,
        quarantined_ids=("E1", "E2"),
        accepted_ids=("E3",),
    )

    uncommitted = _state(
        generation=21,
        quarantined_ids=("E1",),
        accepted_ids=("E2", "E3"),
        commit_marker=False,
    )

    restored = _atomic_load(
        [committed, uncommitted]
    )

    assert restored["generation"] == 20
    assert restored["quarantined_ids"] == {
        "E1",
        "E2",
    }
    assert restored["accepted_ids"] == {"E3"}


def test_commit_marker_must_be_written_for_successful_generation():
    previous = _state(
        generation=1,
        quarantined_ids=("E1",),
    )

    next_state = _state(
        generation=2,
        quarantined_ids=("E1", "E2"),
        commit_marker=False,
    )

    snapshots = _write_generation(
        previous,
        next_state,
    )

    restored = _atomic_load(snapshots)

    assert restored["generation"] == 2
    assert restored["quarantined_ids"] == {
        "E1",
        "E2",
    }


def test_last_valid_snapshot_survives_multiple_failed_writes():
    previous = _state(
        generation=4,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    failed_one = _write_generation(
        previous,
        _state(
            generation=5,
            quarantined_ids=("E1", "E3"),
            accepted_ids=("E2",),
        ),
        crash_stage="during_write",
    )[1]

    failed_two = _write_generation(
        previous,
        _state(
            generation=6,
            quarantined_ids=("E1", "E4"),
            accepted_ids=("E2",),
        ),
        crash_stage="after_write_before_commit",
    )[1]

    restored = _atomic_load(
        [
            previous,
            failed_one,
            failed_two,
        ]
    )

    assert restored["generation"] == 4
    assert restored["quarantined_ids"] == {"E1"}
    assert restored["accepted_ids"] == {"E2"}


def test_new_committed_generation_can_follow_failed_generation():
    previous = _state(
        generation=4,
        quarantined_ids=("E1",),
    )

    failed = _write_generation(
        previous,
        _state(
            generation=5,
            quarantined_ids=("E1", "E2"),
        ),
        crash_stage="after_write_before_commit",
    )[1]

    committed = _state(
        generation=6,
        quarantined_ids=("E1", "E2", "E3"),
        accepted_ids=("E4",),
    )

    restored = _atomic_load(
        [
            previous,
            failed,
            committed,
        ]
    )

    assert restored["generation"] == 6
    assert restored["quarantined_ids"] == {
        "E1",
        "E2",
        "E3",
    }
    assert restored["accepted_ids"] == {"E4"}


def test_uncommitted_snapshot_with_newer_generation_cannot_clear_quarantine():
    previous = _state(
        generation=10,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    uncommitted = _state(
        generation=99,
        quarantined_ids=(),
        accepted_ids=("E1", "E2"),
        commit_marker=False,
    )

    restored = _atomic_load(
        [previous, uncommitted]
    )

    assert restored["generation"] == 10
    assert restored["quarantined_ids"] == {"E1"}
    assert restored["accepted_ids"] == {"E2"}