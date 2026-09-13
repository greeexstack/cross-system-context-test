from pathlib import Path

from experiment.v02.runner import V02Runner


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures_package"


def test_all_frozen_cases_pass() -> None:
    results = V02Runner(FIXTURE_ROOT).run_all()
    assert len(results) == 20
    assert all(result.passed for result in results)


def test_development_and_evaluation_are_not_substantive_duplicates() -> None:
    runner = V02Runner(FIXTURE_ROOT)
    seen = {}
    for case in runner.scenarios:
        key = case["family_id"]
        substantive = {k: v for k, v in case.items() if k not in {"pair_id", "split"}}
        seen.setdefault(key, {})[case["split"]] = substantive
    for family_id, parts in seen.items():
        assert parts["development"] != parts["evaluation"], family_id


def test_identity_and_missing_data_safety() -> None:
    results = {r.pair_id: r for r in V02Runner(FIXTURE_ROOT).run_all()}
    assert results["F05-D1"].identity_integrity
    assert results["F05-E1"].identity_integrity
    assert results["F06-D1"].ambiguity_handling
    assert results["F06-E1"].ambiguity_handling
    assert results["F08-D1"].missing_data_handling
    assert results["F08-E1"].missing_data_handling


def test_temporal_and_reversion_safety() -> None:
    results = {r.pair_id: r for r in V02Runner(FIXTURE_ROOT).run_all()}
    assert results["F07-D1"].temporal_integrity
    assert results["F07-E1"].temporal_integrity
    assert results["F09-D1"].context_resistance
    assert results["F09-E1"].context_resistance
