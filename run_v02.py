from __future__ import annotations

import json
from pathlib import Path

from experiment.v02.runner import V02Runner


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures_package"


def main() -> None:
    runner = V02Runner(FIXTURES)
    results = runner.run_all()
    passed = sum(result.passed for result in results)
    print("=" * 78)
    print("CROSS-SYSTEM CONTEXT REASONING & ROBUSTNESS EXPERIMENT — v0.2")
    print("=" * 78)
    for result in results:
        print(f"{result.pair_id:<8} {result.split:<11} {'PASS' if result.passed else 'FAIL'}")
    print("-" * 78)
    print(f"Passed cases: {passed}/{len(results)}")
    print(f"Result: {'PASS' if passed == len(results) else 'FAIL'}")


if __name__ == "__main__":
    main()
