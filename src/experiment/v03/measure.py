from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .battery import EVALUATION_AT, build_f10_case, build_v03_battery
from .reasoner import ReasonerConfig, V03Reasoner
from .report import build_experiment_report
from .runner import V03TransitionRunner


DEFAULT_OUTPUT = Path("artifacts") / "v03_measurement.json"


def run_v03_measurement():
    reasoner = V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    )

    runner = V03TransitionRunner(reasoner)

    cases = (
        *build_v03_battery(),
        build_f10_case(),
    )

    summary = runner.run(cases)

    return build_experiment_report(summary)


def report_as_dict() -> dict:
    return asdict(run_v03_measurement())


def report_as_json() -> str:
    return json.dumps(
        report_as_dict(),
        indent=2,
        sort_keys=True,
    )


def write_report(
    output_path: str | Path = DEFAULT_OUTPUT,
) -> Path:
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        report_as_json() + "\n",
        encoding="utf-8",
    )

    return path


if __name__ == "__main__":
    output = write_report()
    print(f"Wrote v0.3 measurement report: {output}")