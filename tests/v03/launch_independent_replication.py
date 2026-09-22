from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify provenance, then launch independent replication."
    )
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--attestation", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]

    verifier = root / "tests" / "v03" / "verify_independent_replication.py"
    runner = root / "tests" / "v03" / "run_independent_replication.py"

    verify_cmd = [
        sys.executable,
        str(verifier),
        "--fixture",
        args.fixture,
        "--attestation",
        args.attestation,
    ]

    verify = subprocess.run(verify_cmd)

    if verify.returncode != 0:
        print("REPLICATION BLOCKED: provenance verification failed.")
        return verify.returncode

    run_cmd = [
        sys.executable,
        str(runner),
        "--fixture",
        args.fixture,
        "--json-out",
        args.json_out,
    ]

    run = subprocess.run(run_cmd)

    if run.returncode == 0:
        print("REPLICATION COMPLETED.")
    else:
        print("REPLICATION FAILED DURING EVALUATION.")

    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())