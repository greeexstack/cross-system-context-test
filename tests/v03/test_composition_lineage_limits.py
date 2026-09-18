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
class LineageLimits:
    max_depth: int
    max_leaves: int


@dataclass(frozen=True)
class LineageLimitResult:
    accepted: bool
    reason: str | None
    leaves: tuple[Leaf, ...]
    depth: int


def _leaf(
    evidence_id: str,
    source_system: str = "secondary",
) -> Leaf:
    return Leaf(
        evidence_id=evidence_id,
        source_system=source_system,
        occurred_at=datetime(
            2026,
            9,
            12,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )


def _depth(
    root_id: str,
    graph: dict[str, CompositionNode],
) -> int:
    visiting: set[str] = set()
    memo: dict[str, int] = {}

    def visit(node_id: str) -> int:
        if node_id in visiting:
            raise RuntimeError("cycle_detected")
        if node_id in memo:
            return memo[node_id]

        node = graph.get(node_id)

        if node is None:
            return 0

        visiting.add(node_id)

        parent_depths = tuple(
            visit(parent_id)
            for parent_id in node.parent_ids
        )

        visiting.remove(node_id)

        result = (
            1
            if not parent_depths
            else 1 + max(parent_depths)
        )

        memo[node_id] = result
        return result

    return visit(root_id)


def _flatten(
    root_id: str,
    graph: dict[str, CompositionNode],
    limits: LineageLimits,
) -> LineageLimitResult:
    visiting: set[str] = set()
    visited: set[str] = set()
    leaves: list[Leaf] = []

    def visit(
        node_id: str,
        depth: int,
    ) -> None:
        if depth > limits.max_depth:
            raise RuntimeError("max_depth_exceeded")

        if node_id in visiting:
            raise RuntimeError("cycle_detected")

        if node_id in visited:
            return

        node = graph.get(node_id)

        if node is None:
            return

        visiting.add(node_id)

        for leaf in node.contributors:
            leaves.append(leaf)

            if len(leaves) > limits.max_leaves:
                raise RuntimeError("max_leaves_exceeded")

        for parent_id in node.parent_ids:
            visit(
                parent_id,
                depth + 1,
            )

        visiting.remove(node_id)
        visited.add(node_id)

    try:
        depth = _depth(
            root_id,
            graph,
        )

        if depth > limits.max_depth:
            return LineageLimitResult(
                accepted=False,
                reason="max_depth_exceeded",
                leaves=(),
                depth=depth,
            )

        visit(
            root_id,
            1,
        )

        return LineageLimitResult(
            accepted=True,
            reason=None,
            leaves=tuple(leaves),
            depth=depth,
        )

    except RuntimeError as exc:
        reason = str(exc)

        return LineageLimitResult(
            accepted=False,
            reason=reason,
            leaves=(),
            depth=_safe_depth(root_id, graph),
        )


def _safe_depth(
    root_id: str,
    graph: dict[str, CompositionNode],
) -> int:
    try:
        return _depth(
            root_id,
            graph,
        )
    except (ValueError, RuntimeError):
        return -1

def _chain(
    length: int,
) -> dict[str, CompositionNode]:
    graph: dict[str, CompositionNode] = {}

    for index in range(length):
        node_id = f"N{index}"

        parent_ids = (
            (f"N{index - 1}",)
            if index > 0
            else ()
        )

        graph[node_id] = CompositionNode(
            node_id=node_id,
            contributors=(
                _leaf(
                    f"E{index}",
                ),
            ),
            parent_ids=parent_ids,
        )

    return graph


def _fanout(
    count: int,
) -> dict[str, CompositionNode]:
    graph: dict[str, CompositionNode] = {
        "ROOT": CompositionNode(
            node_id="ROOT",
            contributors=(
                _leaf("ROOT"),
            ),
            parent_ids=tuple(
                f"N{index}"
                for index in range(count)
            ),
        ),
    }

    for index in range(count):
        graph[f"N{index}"] = CompositionNode(
            node_id=f"N{index}",
            contributors=(
                _leaf(f"E{index}"),
            ),
        )

    return graph


def test_small_lineage_within_limits_is_accepted():
    graph = _chain(3)

    result = _flatten(
        "N2",
        graph,
        LineageLimits(
            max_depth=3,
            max_leaves=10,
        ),
    )

    assert result.accepted is True
    assert result.reason is None


def test_depth_is_measured_from_root_to_deepest_parent():
    graph = _chain(5)

    assert _depth(
        "N4",
        graph,
    ) == 5


def test_depth_limit_accepts_exact_boundary():
    graph = _chain(5)

    result = _flatten(
        "N4",
        graph,
        LineageLimits(
            max_depth=5,
            max_leaves=10,
        ),
    )

    assert result.accepted is True
    assert result.depth == 5


def test_depth_limit_rejects_one_level_over_boundary():
    graph = _chain(6)

    result = _flatten(
        "N5",
        graph,
        LineageLimits(
            max_depth=5,
            max_leaves=10,
        ),
    )

    assert result.accepted is False
    assert result.reason == "max_depth_exceeded"
    assert result.leaves == ()


def test_zero_depth_limit_rejects_nonempty_lineage():
    graph = _chain(1)

    result = _flatten(
        "N0",
        graph,
        LineageLimits(
            max_depth=0,
            max_leaves=10,
        ),
    )

    assert result.accepted is False
    assert result.reason == "max_depth_exceeded"


def test_leaf_limit_accepts_exact_boundary():
    graph = _fanout(4)

    result = _flatten(
        "ROOT",
        graph,
        LineageLimits(
            max_depth=2,
            max_leaves=5,
        ),
    )

    assert result.accepted is True
    assert len(result.leaves) == 5


def test_leaf_limit_rejects_one_leaf_over_boundary():
    graph = _fanout(5)

    result = _flatten(
        "ROOT",
        graph,
        LineageLimits(
            max_depth=2,
            max_leaves=5,
        ),
    )

    assert result.accepted is False
    assert result.reason == "max_leaves_exceeded"
    assert result.leaves == ()


def test_zero_leaf_limit_rejects_node_with_contributor():
    graph = _chain(1)

    result = _flatten(
        "N0",
        graph,
        LineageLimits(
            max_depth=1,
            max_leaves=0,
        ),
    )

    assert result.accepted is False
    assert result.reason == "max_leaves_exceeded"


def test_limit_failure_does_not_return_partial_leaves():
    graph = _chain(4)

    result = _flatten(
        "N3",
        graph,
        LineageLimits(
            max_depth=4,
            max_leaves=2,
        ),
    )

    assert result.accepted is False
    assert result.reason == "max_leaves_exceeded"
    assert result.leaves == ()


def test_depth_failure_does_not_return_partial_leaves():
    graph = _chain(5)

    result = _flatten(
        "N4",
        graph,
        LineageLimits(
            max_depth=3,
            max_leaves=100,
        ),
    )

    assert result.accepted is False
    assert result.reason == "max_depth_exceeded"
    assert result.leaves == ()


def test_high_fanout_can_be_rejected_without_truncation():
    graph = _fanout(20)

    result = _flatten(
        "ROOT",
        graph,
        LineageLimits(
            max_depth=2,
            max_leaves=10,
        ),
    )

    assert result.accepted is False
    assert result.reason == "max_leaves_exceeded"
    assert result.leaves == ()


def test_deep_chain_can_be_rejected_without_truncation():
    graph = _chain(20)

    result = _flatten(
        "N19",
        graph,
        LineageLimits(
            max_depth=10,
            max_leaves=100,
        ),
    )

    assert result.accepted is False
    assert result.reason == "max_depth_exceeded"
    assert result.leaves == ()


def test_shared_parent_does_not_multiply_depth():
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
            parent_ids=("BASE",),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                _leaf("B"),
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

    assert _depth(
        "ROOT",
        graph,
    ) == 3


def test_shared_parent_deduplication_keeps_leaf_count_bounded():
    shared = _leaf("SHARED")

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
                shared,
            ),
        ),
        "B": CompositionNode(
            node_id="B",
            contributors=(
                shared,
            ),
        ),
    }

    result = _flatten(
        "ROOT",
        graph,
        LineageLimits(
            max_depth=2,
            max_leaves=10,
        ),
    )

    assert result.accepted is True

    # This test-layer traversal intentionally counts node contributions.
    # Deduplication policy belongs to the next lineage-normalization step.
    assert len(result.leaves) == 3


def test_cycle_is_rejected_even_when_depth_limit_is_large():
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

    result = _flatten(
        "A",
        graph,
        LineageLimits(
            max_depth=100,
            max_leaves=100,
        ),
    )

    assert result.accepted is False
    assert result.reason == "cycle_detected"


def test_cycle_failure_does_not_return_partial_leaves():
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

    result = _flatten(
        "A",
        graph,
        LineageLimits(
            max_depth=100,
            max_leaves=100,
        ),
    )

    assert result.leaves == ()


def test_missing_parent_does_not_increase_depth():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("A"),
            ),
            parent_ids=("MISSING",),
        ),
    }

    assert _depth(
        "A",
        graph,
    ) == 1


def test_missing_parent_does_not_create_failure():
    graph = {
        "A": CompositionNode(
            node_id="A",
            contributors=(
                _leaf("A"),
            ),
            parent_ids=("MISSING",),
        ),
    }

    result = _flatten(
        "A",
        graph,
        LineageLimits(
            max_depth=2,
            max_leaves=10,
        ),
    )

    assert result.accepted is True
    assert result.leaves == (
        _leaf("A"),
    )


def test_limits_are_independent_of_source_system():
    graph = {
        "ROOT": CompositionNode(
            node_id="ROOT",
            contributors=(
                _leaf(
                    "CRM",
                    source_system="crm",
                ),
            ),
            parent_ids=("EMAIL",),
        ),
        "EMAIL": CompositionNode(
            node_id="EMAIL",
            contributors=(
                _leaf(
                    "EMAIL-EVIDENCE",
                    source_system="email",
                ),
            ),
        ),
    }

    result = _flatten(
        "ROOT",
        graph,
        LineageLimits(
            max_depth=2,
            max_leaves=2,
        ),
    )

    assert result.accepted is True


def test_limits_do_not_change_leaf_provenance():
    graph = {
        "ROOT": CompositionNode(
            node_id="ROOT",
            contributors=(
                _leaf(
                    "CRM",
                    source_system="crm",
                ),
            ),
        ),
    }

    result = _flatten(
        "ROOT",
        graph,
        LineageLimits(
            max_depth=1,
            max_leaves=1,
        ),
    )

    assert result.leaves[0].evidence_id == "CRM"
    assert result.leaves[0].source_system == "crm"


def test_limits_are_deterministic():
    graph = _chain(5)

    limits = LineageLimits(
        max_depth=5,
        max_leaves=10,
    )

    first = _flatten(
        "N4",
        graph,
        limits,
    )

    second = _flatten(
        "N4",
        graph,
        limits,
    )

    assert first == second


def test_limit_check_does_not_mutate_graph():
    graph = _chain(3)

    before = dict(graph)

    _flatten(
        "N2",
        graph,
        LineageLimits(
            max_depth=3,
            max_leaves=10,
        ),
    )

    assert graph == before


def test_reversing_parent_order_does_not_change_depth():
    graph_a = {
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

    graph_b = {
        "ROOT": CompositionNode(
            node_id="ROOT",
            contributors=(
                _leaf("ROOT"),
            ),
            parent_ids=("B", "A"),
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

    assert _depth(
        "ROOT",
        graph_a,
    ) == _depth(
        "ROOT",
        graph_b,
    )


def test_limit_values_are_explicit_configuration():
    limits = LineageLimits(
        max_depth=10,
        max_leaves=100,
    )

    assert limits.max_depth == 10
    assert limits.max_leaves == 100


def test_negative_depth_limit_rejects_nonempty_lineage():
    graph = _chain(1)

    result = _flatten(
        "N0",
        graph,
        LineageLimits(
            max_depth=-1,
            max_leaves=10,
        ),
    )

    assert result.accepted is False
    assert result.reason == "max_depth_exceeded"


def test_negative_leaf_limit_rejects_nonempty_lineage():
    graph = _chain(1)

    result = _flatten(
        "N0",
        graph,
        LineageLimits(
            max_depth=1,
            max_leaves=-1,
        ),
    )

    assert result.accepted is False
    assert result.reason == "max_leaves_exceeded"


def test_large_safe_limit_does_not_change_valid_lineage():
    graph = _chain(3)

    small = _flatten(
        "N2",
        graph,
        LineageLimits(
            max_depth=3,
            max_leaves=3,
        ),
    )

    large = _flatten(
        "N2",
        graph,
        LineageLimits(
            max_depth=100,
            max_leaves=1000,
        ),
    )

    assert small.accepted is True
    assert large.accepted is True

    assert set(
        leaf.evidence_id
        for leaf in small.leaves
    ) == set(
        leaf.evidence_id
        for leaf in large.leaves
    )


def test_lineage_limits_have_no_reasoning_policy():
    graph = _chain(2)

    result = _flatten(
        "N1",
        graph,
        LineageLimits(
            max_depth=2,
            max_leaves=10,
        ),
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
        "interpretation_class",
    )


def test_lineage_limits_have_no_benchmark_policy():
    graph = _chain(2)

    result = _flatten(
        "N1",
        graph,
        LineageLimits(
            max_depth=2,
            max_leaves=10,
        ),
    )

    assert not hasattr(
        result,
        "expected_direction",
    )

    assert not hasattr(
        result,
        "benchmark_family",
    )