"""
Quarantine release lineage containment.

Candidate test-layer contract:

- Quarantine propagates from a conflicted parent into descendants.
- Releasing the parent does NOT automatically release descendants.
- A descendant remains quarantined until its own current lineage state is
  explicitly and validly resolved.
- Multi-parent descendants remain quarantined if any unresolved parent remains.
- Independent branches are unaffected.
- Releases are evaluated against the current conflict fingerprint.
- Reordering and repeated evaluation are deterministic.

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


def _evaluate(items, resolutions=()):
    items = tuple(items)

    by_id = {}
    parents_by_id = {}

    for item in items:
        by_id.setdefault(item.evidence_id, []).append(item)
        parents_by_id.setdefault(item.evidence_id, set()).update(
            item.parent_ids
        )

    direct_quarantine = {
        identity
        for identity, members in by_id.items()
        if len({_payload(member) for member in members}) > 1
    }

    inherited_quarantine = set(direct_quarantine)

    changed = True
    while changed:
        changed = False

        for identity, parent_ids in parents_by_id.items():
            if identity in inherited_quarantine:
                continue

            if parent_ids & inherited_quarantine:
                inherited_quarantine.add(identity)
                changed = True

    current_fingerprints = {
        identity: _fingerprint(items, identity)
        for identity in direct_quarantine
    }

    explicitly_released = set()

    for resolution in resolutions:
        identity = resolution.get("identity")
        fingerprint = resolution.get("fingerprint")
        resolution_id = resolution.get("resolution_id")

        valid = (
            identity in direct_quarantine
            and identity == resolution.get("target_identity")
            and fingerprint == current_fingerprints.get(identity)
            and isinstance(resolution_id, str)
            and bool(resolution_id)
        )

        if valid:
            explicitly_released.add(identity)

    # A directly conflicting identity can be released explicitly.
    # Descendants do not inherit that release automatically.
    quarantined = inherited_quarantine - explicitly_released

    accepted = set(by_id) - quarantined

    class Result:
        pass

    result = Result()
    result.quarantined_ids = frozenset(quarantined)
    result.accepted_ids = accepted
    result.released_ids = frozenset(explicitly_released)
    return result


def _resolution(identity, fingerprint, *, resolution_id="R-1"):
    return {
        "identity": identity,
        "target_identity": identity,
        "fingerprint": fingerprint,
        "resolution_id": resolution_id,
    }


def test_parent_release_does_not_release_child():
    parent_a = _item(
        "E1",
        confirms_completion=True,
    )
    parent_b = _item(
        "E1",
        requests_next_step=True,
    )
    child = _item(
        "E2",
        parent_ids=("E1",),
        requests_followup=True,
    )

    items = [parent_a, parent_b, child]
    parent_fingerprint = _fingerprint(items, "E1")

    result = _evaluate(
        items,
        [
            _resolution(
                "E1",
                parent_fingerprint,
            )
        ],
    )

    assert result.released_ids == {"E1"}
    assert result.quarantined_ids == {"E2"}
    assert result.accepted_ids == {"E1"}


def test_grandchild_remains_quarantined_when_only_root_is_released():
    root_a = _item(
        "E1",
        confirms_completion=True,
    )
    root_b = _item(
        "E1",
        requests_next_step=True,
    )
    child = _item(
        "E2",
        parent_ids=("E1",),
    )
    grandchild = _item(
        "E3",
        parent_ids=("E2",),
    )

    items = [root_a, root_b, child, grandchild]
    root_fingerprint = _fingerprint(items, "E1")

    result = _evaluate(
        items,
        [
            _resolution(
                "E1",
                root_fingerprint,
            )
        ],
    )

    assert result.released_ids == {"E1"}
    assert result.quarantined_ids == {"E2", "E3"}
    assert result.accepted_ids == {"E1"}


def test_child_release_requires_its_own_explicit_resolution():
    root_a = _item(
        "E1",
        confirms_completion=True,
    )
    root_b = _item(
        "E1",
        requests_next_step=True,
    )

    child_a = _item(
        "E2",
        confirms_completion=True,
        parent_ids=("E1",),
    )
    child_b = _item(
        "E2",
        requests_followup=True,
        parent_ids=("E1",),
    )

    items = [root_a, root_b, child_a, child_b]

    root_fp = _fingerprint(items, "E1")
    child_fp = _fingerprint(items, "E2")

    root_only = _evaluate(
        items,
        [
            _resolution("E1", root_fp),
        ],
    )

    both_released = _evaluate(
        items,
        [
            _resolution("E1", root_fp, resolution_id="R-E1"),
            _resolution("E2", child_fp, resolution_id="R-E2"),
        ],
    )

    assert root_only.quarantined_ids == {"E2"}
    assert root_only.accepted_ids == {"E1"}

    assert both_released.quarantined_ids == frozenset()
    assert both_released.accepted_ids == {"E1", "E2"}


def test_releasing_child_without_releasing_parent_does_not_cleanse_child():
    root_a = _item(
        "E1",
        confirms_completion=True,
    )
    root_b = _item(
        "E1",
        requests_next_step=True,
    )

    child_a = _item(
        "E2",
        confirms_completion=True,
        parent_ids=("E1",),
    )
    child_b = _item(
        "E2",
        requests_followup=True,
        parent_ids=("E1",),
    )

    items = [root_a, root_b, child_a, child_b]
    child_fp = _fingerprint(items, "E2")

    result = _evaluate(
        items,
        [
            _resolution(
                "E2",
                child_fp,
            )
        ],
    )

    assert result.released_ids == {"E2"}
    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == {"E2"}


def test_multi_parent_child_stays_quarantined_when_one_parent_is_unresolved():
    e1a = _item(
        "E1",
        confirms_completion=True,
    )
    e1b = _item(
        "E1",
        requests_next_step=True,
    )

    e2a = _item(
        "E2",
        confirms_completion=True,
    )
    e2b = _item(
        "E2",
        requests_followup=True,
    )

    child = _item(
        "E3",
        parent_ids=("E1", "E2"),
    )

    items = [e1a, e1b, e2a, e2b, child]

    e1_fp = _fingerprint(items, "E1")
    e2_fp = _fingerprint(items, "E2")

    result = _evaluate(
        items,
        [
            _resolution("E1", e1_fp),
        ],
    )

    assert result.quarantined_ids == {"E2", "E3"}
    assert result.accepted_ids == {"E1"}


def test_multi_parent_child_can_clear_only_after_all_conflicting_parents_are_cleared():
    e1a = _item(
        "E1",
        confirms_completion=True,
    )
    e1b = _item(
        "E1",
        requests_next_step=True,
    )

    e2a = _item(
        "E2",
        confirms_completion=True,
    )
    e2b = _item(
        "E2",
        requests_followup=True,
    )

    child_a = _item(
        "E3",
        parent_ids=("E1", "E2"),
        confirms_completion=True,
    )
    child_b = _item(
        "E3",
        parent_ids=("E1", "E2"),
        requests_followup=True,
    )

    items = [e1a, e1b, e2a, e2b, child_a, child_b]

    e1_fp = _fingerprint(items, "E1")
    e2_fp = _fingerprint(items, "E2")
    e3_fp = _fingerprint(items, "E3")

    one_parent = _evaluate(
        items,
        [
            _resolution("E1", e1_fp, resolution_id="R1"),
        ],
    )

    all_parents = _evaluate(
        items,
        [
            _resolution("E1", e1_fp, resolution_id="R1"),
            _resolution("E2", e2_fp, resolution_id="R2"),
        ],
    )

    all_scopes = _evaluate(
        items,
        [
            _resolution("E1", e1_fp, resolution_id="R1"),
            _resolution("E2", e2_fp, resolution_id="R2"),
            _resolution("E3", e3_fp, resolution_id="R3"),
        ],
    )

    assert one_parent.quarantined_ids == {"E2", "E3"}
    assert all_parents.quarantined_ids == {"E3"}
    assert all_scopes.quarantined_ids == frozenset()


def test_independent_branch_is_not_affected_by_parent_release_requirements():
    e1a = _item(
        "E1",
        confirms_completion=True,
    )
    e1b = _item(
        "E1",
        requests_next_step=True,
    )
    child_of_e1 = _item(
        "E2",
        parent_ids=("E1",),
        requests_followup=True,
    )

    independent = _item(
        "E3",
        confirms_completion=True,
    )
    independent_child = _item(
        "E4",
        parent_ids=("E3",),
        requests_followup=True,
    )

    items = [
        e1a,
        e1b,
        child_of_e1,
        independent,
        independent_child,
    ]

    e1_fp = _fingerprint(items, "E1")

    result = _evaluate(
        items,
        [
            _resolution("E1", e1_fp),
        ],
    )

    assert result.quarantined_ids == {"E2"}
    assert result.accepted_ids == {"E1", "E3", "E4"}


def test_stale_parent_release_does_not_release_descendant():
    parent_a = _item(
        "E1",
        confirms_completion=True,
    )
    parent_b = _item(
        "E1",
        requests_next_step=True,
    )
    child = _item(
        "E2",
        parent_ids=("E1",),
        requests_followup=True,
    )

    old_items = [parent_a, parent_b, child]
    old_fp = _fingerprint(old_items, "E1")

    changed_parent = _item(
        "E1",
        requests_followup=True,
    )

    new_items = [
        parent_a,
        parent_b,
        changed_parent,
        child,
    ]

    result = _evaluate(
        new_items,
        [
            _resolution(
                "E1",
                old_fp,
                resolution_id="STALE",
            )
        ],
    )

    assert result.quarantined_ids == {"E1", "E2"}
    assert result.accepted_ids == set()


def test_child_with_no_direct_conflict_is_still_quarantined_by_parent_lineage():
    parent_a = _item(
        "E1",
        confirms_completion=True,
    )
    parent_b = _item(
        "E1",
        requests_next_step=True,
    )

    child = _item(
        "E2",
        parent_ids=("E1",),
        confirms_completion=True,
    )

    items = [parent_a, parent_b, child]

    result = _evaluate(items)

    assert result.quarantined_ids == {"E1", "E2"}
    assert result.accepted_ids == set()


def test_releasing_every_identity_requires_matching_current_fingerprints():
    e1a = _item(
        "E1",
        confirms_completion=True,
    )
    e1b = _item(
        "E1",
        requests_next_step=True,
    )

    e2a = _item(
        "E2",
        confirms_completion=True,
        parent_ids=("E1",),
    )
    e2b = _item(
        "E2",
        requests_followup=True,
        parent_ids=("E1",),
    )

    items = [e1a, e1b, e2a, e2b]

    e1_fp = _fingerprint(items, "E1")
    e2_fp = _fingerprint(items, "E2")

    wrong_e2_fp = _fingerprint(
        [
            _item(
                "E2",
                confirms_completion=True,
            ),
        ],
        "E2",
    )

    result = _evaluate(
        items,
        [
            _resolution("E1", e1_fp, resolution_id="R1"),
            _resolution("E2", wrong_e2_fp, resolution_id="R2"),
        ],
    )

    assert result.quarantined_ids == {"E2"}
    assert result.accepted_ids == {"E1"}


def test_release_evaluation_is_deterministic_under_reordering():
    e1a = _item(
        "E1",
        confirms_completion=True,
    )
    e1b = _item(
        "E1",
        requests_next_step=True,
    )
    child_a = _item(
        "E2",
        parent_ids=("E1",),
        confirms_completion=True,
    )
    child_b = _item(
        "E2",
        parent_ids=("E1",),
        requests_followup=True,
    )

    items = [e1a, e1b, child_a, child_b]

    e1_fp = _fingerprint(items, "E1")
    e2_fp = _fingerprint(items, "E2")

    resolutions = [
        _resolution("E1", e1_fp, resolution_id="R1"),
        _resolution("E2", e2_fp, resolution_id="R2"),
    ]

    forward = _evaluate(items, resolutions)
    reverse = _evaluate(
        list(reversed(items)),
        resolutions,
    )

    assert forward.quarantined_ids == reverse.quarantined_ids
    assert forward.accepted_ids == reverse.accepted_ids
    assert forward.released_ids == reverse.released_ids


def test_repeated_release_evaluation_is_idempotent():
    e1a = _item(
        "E1",
        confirms_completion=True,
    )
    e1b = _item(
        "E1",
        requests_next_step=True,
    )
    e2a = _item(
        "E2",
        parent_ids=("E1",),
        confirms_completion=True,
    )
    e2b = _item(
        "E2",
        parent_ids=("E1",),
        requests_followup=True,
    )

    items = [e1a, e1b, e2a, e2b]

    e1_fp = _fingerprint(items, "E1")
    e2_fp = _fingerprint(items, "E2")

    resolutions = [
        _resolution("E1", e1_fp, resolution_id="R1"),
        _resolution("E2", e2_fp, resolution_id="R2"),
    ]

    first = _evaluate(items, resolutions)
    second = _evaluate(items, resolutions)
    third = _evaluate(
        items,
        resolutions + resolutions,
    )

    assert first.quarantined_ids == second.quarantined_ids
    assert second.quarantined_ids == third.quarantined_ids

    assert first.accepted_ids == second.accepted_ids
    assert second.accepted_ids == third.accepted_ids