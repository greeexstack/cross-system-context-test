from __future__ import annotations

import argparse
import json
from pathlib import Path

from test_independent_replication_loader import load_suite


REQUIRED_ATTESTATION = {
    "author_accessed_candidate_results": False,
    "author_accessed_prior_holdout_texts": False,
    "author_copied_prior_holdout": False,
    "author_used_candidate_failure_diagnostics": False,
    "oracle_fixed_before_candidate_evaluation": True,
    "fixture_modified_after_evaluation": False,
}


def verify_attestation(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))

    if data.get("fixture_status") != "independent_verified":
        raise ValueError(
            "fixture_status must be 'independent_verified'"
        )

    for field, expected in REQUIRED_ATTESTATION.items():
        if data.get(field) is not expected:
            raise ValueError(
                f"attestation field {field!r} must be {expected!r}"
            )

    statement = data.get("author_attestation")
    if not isinstance(statement, str) or not statement.strip():
        raise ValueError("author_attestation must be non-empty")

    if "Pending" in statement or "pending" in statement:
        raise ValueError("author_attestation is still pending")


def verify_inputs(
    fixture_path: Path,
    attestation_path: Path,
) -> None:
    if not fixture_path.is_file():
        raise FileNotFoundError(
            f"fixture not found: {fixture_path}"
        )

    if not attestation_path.is_file():
        raise FileNotFoundError(
            f"attestation not found: {attestation_path}"
        )

    verify_attestation(attestation_path)

    cases = load_suite(str(fixture_path))

    print(
        {
            "provenance": "independent_verified",
            "cases": len(cases),
            "variants": sum(len(case.texts) for case in cases),
            "candidate_evaluation": False,
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify independent replication inputs without evaluation."
    )
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--attestation", required=True)
    args = parser.parse_args()

    verify_inputs(
        Path(args.fixture),
        Path(args.attestation),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())