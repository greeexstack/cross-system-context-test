from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from experiment.v03.battery import EVALUATION_AT
from experiment.v03.evidence import (
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.normalized_extractor import (
    LexicalNormalizationSemanticExtractor,
)


@dataclass(frozen=True)
class LineageLeaf:
    evidence_id: str
    source_system: str
    customer_id: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class LineageNode:
    node_id: str
    leaves: tuple[LineageLeaf, ...]


@dataclass(frozen=True)
class ComposedLineage:
    node_id: str
    contributors: tuple[LineageLeaf, ...]
    confirms_completion: bool
    requests_next_step: bool
    requests_followup: bool


def _extract(
    evidence_id: str,
    source_system: str,
    text: str,
    *,
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


def _leaf(
    item: SemanticEvidence,
) -> LineageLeaf:
    assert item.timestamp is not None

    timestamp = item.timestamp

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(
            tzinfo=timezone.utc,
        )

    return LineageLeaf(
        evidence_id=item.evidence_id,
        source_system=item.provenance.source_system,
        customer_id=item.identity.customer_id,
        occurred_at=timestamp,
    )


def _compose_direct(
    node_id: str,
    items: tuple[SemanticEvidence, ...],
) -> ComposedLineage:
    eligible = tuple(
        item
        for item in items
        if (
            item.identity.quality == IdentityQuality.CONFIRMED
            and item.timestamp is not None
            and EVALUATION_AT - item.timestamp
            <= __import__("datetime").timedelta(days=30)
            and item.semantics.concerns_same_work_item is not False
        )
    )

    customers = {
        item.identity.customer_id
        for item in eligible
        if item.identity.customer_id is not None
    }

    if len(customers) > 1:
        return ComposedLineage(
            node_id=node_id,
            contributors=(),
            confirms_completion=False,
            requests_next_step=False,
            requests_followup=False,
        )

    leaves = tuple(
        _leaf(item)
        for item in eligible
    )

    return ComposedLineage(
        node_id=node_id,
        contributors=leaves,
        confirms_completion=any(
            item.semantics.confirms_completion is True
            and "completion"
            not in item.semantics.negated_concepts
            for item in eligible
        ),
        requests_next_step=any(
            item.semantics.requests_next_step is True
            and "next_step"
            not in item.semantics.negated_concepts
            for item in eligible
        ),
        requests_followup=any(
            item.semantics.requests_followup is True
            and "followup"
            not in item.semantics.negated_concepts
            for item in eligible
        ),
    )


def _recompose(
    node_id: str,
    nodes: tuple[ComposedLineage, ...],
) -> ComposedLineage:
    leaves: list[LineageLeaf] = []

    seen: set[tuple[str, str, str | None, datetime]] = set()

    completion = False
    next_step = False
    followup = False

    for node in nodes:
        for leaf in node.contributors:
            key = (
                leaf.evidence_id,
                leaf.source_system,
                leaf.customer_id,
                leaf.occurred_at,
            )

            if key in seen:
                continue

            seen.add(key)
            leaves.append(leaf)

        completion = completion or node.confirms_completion
        next_step = next_step or node.requests_next_step
        followup = followup or node.requests_followup

    return ComposedLineage(
        node_id=node_id,
        contributors=tuple(leaves),
        confirms_completion=completion,
        requests_next_step=next_step,
        requests_followup=followup,
    )


def test_direct_composition_creates_one_lineage_leaf_per_source_record():
    completion = _extract(
        "CRM-COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "EMAIL-NEXT",
        "email",
        "The customer asks what comes next.",
    )

    result = _compose_direct(
        "COMPOSED",
        (
            completion,
            next_step,
        ),
    )

    assert set(
        leaf.evidence_id
        for leaf in result.contributors
    ) == {
        "CRM-COMPLETION",
        "EMAIL-NEXT",
    }


def test_direct_composition_retains_source_system_per_leaf():
    completion = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "EMAIL",
        "email",
        "The customer asks what comes next.",
    )

    result = _compose_direct(
        "COMPOSED",
        (
            completion,
            next_step,
        ),
    )

    by_id = {
        leaf.evidence_id: leaf
        for leaf in result.contributors
    }

    assert by_id["CRM"].source_system == "crm"
    assert by_id["EMAIL"].source_system == "email"


def test_direct_composition_retains_customer_identity_per_leaf():
    first = _extract(
        "A",
        "crm",
        "The migration workshop is complete.",
        customer_id="C001",
    )

    second = _extract(
        "B",
        "email",
        "The customer asks what comes next.",
        customer_id="C001",
    )

    result = _compose_direct(
        "COMPOSED",
        (
            first,
            second,
        ),
    )

    assert {
        leaf.customer_id
        for leaf in result.contributors
    } == {
        "C001",
    }


def test_direct_composition_retains_event_time_per_leaf():
    first = _extract(
        "EARLY",
        "crm",
        "The migration workshop is complete.",
        occurred_at="2026-09-10T10:00:00Z",
    )

    second = _extract(
        "LATE",
        "email",
        "The customer asks what comes next.",
        occurred_at="2026-09-12T10:00:00Z",
    )

    result = _compose_direct(
        "COMPOSED",
        (
            first,
            second,
        ),
    )

    by_id = {
        leaf.evidence_id: leaf
        for leaf in result.contributors
    }

    assert by_id["EARLY"].occurred_at < by_id["LATE"].occurred_at


def test_recomposition_preserves_original_leaf_identity():
    first = _extract(
        "A",
        "crm",
        "The migration workshop is complete.",
    )

    second = _extract(
        "B",
        "email",
        "The customer asks what comes next.",
    )

    first_node = _compose_direct(
        "NODE-A",
        (first,),
    )

    second_node = _compose_direct(
        "NODE-B",
        (second,),
    )

    recomposed = _recompose(
        "NODE-C",
        (
            first_node,
            second_node,
        ),
    )

    assert {
        leaf.evidence_id
        for leaf in recomposed.contributors
    } == {
        "A",
        "B",
    }


def test_recomposition_preserves_source_systems():
    first = _extract(
        "CRM",
        "crm",
        "The migration workshop is complete.",
    )

    second = _extract(
        "EMAIL",
        "email",
        "The customer asks what comes next.",
    )

    first_node = _compose_direct(
        "NODE-A",
        (first,),
    )

    second_node = _compose_direct(
        "NODE-B",
        (second,),
    )

    recomposed = _recompose(
        "NODE-C",
        (
            first_node,
            second_node,
        ),
    )

    assert {
        leaf.source_system
        for leaf in recomposed.contributors
    } == {
        "crm",
        "email",
    }


def test_recomposition_preserves_event_times():
    first = _extract(
        "EARLY",
        "crm",
        "The migration workshop is complete.",
        occurred_at="2026-09-10T10:00:00Z",
    )

    second = _extract(
        "LATE",
        "email",
        "The customer asks what comes next.",
        occurred_at="2026-09-12T10:00:00Z",
    )

    first_node = _compose_direct(
        "NODE-A",
        (first,),
    )

    second_node = _compose_direct(
        "NODE-B",
        (second,),
    )

    recomposed = _recompose(
        "NODE-C",
        (
            first_node,
            second_node,
        ),
    )

    by_id = {
        leaf.evidence_id: leaf
        for leaf in recomposed.contributors
    }

    assert by_id["EARLY"].occurred_at == first.timestamp
    assert by_id["LATE"].occurred_at == second.timestamp


def test_recomposition_preserves_semantic_dimensions():
    completion = _extract(
        "COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    next_step = _extract(
        "NEXT",
        "email",
        "The customer asks what comes next.",
    )

    first_node = _compose_direct(
        "NODE-A",
        (completion,),
    )

    second_node = _compose_direct(
        "NODE-B",
        (next_step,),
    )

    recomposed = _recompose(
        "NODE-C",
        (
            first_node,
            second_node,
        ),
    )

    assert recomposed.confirms_completion is True
    assert recomposed.requests_next_step is True


def test_recomposing_the_same_node_is_idempotent():
    completion = _extract(
        "COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    node = _compose_direct(
        "NODE-A",
        (completion,),
    )

    recomposed = _recompose(
        "NODE-B",
        (
            node,
            node,
        ),
    )

    assert len(recomposed.contributors) == 1
    assert recomposed.contributors[0].evidence_id == "COMPLETION"


def test_nested_duplicate_nodes_do_not_amplify_one_leaf():
    completion = _extract(
        "COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    node_a = _compose_direct(
        "NODE-A",
        (completion,),
    )

    node_b = _compose_direct(
        "NODE-B",
        (completion,),
    )

    recomposed = _recompose(
        "NODE-C",
        (
            node_a,
            node_b,
        ),
    )

    assert len(recomposed.contributors) == 1


def test_nested_composition_does_not_duplicate_semantic_truth():
    completion = _extract(
        "COMPLETION",
        "crm",
        "The migration workshop is complete.",
    )

    node_a = _compose_direct(
        "NODE-A",
        (completion,),
    )

    node_b = _compose_direct(
        "NODE-B",
        (completion,),
    )

    recomposed = _recompose(
        "NODE-C",
        (
            node_a,
            node_b,
        ),
    )

    assert recomposed.confirms_completion is True
    assert recomposed.requests_next_step is False
    assert recomposed.requests_followup is False


def test_conflicting_leaf_facts_survive_nested_composition():
    positive = _extract(
        "POSITIVE",
        "crm",
        "The customer wants another discussion about the proposal.",
    )

    negative = _extract(
        "NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
    )

    positive_node = _compose_direct(
        "NODE-POSITIVE",
        (positive,),
    )

    negative_node = _compose_direct(
        "NODE-NEGATIVE",
        (negative,),
    )

    recomposed = _recompose(
        "NODE-CONFLICT",
        (
            positive_node,
            negative_node,
        ),
    )

    assert recomposed.requests_followup is True

    assert {
        leaf.evidence_id
        for leaf in recomposed.contributors
    } == {
        "POSITIVE",
        "NEGATIVE",
    }


def test_nested_conflict_does_not_erase_negative_source_lineage():
    negative = _extract(
        "NEGATIVE",
        "email",
        "The customer does not want another discussion about the proposal.",
    )

    node = _compose_direct(
        "NODE",
        (negative,),
    )

    recomposed = _recompose(
        "ROOT",
        (node,),
    )

    assert recomposed.contributors[0].evidence_id == "NEGATIVE"
    assert recomposed.contributors[0].source_system == "email"


def test_invalid_identity_is_not_added_to_lineage():
    valid = _extract(
        "VALID",
        "crm",
        "The migration workshop is complete.",
        customer_id="C001",
    )

    invalid = _extract(
        "INVALID",
        "email",
        "The customer asks what comes next.",
        customer_id="C999",
        identity_quality=IdentityQuality.NO_MATCH,
    )

    node = _compose_direct(
        "NODE",
        (
            valid,
            invalid,
        ),
    )

    assert {
        leaf.evidence_id
        for leaf in node.contributors
    } == {
        "VALID",
    }


def test_conflicting_customer_identity_blocks_direct_lineage_merge():
    first = _extract(
        "CUSTOMER-A",
        "crm",
        "The migration workshop is complete.",
        customer_id="C001",
    )

    second = _extract(
        "CUSTOMER-B",
        "email",
        "The customer asks what comes next.",
        customer_id="C002",
    )

    node = _compose_direct(
        "NODE",
        (
            first,
            second,
        ),
    )

    assert node.contributors == ()
    assert node.confirms_completion is False
    assert node.requests_next_step is False


def test_lineage_node_ids_do_not_replace_leaf_evidence_ids():
    evidence = _extract(
        "REAL-EVIDENCE",
        "crm",
        "The migration workshop is complete.",
    )

    node = _compose_direct(
        "SYNTHETIC-NODE",
        (evidence,),
    )

    assert node.node_id == "SYNTHETIC-NODE"

    assert node.contributors[0].evidence_id == (
        "REAL-EVIDENCE"
    )


def test_synthetic_node_id_is_not_a_source_record_id():
    evidence = _extract(
        "REAL-EVIDENCE",
        "crm",
        "The migration workshop is complete.",
    )

    node = _compose_direct(
        "SYNTHETIC-NODE",
        (evidence,),
    )

    assert node.node_id != node.contributors[0].evidence_id


def test_lineage_is_preserved_across_three_composition_levels():
    first = _extract(
        "FIRST",
        "crm",
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "email",
        "The customer asks what comes next.",
    )

    third = _extract(
        "THIRD",
        "support",
        "The customer wants another discussion about the proposal.",
    )

    node_a = _compose_direct(
        "A",
        (first,),
    )

    node_b = _compose_direct(
        "B",
        (
            second,
            third,
        ),
    )

    node_c = _recompose(
        "C",
        (
            node_a,
            node_b,
        ),
    )

    node_d = _recompose(
        "D",
        (node_c,),
    )

    assert {
        leaf.evidence_id
        for leaf in node_d.contributors
    } == {
        "FIRST",
        "SECOND",
        "THIRD",
    }


def test_three_level_composition_preserves_each_source():
    first = _extract(
        "FIRST",
        "crm",
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "email",
        "The customer asks what comes next.",
    )

    third = _extract(
        "THIRD",
        "support",
        "The customer wants another discussion about the proposal.",
    )

    node_a = _compose_direct(
        "A",
        (first,),
    )

    node_b = _compose_direct(
        "B",
        (
            second,
            third,
        ),
    )

    node_c = _recompose(
        "C",
        (
            node_a,
            node_b,
        ),
    )

    assert {
        leaf.source_system
        for leaf in node_c.contributors
    } == {
        "crm",
        "email",
        "support",
    }


def test_recomposition_does_not_mutate_existing_nodes():
    evidence = _extract(
        "E",
        "crm",
        "The migration workshop is complete.",
    )

    node = _compose_direct(
        "NODE",
        (evidence,),
    )

    before = node

    recomposed = _recompose(
        "ROOT",
        (node,),
    )

    assert node == before
    assert recomposed.contributors == node.contributors


def test_lineage_is_deterministic():
    first = _extract(
        "FIRST",
        "crm",
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "email",
        "The customer asks what comes next.",
    )

    node_a = _compose_direct(
        "A",
        (
            first,
            second,
        ),
    )

    node_b = _compose_direct(
        "B",
        (
            first,
            second,
        ),
    )

    first_result = _recompose(
        "ROOT",
        (
            node_a,
            node_b,
        ),
    )

    second_result = _recompose(
        "ROOT",
        (
            node_a,
            node_b,
        ),
    )

    assert first_result == second_result


def test_input_order_does_not_change_lineage_membership():
    first = _extract(
        "FIRST",
        "crm",
        "The migration workshop is complete.",
    )

    second = _extract(
        "SECOND",
        "email",
        "The customer asks what comes next.",
    )

    node_a = _compose_direct(
        "A",
        (first,),
    )

    node_b = _compose_direct(
        "B",
        (second,),
    )

    forward = _recompose(
        "ROOT",
        (
            node_a,
            node_b,
        ),
    )

    reverse = _recompose(
        "ROOT",
        (
            node_b,
            node_a,
        ),
    )

    assert set(forward.contributors) == set(
        reverse.contributors
    )


def test_lineage_does_not_create_benchmark_policy():
    evidence = _extract(
        "E",
        "crm",
        "The migration workshop is complete.",
    )

    node = _compose_direct(
        "NODE",
        (evidence,),
    )

    assert not hasattr(
        node,
        "expected_direction",
    )

    assert not hasattr(
        node,
        "benchmark_family",
    )

    assert not hasattr(
        node,
        "winner",
    )

    assert not hasattr(
        node,
        "priority",
    )