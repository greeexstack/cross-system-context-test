"""
Quarantine release authorization scope.

Candidate test-layer contract:

A release authorization is scoped to:
- one evidence identity;
- one work-item/context scope;
- one authority scope;
- one exact conflict fingerprint.

A valid release in one scope must not authorize another scope.

This is intentionally test-layer work. Production behavior is unchanged.
"""


def _item(
    evidence_id,
    *,
    work_item,
    confirms_completion=False,
    requests_next_step=False,
    requests_followup=False,
):
    class Item:
        pass

    item = Item()
    item.evidence_id = evidence_id
    item.work_item = work_item
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
    work_item,
    fingerprint,
    *,
    authority_scope="control-plane",
    resolution_id="R-1",
):
    return {
        "identity": identity,
        "work_item": work_item,
        "fingerprint": fingerprint,
        "authority_scope": authority_scope,
        "resolution_id": resolution_id,
    }


def _evaluate(
    items,
    resolutions=(),
    *,
    required_authority_scope="control-plane",
):
    items = tuple(items)

    by_id = {}
    work_items = {}

    for item in items:
        by_id.setdefault(item.evidence_id, []).append(item)
        work_items[item.evidence_id] = item.work_item

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
        work_item = resolution.get("work_item")
        fingerprint = resolution.get("fingerprint")
        authority_scope = resolution.get("authority_scope")
        resolution_id = resolution.get("resolution_id")

        valid = (
            identity in quarantined
            and work_item == work_items.get(identity)
            and fingerprint == fingerprints.get(identity)
            and authority_scope == required_authority_scope
            and isinstance(resolution_id, str)
            and bool(resolution_id)
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
    result.released_ids = frozenset(released)
    return result


def test_matching_identity_and_work_item_can_be_released():
    a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            _resolution(
                "E1",
                "W1",
                fingerprint,
            )
        ],
    )

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}


def test_release_for_wrong_work_item_cannot_clear_quarantine():
    a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            _resolution(
                "E1",
                "W2",
                fingerprint,
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_release_for_wrong_identity_cannot_clear_quarantine():
    a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            _resolution(
                "E2",
                "W1",
                fingerprint,
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_release_from_wrong_authority_scope_cannot_clear_quarantine():
    a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            _resolution(
                "E1",
                "W1",
                fingerprint,
                authority_scope="untrusted-source",
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == set()


def test_authority_scope_is_not_inferred_from_identity():
    a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            {
                "identity": "E1",
                "work_item": "W1",
                "fingerprint": fingerprint,
                "resolution_id": "R-1",
            }
        ],
    )

    assert result.quarantined_ids == {"E1"}


def test_one_valid_release_does_not_release_second_identity():
    e1a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    e1b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    e2a = _item(
        "E2",
        work_item="W2",
        confirms_completion=True,
    )
    e2b = _item(
        "E2",
        work_item="W2",
        requests_followup=True,
    )

    e1_fingerprint = _fingerprint(
        [e1a, e1b, e2a, e2b],
        "E1",
    )

    result = _evaluate(
        [e1a, e1b, e2a, e2b],
        [
            _resolution(
                "E1",
                "W1",
                e1_fingerprint,
            )
        ],
    )

    assert result.quarantined_ids == {"E2"}
    assert result.accepted_ids == {"E1"}


def test_same_identity_in_different_work_item_is_not_cross_released():
    a1 = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    b1 = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    a2 = _item(
        "E2",
        work_item="W2",
        confirms_completion=True,
    )
    b2 = _item(
        "E2",
        work_item="W2",
        requests_next_step=True,
    )

    fingerprint_w1 = _fingerprint(
        [a1, b1, a2, b2],
        "E1",
    )

    result = _evaluate(
        [a1, b1, a2, b2],
        [
            _resolution(
                "E1",
                "W2",
                fingerprint_w1,
            )
        ],
    )

    assert result.quarantined_ids == {"E1", "E2"}
    assert result.accepted_ids == set()


def test_fingerprint_cannot_be_transferred_to_another_identity():
    e1a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    e1b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    e2a = _item(
        "E2",
        work_item="W2",
        confirms_completion=True,
    )
    e2b = _item(
        "E2",
        work_item="W2",
        requests_followup=True,
    )

    fingerprint_e1 = _fingerprint(
        [e1a, e1b, e2a, e2b],
        "E1",
    )

    result = _evaluate(
        [e1a, e1b, e2a, e2b],
        [
            _resolution(
                "E2",
                "W2",
                fingerprint_e1,
            )
        ],
    )

    assert result.quarantined_ids == {"E1", "E2"}


def test_work_item_change_after_resolution_invalidates_release():
    a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    fingerprint = _fingerprint([a, b], "E1")

    release = _resolution(
        "E1",
        "W1",
        fingerprint,
        resolution_id="REL-1",
    )

    changed_a = _item(
        "E1",
        work_item="W9",
        confirms_completion=True,
    )
    changed_b = _item(
        "E1",
        work_item="W9",
        requests_next_step=True,
    )

    result = _evaluate(
        [changed_a, changed_b],
        [release],
    )

    assert result.quarantined_ids == {"E1"}


def test_authority_scope_change_after_release_invalidates_replay():
    a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    fingerprint = _fingerprint([a, b], "E1")

    original = _resolution(
        "E1",
        "W1",
        fingerprint,
        authority_scope="control-plane",
        resolution_id="REL-1",
    )

    result = _evaluate(
        [a, b],
        [original],
        required_authority_scope="different-plane",
    )

    assert result.quarantined_ids == {"E1"}


def test_multiple_authority_scopes_require_explicit_scope_match():
    a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            _resolution(
                "E1",
                "W1",
                fingerprint,
                authority_scope="control-plane",
            ),
        ],
        required_authority_scope="control-plane",
    )

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}


def test_two_quarantines_in_different_work_items_remain_independent():
    items = [
        _item(
            "E1",
            work_item="W1",
            confirms_completion=True,
        ),
        _item(
            "E1",
            work_item="W1",
            requests_next_step=True,
        ),
        _item(
            "E2",
            work_item="W2",
            confirms_completion=True,
        ),
        _item(
            "E2",
            work_item="W2",
            requests_followup=True,
        ),
    ]

    e1_fingerprint = _fingerprint(items, "E1")

    result = _evaluate(
        items,
        [
            _resolution(
                "E1",
                "W1",
                e1_fingerprint,
                resolution_id="E1-REL",
            )
        ],
    )

    assert result.quarantined_ids == {"E2"}
    assert result.accepted_ids == {"E1"}


def test_release_scope_is_deterministic_under_input_reordering():
    a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )
    c = _item(
        "E2",
        work_item="W2",
        confirms_completion=True,
    )
    d = _item(
        "E2",
        work_item="W2",
        requests_followup=True,
    )

    items = [a, b, c, d]

    e1_fingerprint = _fingerprint(items, "E1")

    resolution = _resolution(
        "E1",
        "W1",
        e1_fingerprint,
        resolution_id="REL-DET",
    )

    forward = _evaluate(items, [resolution])
    reverse = _evaluate(
        list(reversed(items)),
        [resolution],
    )

    assert forward.quarantined_ids == reverse.quarantined_ids
    assert forward.accepted_ids == reverse.accepted_ids
    assert forward.released_ids == reverse.released_ids


def test_empty_scope_cannot_match_real_work_item():
    a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            _resolution(
                "E1",
                "",
                fingerprint,
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}


def test_unknown_authority_scope_cannot_release():
    a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )

    fingerprint = _fingerprint([a, b], "E1")

    result = _evaluate(
        [a, b],
        [
            _resolution(
                "E1",
                "W1",
                fingerprint,
                authority_scope="unknown",
            )
        ],
    )

    assert result.quarantined_ids == {"E1"}


def test_valid_release_does_not_cross_into_clean_identity():
    e1a = _item(
        "E1",
        work_item="W1",
        confirms_completion=True,
    )
    e1b = _item(
        "E1",
        work_item="W1",
        requests_next_step=True,
    )
    clean = _item(
        "E2",
        work_item="W2",
        confirms_completion=True,
    )

    fingerprint = _fingerprint(
        [e1a, e1b, clean],
        "E1",
    )

    result = _evaluate(
        [e1a, e1b, clean],
        [
            _resolution(
                "E1",
                "W1",
                fingerprint,
            )
        ],
    )

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1", "E2"}