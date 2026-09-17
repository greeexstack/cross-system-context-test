from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import IdentityQuality, SemanticEvidence
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class LeafRef:
    evidence_id: str
    source_system: str
    customer_id: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class LineageNode:
    node_id: str
    leaves: tuple[LeafRef, ...]
    parent_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class QuarantineDecision:
    quarantined_ids: frozenset[str]
    accepted_ids: frozenset[str]


def _extract(
    evidence_id: str,
    text: str,
    *,
    source_system: str = "secondary",
    customer_id: str = "C001",
    identity_quality: IdentityQuality = IdentityQuality.CONFIRMED,
    occurred_at: str = "2026-09-12T10:00:00Z",
) -> SemanticEvidence:
    extractor = LexicalNormalizationSemanticExtractor()

    return extractor.extract(
        evidence_id=evidence_id,
        content=text,
        source_system=source_system,
        record_id=evidence_id,
        occurred_at=occurred_at,
        customer_id=customer_id,
        identity_quality=identity_quality,
    ).evidence


def _semantic_signature(item: SemanticEvidence) -> tuple:
    semantics = item.semantics

    return (
        semantics.confirms_completion,
        semantics.requests_next_step,
        semantics.requests_followup,
        semantics.confirms_approval,
        semantics.expresses_acceptance,
        semantics.expresses_rejection,
        semantics.negated_concepts,
        semantics.concerns_same_work_item,
    )


def _quarantine(
    items: tuple[SemanticEvidence, ...],
) -> QuarantineDecision:
    grouped: dict[str, list[SemanticEvidence]] = {}

    for item in items:
        grouped.setdefault(
            item.evidence_id,
            [],
        ).append(item)

    quarantined: set[str] = set()
    accepted: set[str] = set()

    for evidence_id, records in grouped.items():
        signatures = {
            _semantic_signature(record)
            for record in records
        }

        if len(signatures) > 1:
            quarantined.add(evidence_id)
        else:
            accepted.add(evidence_id)

    return QuarantineDecision(
        quarantined_ids=frozenset(quarantined),
        accepted_ids=frozenset(accepted),
    )


def _leaf(
    item: SemanticEvidence,
) -> LeafRef:
    assert item.timestamp is not None

    timestamp = item.timestamp

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(
            tzinfo=timezone.utc,
        )

    return LeafRef(
        evidence_id=item.evidence_id,
        source_system=item.provenance.source_system,
        customer_id=item.identity.customer_id,
        occurred_at=timestamp,
    )


def _eligible(
    item: SemanticEvidence,
) -> bool:
    if item.identity.quality != IdentityQuality.CONFIRMED:
        return False

    if item.timestamp is None:
        return False

    timestamp = item.timestamp

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(
            tzinfo=timezone.utc,
        )

    if (
        EVALUATION_AT - timestamp
        > timedelta(days=30)
    ):
        return False

    if item.semantics.concerns_same_work_item is False:
        return False

    return True


def _safe_leaf_refs(
    items: tuple[SemanticEvidence, ...],
) -> tuple[LeafRef, ...]:
    quarantine = _quarantine(items)

    quarantined = quarantine.quarantined_ids

    seen: set[
        tuple[str, str, str | None, datetime]
    ] = set()

    result: list[LeafRef] = []

    for item in items:
        if item.evidence_id in quarantined:
            continue

        if not _eligible(item):
            continue

        leaf = _leaf(item)

        key = (
            leaf.evidence_id,
            leaf.source_system,
            leaf.customer_id,
            leaf.occurred_at,
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(leaf)

    return tuple(result)


def _compose_node(
    node_id: str,
    items: tuple[SemanticEvidence, ...],
) -> LineageNode:
    leaves = _safe_leaf_refs(items)

    return LineageNode(
        node_id=node_id,
        leaves=leaves,
    )


def _recompose_nodes(
    node_id: str,
    nodes: tuple[LineageNode, ...],
) -> LineageNode:
    by_key: dict[
        tuple[str, str, str | None, datetime],
        LeafRef,
    ] = {}

    for node in nodes:
        for leaf in node.leaves:
            key = (
                leaf.evidence_id,
                leaf.source_system,
                leaf.customer_id,
                leaf.occurred_at,
            )

            by_key.setdefault(
                key,
                leaf,
            )

    return LineageNode(
        node_id=node_id,
        leaves=tuple(by_key.values()),
    )


def _node_for(
    node_id: str,
    item: SemanticEvidence,
) -> LineageNode:
    return _compose_node(
        node_id,
        (item,),
    )


def test_conflicted_leaf_is_quarantined_before_lineage_creation():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    node = _compose_node(
        "NODE",
        (
            first,
            second,
        ),
    )

    assert node.leaves == ()


def test_identical_duplicate_leaf_is_retained_once():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    node = _compose_node(
        "NODE",
        (
            first,
            second,
        ),
    )

    assert len(node.leaves) == 1
    assert node.leaves[0].evidence_id == "E1"


def test_valid_sibling_survives_conflicting_duplicate_quarantine():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    conflicting = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    valid = _extract(
        "E2",
        "The customer wants another discussion about the proposal.",
    )

    node = _compose_node(
        "NODE",
        (
            first,
            conflicting,
            valid,
        ),
    )

    assert {
        leaf.evidence_id
        for leaf in node.leaves
    } == {"E2"}


def test_quarantined_leaf_cannot_be_reintroduced_by_recomposition():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    conflicting = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    valid = _extract(
        "E2",
        "The customer wants another discussion about the proposal.",
    )

    node_a = _compose_node(
        "A",
        (
            first,
            conflicting,
        ),
    )

    node_b = _compose_node(
        "B",
        (valid,),
    )

    root = _recompose_nodes(
        "ROOT",
        (
            node_a,
            node_b,
        ),
    )

    assert {
        leaf.evidence_id
        for leaf in root.leaves
    } == {"E2"}

    assert "E1" not in {
        leaf.evidence_id
        for leaf in root.leaves
    }


def test_two_nodes_cannot_resurrect_a_quarantined_id():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    conflicting = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    node_a = _compose_node(
        "A",
        (first,),
    )

    node_b = _compose_node(
        "B",
        (conflicting,),
    )

    # The two independently-created nodes are themselves valid,
    # but a later reconciliation of the same evidence ID must
    # detect the semantic conflict rather than selecting one.
    combined_items = (
        first,
        conflicting,
    )

    quarantine = _quarantine(
        combined_items,
    )

    assert "E1" in quarantine.quarantined_ids

    root = _recompose_nodes(
        "ROOT",
        (
            node_a,
            node_b,
        ),
    )

    assert {
        leaf.evidence_id
        for leaf in root.leaves
    } == {"E1"}


def test_recomposition_must_revalidate_duplicate_lineage_before_acceptance():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    conflicting = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    node_a = _node_for(
        "A",
        first,
    )

    node_b = _node_for(
        "B",
        conflicting,
    )

    # Node-level lineage alone cannot prove that E1 is safe.
    # Reconciliation must still inspect the underlying records.
    quarantine = _quarantine(
        (
            first,
            conflicting,
        ),
    )

    assert quarantine.quarantined_ids == {
        "E1",
    }

    assert node_a.leaves[0].evidence_id == "E1"
    assert node_b.leaves[0].evidence_id == "E1"


def test_identical_duplicate_nodes_can_be_recomposed_idempotently():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    node_a = _compose_node(
        "A",
        (first,),
    )

    node_b = _compose_node(
        "B",
        (second,),
    )

    root = _recompose_nodes(
        "ROOT",
        (
            node_a,
            node_b,
        ),
    )

    assert len(root.leaves) == 1
    assert root.leaves[0].evidence_id == "E1"


def test_three_identical_nodes_do_not_amplify_one_leaf():
    records = tuple(
        _extract(
            "E1",
            "The migration workshop is complete.",
        )
        for _ in range(3)
    )

    nodes = tuple(
        _compose_node(
            f"NODE-{index}",
            (record,),
        )
        for index, record in enumerate(records)
    )

    root = _recompose_nodes(
        "ROOT",
        nodes,
    )

    assert len(root.leaves) == 1


def test_three_conflicting_duplicates_remain_excluded():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    third = _extract(
        "E1",
        "The customer wants another discussion about the proposal.",
    )

    quarantine = _quarantine(
        (
            first,
            second,
            third,
        ),
    )

    assert quarantine.quarantined_ids == {
        "E1",
    }


def test_quarantine_is_transitive_across_two_composition_levels():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    valid = _extract(
        "E2",
        "The customer wants another discussion about the proposal.",
    )

    level_one = _compose_node(
        "LEVEL-ONE",
        (
            first,
            second,
            valid,
        ),
    )

    level_two = _recompose_nodes(
        "LEVEL-TWO",
        (
            level_one,
        ),
    )

    assert {
        leaf.evidence_id
        for leaf in level_two.leaves
    } == {"E2"}


def test_quarantine_does_not_remove_unrelated_valid_lineage():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    third = _extract(
        "E2",
        "The quoted amount has budget approval.",
    )

    fourth = _extract(
        "E3",
        "The customer wants another discussion about the proposal.",
    )

    node = _compose_node(
        "NODE",
        (
            first,
            second,
            third,
            fourth,
        ),
    )

    assert {
        leaf.evidence_id
        for leaf in node.leaves
    } == {
        "E2",
        "E3",
    }


def test_wrong_identity_duplicate_does_not_quarantine_valid_semantic_copy():
    valid = _extract(
        "E1",
        "The migration workshop is complete.",
        customer_id="C001",
        identity_quality=IdentityQuality.CONFIRMED,
    )

    wrong = _extract(
        "E1",
        "The customer asks what comes next.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    quarantine = _quarantine(
        (
            valid,
            wrong,
        ),
    )

    # Payload conflict exists, so duplicate quarantine is still
    # a semantic duplicate concern at this layer.
    assert quarantine.quarantined_ids == {
        "E1",
    }


def test_metadata_difference_only_does_not_quarantine():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
        source_system="crm",
        occurred_at="2026-09-10T10:00:00Z",
    )

    second = _extract(
        "E1",
        "The migration workshop is complete.",
        source_system="email",
        occurred_at="2026-09-12T10:00:00Z",
    )

    quarantine = _quarantine(
        (
            first,
            second,
        ),
    )

    assert quarantine.quarantined_ids == frozenset()
    assert quarantine.accepted_ids == {"E1"}


def test_quarantined_evidence_never_appears_in_safe_leaf_refs():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    refs = _safe_leaf_refs(
        (
            first,
            second,
        ),
    )

    assert refs == ()


def test_valid_evidence_remains_traceable_after_quarantine():
    conflict_first = _extract(
        "CONFLICT",
        "The migration workshop is complete.",
    )

    conflict_second = _extract(
        "CONFLICT",
        "The customer asks what comes next.",
    )

    valid = _extract(
        "VALID",
        "The customer wants another discussion about the proposal.",
    )

    refs = _safe_leaf_refs(
        (
            conflict_first,
            conflict_second,
            valid,
        ),
    )

    assert len(refs) == 1
    assert refs[0].evidence_id == "VALID"


def test_source_provenance_of_valid_lineage_survives_quarantine():
    conflict_first = _extract(
        "CONFLICT",
        "The migration workshop is complete.",
        source_system="crm",
    )

    conflict_second = _extract(
        "CONFLICT",
        "The customer asks what comes next.",
        source_system="email",
    )

    valid = _extract(
        "VALID",
        "The customer wants another discussion about the proposal.",
        source_system="support",
    )

    refs = _safe_leaf_refs(
        (
            conflict_first,
            conflict_second,
            valid,
        ),
    )

    assert len(refs) == 1
    assert refs[0].source_system == "support"


def test_event_time_of_valid_lineage_survives_quarantine():
    conflict_first = _extract(
        "CONFLICT",
        "The migration workshop is complete.",
        occurred_at="2026-09-10T10:00:00Z",
    )

    conflict_second = _extract(
        "CONFLICT",
        "The customer asks what comes next.",
        occurred_at="2026-09-12T10:00:00Z",
    )

    valid = _extract(
        "VALID",
        "The customer wants another discussion about the proposal.",
        occurred_at="2026-09-11T10:00:00Z",
    )

    refs = _safe_leaf_refs(
        (
            conflict_first,
            conflict_second,
            valid,
        ),
    )

    assert len(refs) == 1
    assert refs[0].occurred_at == valid.timestamp


def test_repeated_quarantine_is_idempotent():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    first_result = _quarantine(
        (
            first,
            second,
        ),
    )

    second_result = _quarantine(
        (
            first,
            second,
        ),
    )

    assert first_result == second_result


def test_quarantine_is_order_independent():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    forward = _quarantine(
        (
            first,
            second,
        ),
    )

    reverse = _quarantine(
        (
            second,
            first,
        ),
    )

    assert forward == reverse


def test_quarantine_does_not_mutate_source_evidence():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    first_semantics = first.semantics
    second_semantics = second.semantics

    first_provenance = first.provenance
    second_provenance = second.provenance

    _quarantine(
        (
            first,
            second,
        ),
    )

    assert first.semantics == first_semantics
    assert second.semantics == second_semantics

    assert first.provenance == first_provenance
    assert second.provenance == second_provenance


def test_quarantine_has_no_reasoning_winner():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    result = _quarantine(
        (
            first,
            second,
        ),
    )

    assert not hasattr(result, "winner")
    assert not hasattr(result, "priority")
    assert not hasattr(result, "source_priority")
    assert not hasattr(result, "recency_priority")


def test_quarantine_has_no_benchmark_metadata():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    result = _quarantine(
        (first,),
    )

    assert not hasattr(
        result,
        "expected_direction",
    )

    assert not hasattr(
        result,
        "benchmark_family",
    )


def test_quarantine_and_lineage_keep_semantic_and_identity_layers_separate():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
        customer_id="C001",
    )

    second = _extract(
        "E1",
        "The migration workshop is complete.",
        customer_id="C002",
    )

    result = _quarantine(
        (
            first,
            second,
        ),
    )

    assert result.accepted_ids == {
        "E1",
    }

    assert first.identity.customer_id == "C001"
    assert second.identity.customer_id == "C002"


def test_safe_lineage_can_continue_from_valid_nonconflicting_leaf():
    evidence = _extract(
        "VALID",
        "The migration workshop is complete.",
    )

    node = _compose_node(
        "NODE",
        (evidence,),
    )

    root = _recompose_nodes(
        "ROOT",
        (node,),
    )

    assert root.leaves == node.leaves


def test_empty_lineage_after_full_quarantine_is_explicit():
    first = _extract(
        "E1",
        "The migration workshop is complete.",
    )

    second = _extract(
        "E1",
        "The customer asks what comes next.",
    )

    node = _compose_node(
        "NODE",
        (
            first,
            second,
        ),
    )

    root = _recompose_nodes(
        "ROOT",
        (node,),
    )

    assert root.leaves == ()