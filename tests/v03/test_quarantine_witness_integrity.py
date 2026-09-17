"""
Quarantine witness / audit integrity.

These tests probe a candidate contract for operational explainability:

- every quarantine must have identifiable conflict witnesses;
- the witnesses must preserve semantic payload and source lineage;
- unrelated evidence must not appear in the witness set;
- identical duplicates must not manufacture a conflict;
- ordering must not affect the audit result.

This is intentionally test-layer work. Production behavior is unchanged.
"""


def _item(
    evidence_id,
    *,
    source_system,
    source_id,
    confirms_completion=False,
    requests_next_step=False,
    requests_followup=False,
    confirms_approval=False,
    expresses_rejection=False,
    parent_ids=(),
):
    class Item:
        pass

    item = Item()
    item.evidence_id = evidence_id
    item.source_system = source_system
    item.source_id = source_id
    item.confirms_completion = confirms_completion
    item.requests_next_step = requests_next_step
    item.requests_followup = requests_followup
    item.confirms_approval = confirms_approval
    item.expresses_rejection = expresses_rejection
    item.parent_ids = tuple(parent_ids)
    return item


def _payload(item):
    return (
        item.confirms_completion,
        item.requests_next_step,
        item.requests_followup,
        item.confirms_approval,
        item.expresses_rejection,
    )


def _evaluate(items):
    """
    Candidate audit model.

    A quarantined identity retains all distinct semantic variants that caused
    the conflict. Each witness also retains its source and lineage metadata.
    """
    items = tuple(items)

    by_id = {}
    for item in items:
        by_id.setdefault(item.evidence_id, []).append(item)

    quarantined = set()
    accepted = set()
    witnesses = {}

    for identity, variants in by_id.items():
        payload_groups = {}

        for item in variants:
            payload_groups.setdefault(_payload(item), []).append(item)

        if len(payload_groups) > 1:
            quarantined.add(identity)

            identity_witnesses = []

            for payload, members in payload_groups.items():
                representative = members[0]

                identity_witnesses.append(
                    {
                        "evidence_id": identity,
                        "payload": payload,
                        "source_system": representative.source_system,
                        "source_id": representative.source_id,
                        "parent_ids": representative.parent_ids,
                    }
                )

            witnesses[identity] = tuple(
                sorted(
                    identity_witnesses,
                    key=lambda witness: (
                        witness["source_system"],
                        witness["source_id"],
                        witness["payload"],
                    ),
                )
            )
        else:
            accepted.add(identity)

    accepted -= quarantined

    class Result:
        pass

    result = Result()
    result.accepted_ids = accepted
    result.quarantined_ids = frozenset(quarantined)
    result.witnesses = witnesses
    return result


def test_quarantine_retains_all_conflicting_semantic_variants():
    a = _item(
        "E1",
        source_system="system-a",
        source_id="A-1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        source_system="system-b",
        source_id="B-1",
        requests_next_step=True,
    )

    result = _evaluate([a, b])

    assert result.quarantined_ids == {"E1"}
    assert len(result.witnesses["E1"]) == 2

    payloads = {
        witness["payload"]
        for witness in result.witnesses["E1"]
    }

    assert payloads == {
        (True, False, False, False, False),
        (False, True, False, False, False),
    }


def test_quarantine_witnesses_preserve_source_identity():
    a = _item(
        "E1",
        source_system="crm",
        source_id="CRM-17",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        source_system="billing",
        source_id="BILL-44",
        requests_next_step=True,
    )

    result = _evaluate([a, b])

    sources = {
        (
            witness["source_system"],
            witness["source_id"],
        )
        for witness in result.witnesses["E1"]
    }

    assert sources == {
        ("crm", "CRM-17"),
        ("billing", "BILL-44"),
    }


def test_quarantine_witnesses_preserve_parent_lineage():
    a = _item(
        "E1",
        source_system="system-a",
        source_id="A-1",
        confirms_completion=True,
        parent_ids=("P1",),
    )
    b = _item(
        "E1",
        source_system="system-b",
        source_id="B-1",
        requests_next_step=True,
        parent_ids=("P2", "P3"),
    )

    result = _evaluate([a, b])

    lineage = {
        witness["parent_ids"]
        for witness in result.witnesses["E1"]
    }

    assert lineage == {
        ("P1",),
        ("P2", "P3"),
    }


def test_unrelated_evidence_does_not_pollute_quarantine_witnesses():
    a = _item(
        "E1",
        source_system="system-a",
        source_id="A-1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        source_system="system-b",
        source_id="B-1",
        requests_next_step=True,
    )
    unrelated = _item(
        "E2",
        source_system="system-c",
        source_id="C-1",
        requests_followup=True,
    )

    result = _evaluate([a, b, unrelated])

    assert result.quarantined_ids == {"E1"}
    assert "E2" in result.accepted_ids

    witness_ids = {
        witness["evidence_id"]
        for witness in result.witnesses["E1"]
    }

    assert witness_ids == {"E1"}


def test_identical_duplicates_do_not_create_fake_witness_conflict():
    a = _item(
        "E1",
        source_system="system-a",
        source_id="A-1",
        confirms_completion=True,
    )
    duplicate = _item(
        "E1",
        source_system="system-a",
        source_id="A-1-copy",
        confirms_completion=True,
    )

    result = _evaluate([a, duplicate])

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}
    assert result.witnesses == {}


def test_metadata_difference_only_does_not_create_witness_conflict():
    a = _item(
        "E1",
        source_system="system-a",
        source_id="A-1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        source_system="system-b",
        source_id="B-1",
        confirms_completion=True,
    )

    result = _evaluate([a, b])

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}
    assert result.witnesses == {}


def test_witness_result_is_order_independent():
    a = _item(
        "E1",
        source_system="system-a",
        source_id="A-1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        source_system="system-b",
        source_id="B-1",
        expresses_rejection=True,
    )

    forward = _evaluate([a, b])
    reverse = _evaluate([b, a])

    assert forward.quarantined_ids == reverse.quarantined_ids
    assert forward.accepted_ids == reverse.accepted_ids
    assert forward.witnesses == reverse.witnesses


def test_each_quarantine_has_at_least_two_distinct_witness_payloads():
    a = _item(
        "E1",
        source_system="system-a",
        source_id="A-1",
        confirms_completion=True,
    )
    b = _item(
        "E1",
        source_system="system-b",
        source_id="B-1",
        requests_next_step=True,
    )
    c = _item(
        "E1",
        source_system="system-c",
        source_id="C-1",
        requests_followup=True,
    )

    result = _evaluate([a, b, c])

    assert result.quarantined_ids == {"E1"}
    assert len(result.witnesses["E1"]) == 3

    witness_payloads = {
        witness["payload"]
        for witness in result.witnesses["E1"]
    }

    assert len(witness_payloads) == 3


def test_multiple_quarantined_identities_keep_separate_witness_sets():
    e1a = _item(
        "E1",
        source_system="system-a",
        source_id="A-1",
        confirms_completion=True,
    )
    e1b = _item(
        "E1",
        source_system="system-b",
        source_id="B-1",
        requests_next_step=True,
    )
    e2a = _item(
        "E2",
        source_system="system-c",
        source_id="C-1",
        confirms_completion=True,
    )
    e2b = _item(
        "E2",
        source_system="system-d",
        source_id="D-1",
        expresses_rejection=True,
    )

    result = _evaluate([e1a, e1b, e2a, e2b])

    assert result.quarantined_ids == {"E1", "E2"}

    assert {
        witness["source_id"]
        for witness in result.witnesses["E1"]
    } == {"A-1", "B-1"}

    assert {
        witness["source_id"]
        for witness in result.witnesses["E2"]
    } == {"C-1", "D-1"}


def test_clean_identity_has_no_quarantine_witness_record():
    clean = _item(
        "E1",
        source_system="system-a",
        source_id="A-1",
        confirms_completion=True,
    )

    result = _evaluate([clean])

    assert result.quarantined_ids == frozenset()
    assert result.accepted_ids == {"E1"}
    assert "E1" not in result.witnesses


def test_quarantine_witnesses_are_partitioned_from_accepted_ids():
    conflict_a = _item(
        "E1",
        source_system="system-a",
        source_id="A-1",
        confirms_completion=True,
    )
    conflict_b = _item(
        "E1",
        source_system="system-b",
        source_id="B-1",
        requests_next_step=True,
    )
    clean = _item(
        "E2",
        source_system="system-c",
        source_id="C-1",
        requests_followup=True,
    )

    result = _evaluate([conflict_a, conflict_b, clean])

    assert result.quarantined_ids.isdisjoint(
        result.accepted_ids
    )
    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == {"E2"}
    assert set(result.witnesses) == {"E1"}


def test_three_way_conflict_preserves_all_sources_without_duplication():
    items = [
        _item(
            "E1",
            source_system="system-a",
            source_id="A-1",
            confirms_completion=True,
        ),
        _item(
            "E1",
            source_system="system-b",
            source_id="B-1",
            requests_next_step=True,
        ),
        _item(
            "E1",
            source_system="system-c",
            source_id="C-1",
            requests_followup=True,
        ),
        _item(
            "E2",
            source_system="system-d",
            source_id="D-1",
            confirms_approval=True,
        ),
    ]

    result = _evaluate(items)

    assert result.quarantined_ids == {"E1"}
    assert result.accepted_ids == {"E2"}

    assert {
        witness["source_id"]
        for witness in result.witnesses["E1"]
    } == {"A-1", "B-1", "C-1"}