from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from .v02.runner import V02Runner


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_ROOT = REPO_ROOT / "fixtures_package"


def _resolve_fixture_root(value: str | None) -> Path:
    return (
        Path(value).expanduser().resolve()
        if value
        else DEFAULT_FIXTURE_ROOT
    )


def validate_fixtures(fixture_root: Path) -> int:
    validator = fixture_root / "validate_fixtures.py"

    if not validator.is_file():
        print(
            f"ERROR: fixture validator not found: {validator}",
            file=sys.stderr,
        )
        return 2

    completed = subprocess.run(
        [sys.executable, str(validator)],
        cwd=str(fixture_root),
        check=False,
    )
    return completed.returncode


def run_experiment(fixture_root: Path) -> int:
    try:
        runner = V02Runner(fixture_root)
        results = runner.run_all()
    except Exception as exc:
        print(f"ERROR: experiment execution failed: {exc}", file=sys.stderr)
        return 2

    passed = sum(result.passed for result in results)

    print("=" * 78)
    print("CROSS-SYSTEM CONTEXT REASONING & ROBUSTNESS EXPERIMENT — v0.2")
    print("=" * 78)

    for result in results:
        print(
            f"{result.pair_id:<8} "
            f"{result.split:<11} "
            f"{'PASS' if result.passed else 'FAIL'}"
        )

    print("-" * 78)
    print(f"Passed cases: {passed}/{len(results)}")

    all_passed = bool(results) and passed == len(results)
    print(f"Result: {'PASS' if all_passed else 'FAIL'}")

    return 0 if all_passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cross-system-context",
        description=(
            "Run the controlled Cross-System Context v0.2 experiment."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="validate the fixture package invariants",
    )
    validate_parser.add_argument(
        "--fixtures",
        default=None,
        help="fixture package directory (default: repository fixtures_package)",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="run the frozen v0.2 experiment",
    )
    run_parser.add_argument(
        "--fixtures",
        default=None,
        help="fixture package directory (default: repository fixtures_package)",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    fixture_root = _resolve_fixture_root(args.fixtures)

    if args.command == "validate":
        return validate_fixtures(fixture_root)

    if args.command == "run":
        return run_experiment(fixture_root)

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
