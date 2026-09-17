"""
Quarantine release semantics.

Candidate test-layer policy:

- Quarantine is sticky by default.
- Loss of observability does not clear quarantine.
- Additional benign evidence does not clear quarantine.
- A quarantine can be cleared only by an explicit authoritative resolution.
- A resolution must match the conflict state it is intended to resolve.
- Stale, malformed, unrelated, or non-authoritative resolutions do not clear it.

No production behavior is changed by this experiment.
"""


def _item(
    evidence_id,
    *,
    confirms_completion=False,
    requests_next_step=False,
    requests_followup=False,
    source_system="system-a",
    source_id="A-1",
):
    class Item:
        pass

    item = Item()
    item.evidence_id = evidence_id
    item.confirms_completion = confirms_completion
    item.requests_next_step = requests_next_step
    item.requests_followup = requests_followup
    item.source_system = source_system
    item.source_id = source_id
    return item


def _payload(item):
    return (
        item.confirms_completion,
        item.requests_next_step,
        item.requests_followup,
    )


def _conflict_fingerprint(items, identity):
    payloads = sorted(
        {
            _payload(item)
            for item in items
            if item.evidence_id == identity
        }
    )
    return tuple(payloads)


def _evaluate(items, resolutions=()):
    items = tuple(items)

    by_id = {}
    for item in items:
        by_id.setdefault(item.evidence_id, []).append(item)

    direct_quarantine = {
        identity
        for identity, members in by_id.items()
        if len({_payload(member) for member in members}) > 1
    }

    current_fingerprints = {
        identity: _conflict_fingerprint(items, identity)
        for identity in direct_quarantine
    }

    valid_resolutions = {
        resolution["identity"]
        for resolution in resolutions
        if resolution.get("authoritative") is True
        and resolution.get("resolution_id")
        and resolution.get("identity") in direct_quarantine
        and resolution.get("fingerprint")
        == current_fingerprints.get(resolution["identity"])
    }

    quarantined = direct_quarantine - valid_resolutions
    accepted = set(by_id) - quarantined

    class Result:
        pass

    result = Result()
    result.quarantined_ids = frozenset(quarantined)
    result.accepted_ids = accepted
    result.current_fingerprints = current_fingerprints
    return result


def _resolution(identity, fingerprint, *, resolution_id="R-1", authoritative=True):
    return {
        "identity": identity,
        "fingerprint": fingerprint,
        "resolution_id": resolution_id,
        "authoritative": authoritative,
    }


def test_quarantine_is_sticky_without_explicit_resolution():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    result = _evaluate([a, b])

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_empty_resolution_set_does_not_clear_quarantine():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    result = _evaluate([a, b], resolutions=[])

    assert result.quarantined_ids == {"E1"}
    assert "E1" not in result.accepted_ids


def test_non_authoritative_resolution_does_not_clear_quarantine():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _conflict_fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        resolutions=[
            _resolution(
                "E1",
                fingerprint,
                authoritative=False,
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_unrelated_resolution_does_not_clear_quarantine():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _conflict_fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        resolutions=[
            _resolution("E2", fingerprint)
        ],
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_explicit_matching_resolution_clears_quarantine():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _conflict_fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        resolutions=[
            _resolution("E1", fingerprint)
        ],
    )

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}


def test_wrong_fingerprint_does_not_clear_quarantine():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    result = _evaluate(
        [a, b],
        resolutions=[
            _resolution(
                "E1",
                (
                    (False, False, True),
                    (True, False, False),
                ),
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_stale_resolution_does_not_clear_new_conflict():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    old_fingerprint = _conflict_fingerprint([a, b], "E1")

    c = _item("E1", requests_followup=True)

    result = _evaluate(
        [a, b, c],
        resolutions=[
            _resolution("E1", old_fingerprint)
        ],
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_additional_benign_identity_does_not_clear_existing_quarantine():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)
    clean = _item("E2", requests_followup=True)

    result = _evaluate([a, b, clean])

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == {"E2"}


def test_source_metadata_change_does_not_clear_quarantine():
    a = _item(
        "E1",
        confirms_completion=True,
        source_system="crm",
        source_id="CRM-1",
    )
    b = _item(
        "E1",
        requests_next_step=True,
        source_system="billing",
        source_id="BILL-1",
    )

    result = _evaluate([a, b])

    assert result.quarantined_ids == {"E1"}

    metadata_variant = _item(
        "E1",
        confirms_completion=True,
        source_system="archive",
        source_id="ARCH-9",
    )
    same_conflict = _item(
        "E1",
        requests_next_step=True,
        source_system="replay",
        source_id="REPLAY-9",
    )

    result_after_change = _evaluate(
        [metadata_variant, same_conflict]
    )

    assert result_after_change.quarantined_ids == {"E1"}
    assert "E1" not in result_after_change.accepted_ids


def test_duplicate_matching_resolution_is_idempotent():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _conflict_fingerprint([a, b], "E1")

    resolution = _resolution("E1", fingerprint)

    first = _evaluate([a, b], [resolution])
    second = _evaluate([a, b], [resolution, resolution])

    assert first.quarantined_ids == frozenset()
    assert second.quarantined_ids == frozenset()
    assert first.accepted_ids == second.accepted_ids == {"E1"}


def test_missing_resolution_id_does_not_clear_quarantine():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _conflict_fingerprint([a, b], "E1")

    resolution = _resolution("E1", fingerprint)
    del resolution["resolution_id"]

    result = _evaluate([a, b], [resolution])

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_clean_identity_does_not_require_a_release_resolution():
    clean = _item("E1", confirms_completion=True)

    result = _evaluate([clean])

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}
    assert result.current_fingerprints == {}


def test_release_of_parent_does_not_automatically_change_unrelated_identity():
    parent_a = _item("E1", confirms_completion=True)
    parent_b = _item("E1", requests_next_step=True)

    unrelated_a = _item("E2", confirms_completion=True)
    unrelated_b = _item("E2", requests_followup=True)

    parent_fingerprint = _conflict_fingerprint(
        [parent_a, parent_b],
        "E1",
    )

    result = _evaluate(
        [
            parent_a,
            parent_b,
            unrelated_a,
            unrelated_b,
        ],
        resolutions=[
            _resolution("E1", parent_fingerprint)
        ],
    )

    assert result.quarantined_ids == {"E2"}
    assert result.accepted_ids == {"E1"}


def test_resolution_does_not_hide_a_still_present_conflict():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _conflict_fingerprint([a, b], "E1")

    resolution = _resolution("E1", fingerprint)

    changed = _item("E1", requests_followup=True)

    result = _evaluate(
        [a, b, changed],
        resolutions=[resolution],
    )

    assert result.quarantined_ids == {"E1"}
    assert "E1" not in result.accepted_ids


def test_quarantine_release_partition_is_deterministic():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)
    c = _item("E2", confirms_completion=True)

    fingerprint = _conflict_fingerprint([a, b], "E1")
    resolution = _resolution("E1", fingerprint)

    forward = _evaluate([a, b, c], [resolution])
    reverse = _evaluate([c, b, a], [resolution])

    assert forward.quarantined_ids == reverse.quarantined_ids
    assert forward.accepted_ids == reverse.accepted_ids
    assert forward.accepted_ids == {"E1", "E2"}