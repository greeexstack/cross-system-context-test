"""
Incremental quarantine state.

Candidate test-layer contract:

- Evidence can arrive in multiple batches.
- Incremental evaluation must converge to the same state as evaluating
  the complete evidence set.
- A later batch may create quarantine, but must not erase an earlier one.
- Reordering batches must not change the final result.
- Replaying a batch must be idempotent.
- A benign batch must not cleanse an existing quarantine.
- Lineage quarantine must propagate across batch boundaries.
- Explicit release must be evaluated against the current complete state.

No production behavior is changed by this experiment.
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


def _evaluate(items):
    items = tuple(items)

    by_id = {}
    parents_by_id = {}

    for item in items:
        by_id.setdefault(item.evidence_id, []).append(item)
        parents_by_id.setdefault(item.evidence_id, set()).update(
            item.parent_ids
        )

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


def _incremental(batches):
    accumulated = []

    states = []

    for batch in batches:
        accumulated.extend(batch)
        states.append(
            _evaluate(accumulated)
        )

    return states


def test_single_batch_matches_all_at_once():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
        _item("E2", requests_followup=True),
    ]

    full = _evaluate(items)
    incremental = _incremental([items])[-1]

    assert full.quarantined_ids == incremental.quarantined_ids
    assert full.accepted_ids == incremental.accepted_ids


def test_late_conflict_can_create_quarantine():
    first = [
        _item("E1", confirms_completion=True),
    ]
    second = [
        _item("E1", requests_next_step=True),
    ]

    states = _incremental([first, second])

    assert states[0].quarantined_ids == frozenset()
    assert states[0].accepted_ids == {"E1"}

    assert states[1].quarantined_ids == {"E1"}
    assert states[1].accepted_ids == set()


def test_late_benign_evidence_does_not_clear_existing_quarantine():
    first = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]
    second = [
        _item("E2", requests_followup=True),
    ]

    states = _incremental([first, second])

    assert states[0].quarantined_ids == {"E1"}
    assert states[1].quarantined_ids == {"E1"}
    assert states[1].accepted_ids == {"E2"}


def test_batch_order_does_not_change_final_state():
    a = [
        _item("E1", confirms_completion=True),
    ]
    b = [
        _item("E2", requests_followup=True),
    ]
    c = [
        _item("E1", requests_next_step=True),
    ]

    forward = _incremental([a, b, c])[-1]
    reverse = _incremental([c, b, a])[-1]

    assert forward.quarantined_ids == reverse.quarantined_ids
    assert forward.accepted_ids == reverse.accepted_ids


def test_split_batches_match_complete_evaluation():
    a = [
        _item("E1", confirms_completion=True),
        _item("E2", requests_followup=True),
    ]
    b = [
        _item("E1", requests_next_step=True),
    ]
    c = [
        _item("E3", confirms_completion=True),
    ]

    full = _evaluate(a + b + c)
    incremental = _incremental([a, b, c])[-1]

    assert full.quarantined_ids == {"E1"}
    assert full.accepted_ids == {"E2", "E3"}

    assert incremental.quarantined_ids == full.quarantined_ids
    assert incremental.accepted_ids == full.accepted_ids


def test_replayed_batch_is_idempotent():
    first = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]

    replay = list(first)

    once = _incremental([first])[-1]
    twice = _incremental([first, replay])[-1]

    assert once.quarantined_ids == {"E1"}
    assert twice.quarantined_ids == {"E1"}

    assert once.accepted_ids == twice.accepted_ids == set()


def test_replaying_benign_batch_does_not_change_state():
    first = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]
    benign = [
        _item("E2", requests_followup=True),
    ]

    once = _incremental([first, benign])[-1]
    replayed = _incremental(
        [first, benign, benign]
    )[-1]

    assert once.quarantined_ids == {"E1"}
    assert replayed.quarantined_ids == {"E1"}

    assert once.accepted_ids == {"E2"}
    assert replayed.accepted_ids == {"E2"}


def test_lineage_quarantine_can_cross_batch_boundary():
    first = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]

    second = [
        _item(
            "E2",
            parent_ids=("E1",),
            requests_followup=True,
        ),
    ]

    states = _incremental([first, second])

    assert states[0].quarantined_ids == {"E1"}
    assert states[1].quarantined_ids == {"E1", "E2"}
    assert states[1].accepted_ids == set()


def test_child_arriving_before_conflicted_parent_is_reclassified_later():
    child = [
        _item(
            "E2",
            parent_ids=("E1",),
            requests_followup=True,
        ),
    ]

    parent_first = [
        _item("E1", confirms_completion=True),
    ]

    parent_conflict = [
        _item("E1", requests_next_step=True),
    ]

    states = _incremental(
        [
            child,
            parent_first,
            parent_conflict,
        ]
    )

    assert states[0].quarantined_ids == frozenset()
    assert states[0].accepted_ids == {"E2"}

    assert states[1].quarantined_ids == frozenset()
    assert states[1].accepted_ids == {"E1", "E2"}

    assert states[2].quarantined_ids == {"E1", "E2"}
    assert states[2].accepted_ids == set()


def test_independent_branch_survives_late_quarantine_elsewhere():
    first = [
        _item(
            "E2",
            confirms_completion=True,
        ),
        _item(
            "E3",
            parent_ids=("E2",),
            requests_followup=True,
        ),
    ]

    conflict = [
        _item(
            "E1",
            confirms_completion=True,
        ),
        _item(
            "E1",
            requests_next_step=True,
        ),
    ]

    result = _incremental([first, conflict])[-1]

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == {"E2", "E3"}


def test_incremental_result_is_stable_after_quarantine_creation():
    first = [
        _item("E1", confirms_completion=True),
    ]
    conflict = [
        _item("E1", requests_next_step=True),
    ]
    benign = [
        _item("E2", requests_followup=True),
        _item("E3", confirms_completion=True),
    ]

    states = _incremental(
        [first, conflict, benign]
    )

    assert states[1].quarantined_ids == {"E1"}
    assert states[2].quarantined_ids == {"E1"}

    assert states[2].accepted_ids == {"E2", "E3"}


def test_multiple_late_conflicts_accumulate_monotonically():
    first = [
        _item("E1", confirms_completion=True),
    ]

    second = [
        _item("E1", requests_next_step=True),
        _item("E2", confirms_completion=True),
    ]

    third = [
        _item("E2", requests_followup=True),
    ]

    states = _incremental(
        [first, second, third]
    )

    assert states[0].quarantined_ids == frozenset()
    assert states[1].quarantined_ids == {"E1"}
    assert states[2].quarantined_ids == {"E1", "E2"}

    assert states[2].accepted_ids == set()


def test_incremental_quarantine_matches_full_graph_closure():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
        _item("E2", parent_ids=("E1",)),
        _item("E3", parent_ids=("E2",)),
        _item("E4", confirms_completion=True),
        _item("E5", parent_ids=("E4",)),
    ]

    batches = [
        items[:2],
        items[2:4],
        items[4:],
    ]

    incremental = _incremental(batches)[-1]
    full = _evaluate(items)

    assert full.quarantined_ids == {"E1", "E2", "E3"}
    assert full.accepted_ids == {"E4", "E5"}

    assert incremental.quarantined_ids == full.quarantined_ids
    assert incremental.accepted_ids == full.accepted_ids


def test_empty_batch_does_not_change_state():
    first = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
    ]

    states = _incremental(
        [first, [], []]
    )

    assert states[0].quarantined_ids == {"E1"}
    assert states[1].quarantined_ids == {"E1"}
    assert states[2].quarantined_ids == {"E1"}

    assert states[0].accepted_ids == states[1].accepted_ids
    assert states[1].accepted_ids == states[2].accepted_ids


def test_duplicate_ordered_batches_match_single_merged_batch():
    batch_a = [
        _item("E1", confirms_completion=True),
        _item("E2", requests_followup=True),
    ]

    batch_b = [
        _item("E1", requests_next_step=True),
    ]

    incremental = _incremental(
        [batch_a, batch_b]
    )[-1]

    merged = _evaluate(
        batch_a + batch_b
    )

    assert incremental.quarantined_ids == merged.quarantined_ids
    assert incremental.accepted_ids == merged.accepted_ids


def test_final_state_is_partitioned():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
        _item("E2", requests_followup=True),
        _item("E3", confirms_completion=True),
    ]

    result = _incremental(
        [items[:1], items[1:]]
    )[-1]

    assert result.quarantined_ids.isdisjoint(
        result.accepted_ids
    )

    assert (
        result.quarantined_ids
        | result.accepted_ids
        == {"E1", "E2", "E3"}
    )


def test_many_small_batches_converge_to_full_result():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
        _item("E2", confirms_completion=True),
        _item("E3", parent_ids=("E2",)),
        _item("E4", requests_followup=True),
        _item("E5", confirms_completion=True),
        _item("E5", requests_followup=True),
    ]

    batches = [[item] for item in items]

    incremental = _incremental(batches)[-1]
    full = _evaluate(items)

    assert incremental.quarantined_ids == full.quarantined_ids
    assert incremental.accepted_ids == full.accepted_ids


def test_reordered_small_batches_converge_to_same_result():
    items = [
        _item("E1", confirms_completion=True),
        _item("E1", requests_next_step=True),
        _item("E2", confirms_completion=True),
        _item("E3", parent_ids=("E2",)),
        _item("E4", requests_followup=True),
    ]

    batches = [[item] for item in items]

    forward = _incremental(batches)[-1]
    reverse = _incremental(
        list(reversed(batches))
    )[-1]

    assert forward.quarantined_ids == reverse.quarantined_ids
    assert forward.accepted_ids == reverse.accepted_ids