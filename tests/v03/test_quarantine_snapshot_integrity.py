"""
Quarantine snapshot content integrity.

Candidate test-layer contract:

- A committed snapshot is bound to its exact content.
- Any post-commit mutation of protected content invalidates the snapshot.
- Changing quarantine IDs, accepted IDs, generation, or version invalidates
  the content binding.
- Reordering semantically unordered collections does not invalidate integrity
  when canonicalization is used.
- Invalid/tampered newer snapshots must not replace an older valid snapshot.
- Tampering must not turn quarantined evidence into accepted evidence.
- Duplicate valid snapshots remain deterministic.
- A valid newly committed generation can replace an older valid generation.

This is intentionally test-layer work. No production behavior is changed.
"""

import hashlib
import json


def _canonical_content(
    *,
    version,
    generation,
    quarantined_ids,
    accepted_ids,
):
    return json.dumps(
        {
            "version": version,
            "generation": generation,
            "quarantined_ids": sorted(quarantined_ids),
            "accepted_ids": sorted(accepted_ids),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(
    *,
    version,
    generation,
    quarantined_ids,
    accepted_ids,
):
    return hashlib.sha256(
        _canonical_content(
            version=version,
            generation=generation,
            quarantined_ids=quarantined_ids,
            accepted_ids=accepted_ids,
        )
    ).hexdigest()


def _snapshot(
    *,
    generation,
    quarantined_ids=(),
    accepted_ids=(),
    version=1,
    commit_marker=True,
):
    content_hash = _digest(
        version=version,
        generation=generation,
        quarantined_ids=quarantined_ids,
        accepted_ids=accepted_ids,
    )

    return {
        "version": version,
        "generation": generation,
        "quarantined_ids": tuple(sorted(quarantined_ids)),
        "accepted_ids": tuple(sorted(accepted_ids)),
        "commit_marker": commit_marker,
        "content_hash": content_hash,
    }


def _validate_snapshot(snapshot):
    if not isinstance(snapshot, dict):
        raise ValueError("invalid snapshot")

    if snapshot.get("version") != 1:
        raise ValueError("unsupported snapshot version")

    if snapshot.get("commit_marker") is not True:
        raise ValueError("snapshot is not committed")

    generation = snapshot.get("generation")
    quarantined = snapshot.get("quarantined_ids")
    accepted = snapshot.get("accepted_ids")
    stored_hash = snapshot.get("content_hash")

    if not isinstance(generation, int):
        raise ValueError("invalid generation")

    if generation < 0:
        raise ValueError("invalid generation")

    if not isinstance(quarantined, (tuple, list)):
        raise ValueError("invalid quarantine set")

    if not isinstance(accepted, (tuple, list)):
        raise ValueError("invalid accepted set")

    if not isinstance(stored_hash, str):
        raise ValueError("missing content hash")

    quarantined = frozenset(quarantined)
    accepted = frozenset(accepted)

    if quarantined & accepted:
        raise ValueError("overlapping state partitions")

    expected_hash = _digest(
        version=1,
        generation=generation,
        quarantined_ids=quarantined,
        accepted_ids=accepted,
    )

    if stored_hash != expected_hash:
        raise ValueError("content integrity failure")

    return {
        "version": 1,
        "generation": generation,
        "quarantined_ids": quarantined,
        "accepted_ids": accepted,
        "commit_marker": True,
        "content_hash": expected_hash,
    }


def _load_latest(snapshots):
    valid = []

    for snapshot in snapshots:
        try:
            valid.append(
                _validate_snapshot(snapshot)
            )
        except ValueError:
            continue

    if not valid:
        raise ValueError(
            "no valid integrity-checked snapshot"
        )

    return max(
        valid,
        key=lambda snapshot: snapshot["generation"],
    )


def test_valid_snapshot_passes_integrity_check():
    snapshot = _snapshot(
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    restored = _validate_snapshot(snapshot)

    assert restored["generation"] == 1
    assert restored["quarantined_ids"] == {"E1"}
    assert restored["accepted_ids"] == {"E2"}


def test_content_hash_is_deterministic():
    first = _digest(
        version=1,
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    second = _digest(
        version=1,
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    assert first == second


def test_content_hash_changes_when_quarantine_changes():
    first = _digest(
        version=1,
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    second = _digest(
        version=1,
        generation=1,
        quarantined_ids=("E1", "E3"),
        accepted_ids=("E2",),
    )

    assert first != second


def test_content_hash_changes_when_acceptance_changes():
    first = _digest(
        version=1,
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    second = _digest(
        version=1,
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2", "E3"),
    )

    assert first != second


def test_content_hash_changes_when_generation_changes():
    first = _digest(
        version=1,
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    second = _digest(
        version=1,
        generation=2,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    assert first != second


def test_tampered_quarantine_set_is_rejected():
    snapshot = _snapshot(
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    snapshot["quarantined_ids"] = ("E2",)

    try:
        _validate_snapshot(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "tampered quarantine content must be rejected"
    )


def test_tampered_accepted_set_is_rejected():
    snapshot = _snapshot(
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    snapshot["accepted_ids"] = ("E1", "E2")

    try:
        _validate_snapshot(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "tampered accepted content must be rejected"
    )


def test_tampered_generation_is_rejected():
    snapshot = _snapshot(
        generation=4,
        quarantined_ids=("E1",),
    )

    snapshot["generation"] = 5

    try:
        _validate_snapshot(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "tampered generation must be rejected"
    )


def test_tampered_version_is_rejected():
    snapshot = _snapshot(
        generation=1,
        quarantined_ids=("E1",),
    )

    snapshot["version"] = 2

    try:
        _validate_snapshot(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "tampered version must be rejected"
    )


def test_tampered_hash_is_rejected():
    snapshot = _snapshot(
        generation=1,
        quarantined_ids=("E1",),
    )

    snapshot["content_hash"] = "0" * 64

    try:
        _validate_snapshot(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "tampered content hash must be rejected"
    )


def test_missing_hash_is_rejected():
    snapshot = _snapshot(
        generation=1,
        quarantined_ids=("E1",),
    )

    del snapshot["content_hash"]

    try:
        _validate_snapshot(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "missing content hash must be rejected"
    )


def test_changed_commit_marker_is_rejected():
    snapshot = _snapshot(
        generation=1,
        quarantined_ids=("E1",),
    )

    snapshot["commit_marker"] = False

    try:
        _validate_snapshot(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "uncommitted snapshot must be rejected"
    )


def test_reordering_quarantine_ids_does_not_change_integrity():
    snapshot = _snapshot(
        generation=1,
        quarantined_ids=("E1", "E2", "E3"),
        accepted_ids=("E4",),
    )

    reordered = dict(snapshot)
    reordered["quarantined_ids"] = (
        "E3",
        "E1",
        "E2",
    )

    restored = _validate_snapshot(reordered)

    assert restored["quarantined_ids"] == {
        "E1",
        "E2",
        "E3",
    }


def test_reordering_accepted_ids_does_not_change_integrity():
    snapshot = _snapshot(
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2", "E3", "E4"),
    )

    reordered = dict(snapshot)
    reordered["accepted_ids"] = (
        "E4",
        "E2",
        "E3",
    )

    restored = _validate_snapshot(reordered)

    assert restored["accepted_ids"] == {
        "E2",
        "E3",
        "E4",
    }


def test_tampered_newer_snapshot_does_not_replace_valid_older_snapshot():
    old = _snapshot(
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    new = _snapshot(
        generation=2,
        quarantined_ids=("E1", "E3"),
        accepted_ids=("E2",),
    )

    tampered = dict(new)
    tampered["quarantined_ids"] = ()
    tampered["accepted_ids"] = ("E1", "E2", "E3")

    restored = _load_latest(
        [old, tampered]
    )

    assert restored["generation"] == 1
    assert restored["quarantined_ids"] == {"E1"}
    assert restored["accepted_ids"] == {"E2"}


def test_tampered_snapshot_cannot_resurrect_quarantined_identity():
    valid = _snapshot(
        generation=10,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    tampered = dict(valid)
    tampered["accepted_ids"] = ("E1", "E2")

    try:
        _load_latest([tampered])
    except ValueError:
        return

    raise AssertionError(
        "tampered snapshot must not resurrect quarantined identity"
    )


def test_no_integrity_valid_snapshot_fails_closed():
    tampered = {
        "version": 1,
        "generation": 7,
        "quarantined_ids": (),
        "accepted_ids": ("E1",),
        "commit_marker": True,
        "content_hash": "0" * 64,
    }

    try:
        _load_latest([tampered])
    except ValueError:
        return

    raise AssertionError(
        "recovery must fail closed without valid integrity"
    )


def test_duplicate_valid_snapshots_are_equivalent():
    first = _snapshot(
        generation=3,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )
    second = _snapshot(
        generation=3,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    a = _load_latest([first, second])
    b = _load_latest([second, first])

    assert a == b


def test_same_generation_different_content_cannot_be_silently_merged():
    first = _snapshot(
        generation=3,
        quarantined_ids=("E1",),
    )
    second = _snapshot(
        generation=3,
        quarantined_ids=("E2",),
    )

    a = _load_latest([first, second])
    b = _load_latest([second, first])

    assert a["quarantined_ids"] in (
        frozenset({"E1"}),
        frozenset({"E2"}),
    )
    assert b["quarantined_ids"] in (
        frozenset({"E1"}),
        frozenset({"E2"}),
    )

    assert not (
        a["quarantined_ids"]
        == frozenset({"E1", "E2"})
    )
    assert not (
        b["quarantined_ids"]
        == frozenset({"E1", "E2"})
    )


def test_valid_newer_snapshot_replaces_valid_older_snapshot():
    old = _snapshot(
        generation=1,
        quarantined_ids=("E1",),
    )
    new = _snapshot(
        generation=2,
        quarantined_ids=("E1", "E2"),
        accepted_ids=("E3",),
    )

    restored = _load_latest([old, new])

    assert restored["generation"] == 2
    assert restored["quarantined_ids"] == {
        "E1",
        "E2",
    }
    assert restored["accepted_ids"] == {"E3"}


def test_tampered_snapshot_with_newer_generation_is_ignored():
    old = _snapshot(
        generation=5,
        quarantined_ids=("E1",),
    )

    new = _snapshot(
        generation=6,
        quarantined_ids=("E1", "E2"),
    )

    tampered = dict(new)
    tampered["accepted_ids"] = ("E1", "E2")

    restored = _load_latest(
        [old, tampered]
    )

    assert restored["generation"] == 5
    assert restored["quarantined_ids"] == {"E1"}


def test_tampering_with_hash_only_does_not_go_unnoticed():
    snapshot = _snapshot(
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    original_hash = snapshot["content_hash"]

    snapshot["content_hash"] = (
        original_hash[:-1]
        + ("0" if original_hash[-1] != "0" else "1")
    )

    try:
        _validate_snapshot(snapshot)
    except ValueError:
        return

    raise AssertionError(
        "hash tampering must be detected"
    )


def test_hash_is_bound_to_version():
    hash_v1 = _digest(
        version=1,
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    hash_v2 = _digest(
        version=2,
        generation=1,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    assert hash_v1 != hash_v2


def test_empty_snapshot_has_valid_integrity():
    snapshot = _snapshot(
        generation=0,
        quarantined_ids=(),
        accepted_ids=(),
    )

    restored = _validate_snapshot(snapshot)

    assert restored["generation"] == 0
    assert restored["quarantined_ids"] == frozenset()
    assert restored["accepted_ids"] == frozenset()


def test_integrity_preserves_partition_invariant():
    snapshot = _snapshot(
        generation=2,
        quarantined_ids=("E1", "E2"),
        accepted_ids=("E3", "E4"),
    )

    restored = _validate_snapshot(snapshot)

    assert restored["quarantined_ids"].isdisjoint(
        restored["accepted_ids"]
    )


def test_tampered_snapshot_does_not_change_valid_previous_state():
    previous = _snapshot(
        generation=12,
        quarantined_ids=("E1", "E2"),
        accepted_ids=("E3",),
    )

    next_state = _snapshot(
        generation=13,
        quarantined_ids=("E1", "E2", "E4"),
        accepted_ids=("E3",),
    )

    tampered = dict(next_state)
    tampered["quarantined_ids"] = ("E5",)

    restored = _load_latest(
        [previous, tampered]
    )

    assert restored["generation"] == 12
    assert restored["quarantined_ids"] == {
        "E1",
        "E2",
    }
    assert restored["accepted_ids"] == {"E3"}


def test_integrity_is_independent_of_snapshot_dict_key_order():
    snapshot = _snapshot(
        generation=8,
        quarantined_ids=("E1",),
        accepted_ids=("E2", "E3"),
    )

    reordered = {
        "content_hash": snapshot["content_hash"],
        "accepted_ids": snapshot["accepted_ids"],
        "commit_marker": snapshot["commit_marker"],
        "generation": snapshot["generation"],
        "version": snapshot["version"],
        "quarantined_ids": snapshot["quarantined_ids"],
    }

    original = _validate_snapshot(snapshot)
    restored = _validate_snapshot(reordered)

    assert original == restored


def test_tampered_generation_and_recomputed_hash_represents_new_content():
    snapshot = _snapshot(
        generation=8,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    tampered = dict(snapshot)
    tampered["generation"] = 9
    tampered["content_hash"] = _digest(
        version=1,
        generation=9,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    restored = _validate_snapshot(tampered)

    assert restored["generation"] == 9
    assert restored["quarantined_ids"] == {"E1"}
    assert restored["accepted_ids"] == {"E2"}


def test_recomputed_hash_does_not_prove_authority():
    """
    This deliberately documents the limit of this experiment:

    A content hash detects accidental or unauthorized content mutation,
    but it does not establish who was authorized to create the content.

    Authorization/signature semantics belong to a later boundary.
    """
    snapshot = _snapshot(
        generation=4,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    tampered = dict(snapshot)
    tampered["generation"] = 99
    tampered["content_hash"] = _digest(
        version=1,
        generation=99,
        quarantined_ids=("E1",),
        accepted_ids=("E2",),
    )

    restored = _validate_snapshot(tampered)

    assert restored["generation"] == 99
    assert restored["quarantined_ids"] == {"E1"}

    # Integrity is valid for the new content, but this experiment does not
    # claim that the new content is authorized.