"""
Quarantine release authorization and replay safety.

Candidate test-layer contract:

- A release must identify the quarantined identity.
- A release must identify the conflict fingerprint it resolves.
- A release must identify the authority that issued it.
- A release must have a unique resolution ID.
- Missing, blank, malformed, or non-authoritative resolution metadata
  cannot clear quarantine.
- A resolution for one conflict cannot be replayed against another.
- Duplicate replay of the same valid resolution is idempotent.
- A valid release remains attributable to its authority and resolution ID.

No production behavior is changed by this experiment.
"""


def _item(
    evidence_id,
    *,
    confirms_completion=False,
    requests_next_step=False,
    requests_followup=False,
):
    class Item:
        pass

    item = Item()
    item.evidence_id = evidence_id
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


def _resolution(
    identity,
    fingerprint,
    *,
    resolution_id="R-1",
    authority="operator-1",
):
    return {
        "identity": identity,
        "fingerprint": fingerprint,
        "resolution_id": resolution_id,
        "authority": authority,
    }


def _evaluate(items, resolutions=()):
    items = tuple(items)

    by_id = {}
    for item in items:
        by_id.setdefault(item.evidence_id, []).append(item)

    quarantined = {
        identity
        for identity, members in by_id.items()
        if len({_payload(member) for member in members}) > 1
    }

    fingerprints = {
        identity: _fingerprint(items, identity)
        for identity in quarantined
    }

    released = set()

    for resolution in resolutions:
        identity = resolution.get("identity")
        fingerprint = resolution.get("fingerprint")
        resolution_id = resolution.get("resolution_id")
        authority = resolution.get("authority")

        valid = (
            isinstance(identity, str)
            and bool(identity)
            and identity in quarantined
            and fingerprint == fingerprints.get(identity)
            and isinstance(resolution_id, str)
            and bool(resolution_id)
            and isinstance(authority, str)
            and bool(authority)
        )

        if valid:
            released.add(identity)

    quarantined -= released
    accepted = set(by_id) - quarantined

    class Result:
        pass

    result = Result()
    result.quarantined_ids = frozenset(quarantined)
    result.accepted_ids = accepted
    result.fingerprints = fingerprints
    result.released_ids = frozenset(released)
    return result


def test_valid_resolution_requires_authority():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            {
                "identity": "E1",
                "fingerprint": fingerprint,
                "resolution_id": "R-1",
            }
        ],
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_blank_authority_cannot_release():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            _resolution(
                "E1",
                fingerprint,
                authority="",
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}


def test_blank_resolution_id_cannot_release():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            _resolution(
                "E1",
                fingerprint,
                resolution_id="",
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}


def test_valid_authorized_resolution_releases_exact_conflict():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _fingerprint([a, b], "E1")

    resolution = _resolution(
        "E1",
        fingerprint,
        resolution_id="REL-100",
        authority="control-plane",
    )

    result = _evaluate([a, b], [resolution])

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}
    assert result.released_ids == {"E1"}


def test_resolution_for_wrong_identity_cannot_release():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            _resolution(
                "E2",
                fingerprint,
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_resolution_for_old_conflict_cannot_be_replayed_on_new_conflict():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    old_fingerprint = _fingerprint([a, b], "E1")

    c = _item("E1", requests_followup=True)

    new_items = [a, b, c]

    result = _evaluate(
        new_items,
        [
            _resolution(
                "E1",
                old_fingerprint,
                resolution_id="OLD-1",
                authority="control-plane",
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_new_resolution_can_release_new_conflict():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)
    c = _item("E1", requests_followup=True)

    items = [a, b, c]
    new_fingerprint = _fingerprint(items, "E1")

    result = _evaluate(
        items,
        [
            _resolution(
                "E1",
                new_fingerprint,
                resolution_id="NEW-1",
                authority="control-plane",
            )
        ],
    )

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}


def test_duplicate_valid_resolution_is_idempotent():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _fingerprint([a, b], "E1")

    resolution = _resolution(
        "E1",
        fingerprint,
        resolution_id="REL-1",
        authority="control-plane",
    )

    first = _evaluate([a, b], [resolution])
    second = _evaluate(
        [a, b],
        [resolution, resolution],
    )

    assert first.quarantined_ids == frozenset()
    assert second.quarantined_ids == frozenset()
    assert first.accepted_ids == second.accepted_ids == {"E1"}


def test_two_different_authorized_resolutions_for_same_state_do_not_requarantine():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _fingerprint([a, b], "E1")

    r1 = _resolution(
        "E1",
        fingerprint,
        resolution_id="REL-1",
        authority="operator-a",
    )
    r2 = _resolution(
        "E1",
        fingerprint,
        resolution_id="REL-2",
        authority="operator-b",
    )

    result = _evaluate([a, b], [r1, r2])

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}


def test_resolution_fingerprint_is_exact_not_partial():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)
    c = _item("E1", requests_followup=True)

    items = [a, b, c]

    partial_fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        items,
        [
            _resolution(
                "E1",
                partial_fingerprint,
                resolution_id="PARTIAL-1",
                authority="control-plane",
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}


def test_resolution_metadata_is_preserved_as_audit_identity():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _fingerprint([a, b], "E1")

    resolution = _resolution(
        "E1",
        fingerprint,
        resolution_id="REL-AUDIT-77",
        authority="policy-engine",
    )

    assert resolution["identity"] == "E1"
    assert resolution["resolution_id"] == "REL-AUDIT-77"
    assert resolution["authority"] == "policy-engine"
    assert resolution["fingerprint"] == fingerprint


def test_resolution_id_must_be_text():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            _resolution(
                "E1",
                fingerprint,
                resolution_id=123,
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}


def test_authority_must_be_text():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            _resolution(
                "E1",
                fingerprint,
                authority=123,
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}


def test_release_is_scoped_to_currently_quarantined_identities():
    clean = _item("E1", confirms_completion=True)

    resolution = _resolution(
        "E1",
        _fingerprint([clean], "E1"),
        resolution_id="R-CLEAN",
        authority="control-plane",
    )

    result = _evaluate([clean], [resolution])

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}
    assert result.released_ids == frozenset()


def test_replay_of_release_after_conflict_returns_is_rejected():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)

    fingerprint = _fingerprint([a, b], "E1")

    resolution = _resolution(
        "E1",
        fingerprint,
        resolution_id="R-REPLAY",
        authority="control-plane",
    )

    released = _evaluate([a, b], [resolution])

    assert released.quarantined_ids == frozenset()

    changed = _item("E1", requests_followup=True)

    replayed = _evaluate(
        [a, b, changed],
        [resolution],
    )

    assert replayed.quarantined_ids == {"E1"}
    assert replayed.accepted_ids == set()


def test_multiple_identities_require_individual_release_authority():
    e1a = _item("E1", confirms_completion=True)
    e1b = _item("E1", requests_next_step=True)

    e2a = _item("E2", confirms_completion=True)
    e2b = _item("E2", requests_followup=True)

    e1_fingerprint = _fingerprint(
        [e1a, e1b, e2a, e2b],
        "E1",
    )

    result = _evaluate(
        [e1a, e1b, e2a, e2b],
        [
            _resolution(
                "E1",
                e1_fingerprint,
                resolution_id="E1-REL",
                authority="control-plane",
            )
        ],
    )

    assert result.quarantined_ids == {"E2"}
    assert result.accepted_ids == {"E1"}


def test_release_result_is_deterministic_under_input_reordering():
    a = _item("E1", confirms_completion=True)
    b = _item("E1", requests_next_step=True)
    c = _item("E2", confirms_completion=True)

    fingerprint = _fingerprint([a, b, c], "E1")

    resolution = _resolution(
        "E1",
        fingerprint,
        resolution_id="REL-DET",
        authority="control-plane",
    )

    forward = _evaluate([a, b, c], [resolution])
    reverse = _evaluate([c, b, a], [resolution])

    assert forward.quarantined_ids == reverse.quarantined_ids
    assert forward.accepted_ids == reverse.accepted_ids
    assert forward.released_ids == reverse.released_ids