from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Leaf:
    evidence_id: str
    source_system: str
    occurred_at: datetime


@dataclass(frozen=True)
class CompositionNode:
    node_id: str
    contributors: tuple[Leaf, ...]
    parent_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CycleCheck:
    valid: bool
    visited_nodes: tuple[str, ...]


def _leaf(
    evidence_id: str,
    source_system: str = "secondary",
    occurred_at: str = "2026-09-12T10:00:00Z",
) -> Leaf:
    return Leaf(
        evidence_id=evidence_id,
        source_system=source_system,
        occurred_at=datetime.fromisoformat(
            occurred_at.replace("Z", "+00:00")
        ),
    )


def _check_acyclic(
    root_id: str,
    graph: dict[str, CompositionNode],
) -> CycleCheck:
    visiting: set[str] = set()
    visited: set[str] = set()
    order: list[str] = []

    def visit(node_id: str) -> bool:
        if node_id in visiting:
            return False

        if node_id in visited:
            return True

        node = graph.get(node_id)

        if node is None:
            return True

        visiting.add(node_id)
        order.append(node_id)

        for parent_id in node.parent_ids:
            if not visit(parent_id):
                return False

        visiting.remove(node_id)
        visited.add(node_id)

        return True

    valid = visit(root_id)

    return CycleCheck(
        valid=valid,
        visited_nodes=tuple(order),
    )


def _flatten_lineage(
    root_id: str,
    graph: dict[str, CompositionNode],
) -> tuple[Leaf, ...]:
    leaves: list[Leaf] = []
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visited:
            return

        visited.add(node_id)

        node = graph.get(node_id)

        if node is None:
            return

        leaves.extend(node.contributors)

        for parent_id in node.parent_ids:
            visit(parent_id)

    visit(root_id)

    unique: dict[tuple, Leaf] = {}

    for leaf in leaves:
        unique.setdefault(
            (
                leaf.evidence_id,
                leaf.source_system,
                leaf.occurred_at,
            ),
            leaf,
        )

    return tuple(unique.values())


def test_single_node_without_parents_is_acyclic():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("E1"),
            ),
        ),
    }

    result = _check_acyclic(
        "A",
        graph,
    )

    assert result.valid is True
    assert result.visited_nodes == ("A",)


def test_linear_composition_is_acyclic():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("E1"),
            ),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                _leaf("E2"),
            ),
            parent_ids=("A",),
        ),
        "C": CompositionNode(
            node_id="C",
            contributors=(
                _leaf("E3"),
            ),
            parent_ids=("B",),
        ),
    }

    result = _check_acyclic(
        "C",
        graph,
    )

    assert result.valid is True


def test_direct_self_cycle_is_rejected():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("E1"),
            ),
            parent_ids=("A",),
        ),
    }

    result = _check_acyclic(
        "A",
        graph,
    )

    assert result.valid is False


def test_two_node_cycle_is_rejected():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("E1"),
            ),
            parent_ids=("B",),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                _leaf("E2"),
            ),
            parent_ids=("A",),
        ),
    }

    result = _check_acyclic(
        "A",
        graph,
    )

    assert result.valid is False


def test_three_node_cycle_is_rejected():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("E1"),
            ),
            parent_ids=("B",),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                _leaf("E2"),
            ),
            parent_ids=("C",),
        ),
        "C": CompositionNode(
            node_id="C",
            contributors=(
                _leaf("E3"),
            ),
            parent_ids=("A",),
        ),
    }

    result = _check_acyclic(
        "A",
        graph,
    )

    assert result.valid is False


def test_cycle_detection_does_not_depend_on_contributor_count():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(),
            parent_ids=("A",),
        ),
    }

    result = _check_acyclic(
        "A",
        graph,
    )

    assert result.valid is False


def test_shared_parent_is_not_a_cycle():
    graph = {
        "ROOT": CompositionNode(
            node_id="ROOT",
            contributors=(
                _leaf("ROOT-E"),
            ),
            parent_ids=("A", "B"),
        ),
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("A-E"),
            ),
            parent_ids=("BASE",),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                _leaf("B-E"),
            ),
            parent_ids=("BASE",),
        ),
        "BASE": CompositionNode(
            node_id="BASE",
            contributors=(
                _leaf("BASE-E"),
            ),
        ),
    }

    result = _check_acyclic(
        "ROOT",
        graph,
    )

    assert result.valid is True


def test_diamond_graph_is_acyclic():
    graph = {
        "ROOT": CompositionNode(
            node_id="ROOT",
            contributors=(
                _leaf("ROOT"),
            ),
            parent_ids=("LEFT", "RIGHT"),
        ),
        "LEFT": CompositionNode(
            node_id="LEFT",
            contributors=(
                _leaf("LEFT"),
            ),
            parent_ids=("BASE",),
        ),
        "RIGHT": CompositionNode(
            node_id="RIGHT",
            contributors=(
                _leaf("RIGHT"),
            ),
            parent_ids=("BASE",),
        ),
        "BASE": CompositionNode(
            node_id="BASE",
            contributors=(
                _leaf("BASE"),
            ),
        ),
    }

    result = _check_acyclic(
        "ROOT",
        graph,
    )

    assert result.valid is True


def test_diamond_lineage_deduplicates_shared_leaf():
    graph = {
        "ROOT": CompositionNode(
            node_id="ROOT",
            contributors=(
                _leaf("ROOT"),
            ),
            parent_ids=("LEFT", "RIGHT"),
        ),
        "LEFT": CompositionNode(
            node_id="LEFT",
            contributors=(
                _leaf("LEFT"),
                _leaf("SHARED"),
            ),
            parent_ids=("BASE",),
        ),
        "RIGHT": CompositionNode(
            node_id="RIGHT",
            contributors=(
                _leaf("RIGHT"),
                _leaf("SHARED"),
            ),
            parent_ids=("BASE",),
        ),
        "BASE": CompositionNode(
            node_id="BASE",
            contributors=(
                _leaf("BASE"),
            ),
        ),
    }

    leaves = _flatten_lineage(
        "ROOT",
        graph,
    )

    assert {
        leaf.evidence_id
        for leaf in leaves
    } == {
        "ROOT",
        "LEFT",
        "RIGHT",
        "SHARED",
        "BASE",
    }


def test_repeated_parent_reference_does_not_duplicate_lineage():
    graph = {
        "ROOT": CompositionNode(
            node_id="ROOT",
            contributors=(
                _leaf("ROOT"),
            ),
            parent_ids=("A", "A", "A"),
        ),
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("A"),
            ),
        ),
    }

    leaves = _flatten_lineage(
        "ROOT",
        graph,
    )

    assert [
        leaf.evidence_id
        for leaf in leaves
    ] == [
        "ROOT",
        "A",
    ]


def test_cycle_check_is_deterministic():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("E1"),
            ),
            parent_ids=("B",),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                _leaf("E2"),
            ),
            parent_ids=("A",),
        ),
    }

    first = _check_acyclic(
        "A",
        graph,
    )

    second = _check_acyclic(
        "A",
        graph,
    )

    assert first == second


def test_cycle_check_reports_encountered_nodes_before_failure():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("A"),
            ),
            parent_ids=("B",),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                _leaf("B"),
            ),
            parent_ids=("A",),
        ),
    }

    result = _check_acyclic(
        "A",
        graph,
    )

    assert result.valid is False
    assert result.visited_nodes == (
        "A",
        "B",
    )


def test_missing_parent_is_not_treated_as_cycle():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("A"),
            ),
            parent_ids=("MISSING",),
        ),
    }

    result = _check_acyclic(
        "A",
        graph,
    )

    assert result.valid is True


def test_missing_parent_does_not_create_fake_lineage():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("A"),
            ),
            parent_ids=("MISSING",),
        ),
    }

    leaves = _flatten_lineage(
        "A",
        graph,
    )

    assert [
        leaf.evidence_id
        for leaf in leaves
    ] == ["A"]


def test_cycle_check_is_independent_of_leaf_semantics():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf(
                    "E1",
                    source_system="crm",
                ),
            ),
            parent_ids=("A",),
        ),
    }

    result = _check_acyclic(
        "A",
        graph,
    )

    assert result.valid is False


def test_source_metadata_does_not_break_cycle_detection():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf(
                    "E1",
                    source_system="crm",
                ),
            ),
            parent_ids=("B",),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                _leaf(
                    "E2",
                    source_system="email",
                ),
            ),
            parent_ids=("A",),
        ),
    }

    result = _check_acyclic(
        "A",
        graph,
    )

    assert result.valid is False


def test_event_time_does_not_break_cycle_detection():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf(
                    "E1",
                    occurred_at="2026-09-10T10:00:00Z",
                ),
            ),
            parent_ids=("B",),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                _leaf(
                    "E2",
                    occurred_at="2026-09-12T10:00:00Z",
                ),
            ),
            parent_ids=("A",),
        ),
    }

    result = _check_acyclic(
        "A",
        graph,
    )

    assert result.valid is False


def test_lineage_flattening_terminates_on_cycle():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("A"),
            ),
            parent_ids=("B",),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                _leaf("B"),
            ),
            parent_ids=("A",),
        ),
    }

    leaves = _flatten_lineage(
        "A",
        graph,
    )

    assert {
        leaf.evidence_id
        for leaf in leaves
    } == {
        "A",
        "B",
    }


def test_nested_cycle_does_not_duplicate_leaves_indefinitely():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("A"),
            ),
            parent_ids=("B",),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                _leaf("B"),
            ),
            parent_ids=("C",),
        ),
        "C": CompositionNode(
            node_id="C",
            contributors=(
                _leaf("C"),
            ),
            parent_ids=("B",),
        ),
    }

    leaves = _flatten_lineage(
        "A",
        graph,
    )

    assert {
        leaf.evidence_id
        for leaf in leaves
    } == {
        "A",
        "B",
        "C",
    }


def test_acyclic_lineage_preserves_all_expected_leaves():
    graph = {
        "ROOT": CompositionNode(
            node_id="ROOT",
            contributors=(
                _leaf("ROOT"),
            ),
            parent_ids=("A", "B"),
        ),
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("A"),
            ),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                _leaf("B"),
            ),
        ),
    }

    leaves = _flatten_lineage(
        "ROOT",
        graph,
    )

    assert {
        leaf.evidence_id
        for leaf in leaves
    } == {
        "ROOT",
        "A",
        "B",
    }


def test_lineage_leaf_identity_is_complete():
    leaf = _leaf(
        "E1",
        source_system="crm",
        occurred_at="2026-09-12T10:00:00Z",
    )

    assert leaf.evidence_id == "E1"
    assert leaf.source_system == "crm"

    assert leaf.occurred_at == datetime(
        2026,
        9,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )


def test_cycle_safety_has_no_winner_or_priority_policy():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("A"),
            ),
            parent_ids=("A",),
        ),
    }

    result = _check_acyclic(
        "A",
        graph,
    )

    assert not hasattr(
        result,
        "winner",
    )

    assert not hasattr(
        result,
        "priority",
    )

    assert not hasattr(
        result,
        "source_priority",
    )


def test_cycle_safety_has_no_benchmark_policy():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("A"),
            ),
            parent_ids=("A",),
        ),
    }

    result = _check_acyclic(
        "A",
        graph,
    )

    assert not hasattr(
        result,
        "expected_direction",
    )

    assert not hasattr(
        result,
        "benchmark_family",
    )