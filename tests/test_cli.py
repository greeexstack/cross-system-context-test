from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT_ROOT / "fixtures_package"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "experiment.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def copy_fixtures(tmp_path: Path) -> Path:
    destination = tmp_path / "fixtures_package"
    shutil.copytree(FIXTURES, destination)
    return destination


def test_validate_default_fixtures_passes() -> None:
    result = run_cli("validate")

    assert result.returncode == 0
    assert "VALIDATION PASS" in result.stdout


def test_run_default_v02_passes() -> None:
    result = run_cli("run")

    assert result.returncode == 0
    assert "Passed cases: 20/20" in result.stdout
    assert "Result: PASS" in result.stdout


def test_validate_returns_nonzero_for_invalid_fixture_package(
    tmp_path: Path,
) -> None:
    fixture_root = copy_fixtures(tmp_path)
    (fixture_root / "fixtures" / "quotes.json").unlink()

    result = run_cli(
        "validate",
        "--fixtures",
        str(fixture_root),
    )

    assert result.returncode != 0
    assert "VALIDATION FAIL" in result.stdout


def test_run_returns_nonzero_for_unusable_fixture_package(
    tmp_path: Path,
) -> None:
    fixture_root = copy_fixtures(tmp_path)
    (fixture_root / "fixtures" / "customers.json").unlink()

    result = run_cli(
        "run",
        "--fixtures",
        str(fixture_root),
    )

    assert result.returncode != 0
    assert "ERROR: experiment execution failed" in result.stderr
