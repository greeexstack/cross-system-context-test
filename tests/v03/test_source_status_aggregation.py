from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceStatus:
    source_system: str
    availability: str
    error_class: str | None = None


@dataclass(frozen=True)
class SourceStatusSummary:
    sources: tuple[SourceStatus, ...]

    @property
    def available_sources(self) -> tuple[str, ...]:
        return tuple(
            source.source_system
            for source in self.sources
            if source.availability == "available"
        )

    @property
    def unavailable_sources(self) -> tuple[str, ...]:
        return tuple(
            source.source_system
            for source in self.sources
            if source.availability == "unavailable"
        )

    @property
    def failed_sources(self) -> tuple[str, ...]:
        return tuple(
            source.source_system
            for source in self.sources
            if source.availability == "failed"
        )

    @property
    def all_available(self) -> bool:
        return bool(self.sources) and all(
            source.availability == "available"
            for source in self.sources
        )

    @property
    def any_available(self) -> bool:
        return any(
            source.availability == "available"
            for source in self.sources
        )

    @property
    def any_failure(self) -> bool:
        return any(
            source.availability in {
                "unavailable",
                "failed",
            }
            for source in self.sources
        )


def test_single_available_source_is_reported_as_available():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="available",
            ),
        ),
    )

    assert summary.available_sources == ("crm",)
    assert summary.unavailable_sources == ()
    assert summary.failed_sources == ()

    assert summary.all_available is True
    assert summary.any_available is True
    assert summary.any_failure is False


def test_single_unavailable_source_is_reported_as_unavailable():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="email",
                availability="unavailable",
            ),
        ),
    )

    assert summary.available_sources == ()
    assert summary.unavailable_sources == ("email",)
    assert summary.failed_sources == ()

    assert summary.all_available is False
    assert summary.any_available is False
    assert summary.any_failure is True


def test_single_failed_source_is_reported_as_failed():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="billing",
                availability="failed",
                error_class="timeout",
            ),
        ),
    )

    assert summary.available_sources == ()
    assert summary.unavailable_sources == ()
    assert summary.failed_sources == ("billing",)

    assert summary.all_available is False
    assert summary.any_available is False
    assert summary.any_failure is True


def test_multiple_source_states_remain_independent():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="available",
            ),
            SourceStatus(
                source_system="email",
                availability="unavailable",
            ),
            SourceStatus(
                source_system="billing",
                availability="failed",
                error_class="timeout",
            ),
        ),
    )

    assert summary.available_sources == ("crm",)
    assert summary.unavailable_sources == ("email",)
    assert summary.failed_sources == ("billing",)


def test_one_failed_source_does_not_make_all_sources_unavailable():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="available",
            ),
            SourceStatus(
                source_system="email",
                availability="failed",
                error_class="timeout",
            ),
        ),
    )

    assert summary.any_available is True
    assert summary.any_failure is True

    assert summary.available_sources == ("crm",)
    assert summary.failed_sources == ("email",)


def test_one_unavailable_source_does_not_make_all_sources_failed():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="available",
            ),
            SourceStatus(
                source_system="email",
                availability="unavailable",
            ),
        ),
    )

    assert summary.failed_sources == ()
    assert summary.unavailable_sources == ("email",)


def test_all_available_requires_every_source_to_be_available():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="available",
            ),
            SourceStatus(
                source_system="email",
                availability="available",
            ),
        ),
    )

    assert summary.all_available is True


def test_mixed_states_are_not_all_available():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="available",
            ),
            SourceStatus(
                source_system="email",
                availability="failed",
                error_class="timeout",
            ),
        ),
    )

    assert summary.all_available is False


def test_empty_source_set_is_not_considered_all_available():
    summary = SourceStatusSummary(
        sources=(),
    )

    assert summary.all_available is False
    assert summary.any_available is False
    assert summary.any_failure is False


def test_empty_source_set_has_no_source_classifications():
    summary = SourceStatusSummary(
        sources=(),
    )

    assert summary.available_sources == ()
    assert summary.unavailable_sources == ()
    assert summary.failed_sources == ()


def test_error_class_is_retained_for_failed_sources():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="email",
                availability="failed",
                error_class="timeout",
            ),
        ),
    )

    assert summary.sources[0].error_class == "timeout"


def test_different_failures_remain_distinguishable():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="email",
                availability="failed",
                error_class="timeout",
            ),
            SourceStatus(
                source_system="billing",
                availability="failed",
                error_class="authentication",
            ),
        ),
    )

    assert {
        source.error_class
        for source in summary.sources
    } == {
        "timeout",
        "authentication",
    }


def test_source_status_does_not_erase_source_identity():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="available",
            ),
            SourceStatus(
                source_system="email",
                availability="unavailable",
            ),
        ),
    )

    assert {
        source.source_system
        for source in summary.sources
    } == {
        "crm",
        "email",
    }


def test_source_status_is_deterministic():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="available",
            ),
            SourceStatus(
                source_system="email",
                availability="failed",
                error_class="timeout",
            ),
        ),
    )

    assert summary == summary


def test_repeated_construction_produces_same_summary():
    sources = (
        SourceStatus(
            source_system="crm",
            availability="available",
        ),
        SourceStatus(
            source_system="email",
            availability="unavailable",
        ),
    )

    first = SourceStatusSummary(
        sources=sources,
    )

    second = SourceStatusSummary(
        sources=sources,
    )

    assert first == second


def test_input_order_does_not_change_classification_sets():
    crm = SourceStatus(
        source_system="crm",
        availability="available",
    )

    email = SourceStatus(
        source_system="email",
        availability="unavailable",
    )

    first = SourceStatusSummary(
        sources=(crm, email),
    )

    second = SourceStatusSummary(
        sources=(email, crm),
    )

    assert set(first.available_sources) == set(
        second.available_sources
    )

    assert set(first.unavailable_sources) == set(
        second.unavailable_sources
    )

    assert set(first.failed_sources) == set(
        second.failed_sources
    )


def test_source_failure_is_not_a_semantic_fact():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="email",
                availability="failed",
                error_class="timeout",
            ),
        ),
    )

    assert not hasattr(
        summary,
        "confirms_completion",
    )

    assert not hasattr(
        summary,
        "requests_followup",
    )

    assert not hasattr(
        summary,
        "winner",
    )


def test_source_status_has_no_source_priority():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="available",
            ),
            SourceStatus(
                source_system="email",
                availability="failed",
                error_class="timeout",
            ),
        ),
    )

    assert not hasattr(summary, "source_priority")
    assert not hasattr(summary, "recency_priority")
    assert not hasattr(summary, "winner")


def test_source_status_has_no_benchmark_policy():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="available",
            ),
        ),
    )

    assert not hasattr(summary, "expected_direction")
    assert not hasattr(summary, "benchmark_family")


def test_source_status_can_represent_multiple_failure_classes():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="failed",
                error_class="timeout",
            ),
            SourceStatus(
                source_system="email",
                availability="failed",
                error_class="authorization",
            ),
            SourceStatus(
                source_system="billing",
                availability="unavailable",
            ),
        ),
    )

    assert summary.available_sources == ()
    assert set(summary.failed_sources) == {
        "crm",
        "email",
    }
    assert summary.unavailable_sources == (
        "billing",
    )


def test_source_status_does_not_treat_unavailable_as_empty_success():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="email",
                availability="unavailable",
            ),
        ),
    )

    assert summary.any_available is False
    assert summary.any_failure is True
    assert summary.available_sources == ()


def test_partial_success_is_explicit():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="available",
            ),
            SourceStatus(
                source_system="email",
                availability="failed",
                error_class="timeout",
            ),
        ),
    )

    assert summary.any_available is True
    assert summary.any_failure is True
    assert summary.all_available is False


def test_source_status_does_not_mutate_individual_source_records():
    source = SourceStatus(
        source_system="crm",
        availability="available",
    )

    summary = SourceStatusSummary(
        sources=(source,),
    )

    assert summary.sources[0] == source


def test_source_status_retains_failure_reason_only_when_present():
    failed = SourceStatus(
        source_system="email",
        availability="failed",
        error_class="timeout",
    )

    available = SourceStatus(
        source_system="crm",
        availability="available",
    )

    assert failed.error_class == "timeout"
    assert available.error_class is None


def test_availability_summary_is_not_a_reasoning_result():
    summary = SourceStatusSummary(
        sources=(
            SourceStatus(
                source_system="crm",
                availability="available",
            ),
            SourceStatus(
                source_system="email",
                availability="failed",
                error_class="timeout",
            ),
        ),
    )

    assert summary.any_available is True
    assert summary.any_failure is True

    assert not hasattr(
        summary,
        "interpretation_class",
    )

    assert not hasattr(
        summary,
        "decision_strength",
    )