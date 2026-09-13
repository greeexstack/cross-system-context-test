from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .engine import ContextReasoningEngine, EngineConfig
from .evaluator import V02Evaluator, CaseScore


class V02Runner:
    def __init__(self, fixture_root: str | Path, stale_after_days: int = 30) -> None:
        self.root = Path(fixture_root)
        self.engine = ContextReasoningEngine(EngineConfig(stale_after_days=stale_after_days))
        self.evaluator = V02Evaluator()
        self._load()

    def _load_json(self, relative: str) -> Any:
        with (self.root / relative).open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load(self) -> None:
        self.customers = self._load_json("fixtures/customers.json")
        self.opportunities = self._load_json("fixtures/opportunities.json")
        self.communications = self._load_json("fixtures/communications.json")
        self.scenarios = self._load_json("fixtures/scenario_pairs.json")
        self.dev_gt = self._load_json("ground_truth/development.json")
        self.eval_gt = self._load_json("ground_truth/evaluation.json")
        self.engine.initialize_indexes(
            self.customers, self.opportunities, self.communications,
            self.dev_gt["experiment_time"],
        )

    def run_case(self, case: dict[str, Any]) -> CaseScore:
        expected = (self.dev_gt if case["split"] == "development" else self.eval_gt)
        expected_case = next(item for item in expected["cases"] if item["pair_id"] == case["pair_id"])
        base = self.engine.evaluate(case, phase="base")
        variant = self.engine.evaluate(case, phase="variant")
        return self.evaluator.score(case, base, variant, expected_case)

    def run_all(self) -> list[CaseScore]:
        return [self.run_case(case) for case in self.scenarios]
