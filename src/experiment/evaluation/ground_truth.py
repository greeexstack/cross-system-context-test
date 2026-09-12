import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExpectedAnalysis:
    finding: bool
    diagnosis_class: str
    confidence: str
    recommendation_class: str


@dataclass(frozen=True)
class ExpectedIdentityResolution:
    status: str | None


@dataclass(frozen=True)
class ScenarioGroundTruth:
    scenario_id: str
    description: str
    primary_only: ExpectedAnalysis
    cross_system: ExpectedAnalysis
    incremental_information: bool
    identity_resolution: ExpectedIdentityResolution


class GroundTruthLoader:
    def __init__(self, scenarios_root: str | Path):
        self.scenarios_root = Path(scenarios_root)

    def load(self, scenario_id: str) -> ScenarioGroundTruth:
        scenario_path = (
            self.scenarios_root
            / scenario_id
            / "scenario.json"
        )

        if not scenario_path.exists():
            raise ValueError(
                f"Scenario ground truth not found: {scenario_id}"
            )

        with scenario_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if data.get("scenario_id") != scenario_id:
            raise ValueError(
                "Scenario ID mismatch: "
                f"expected '{scenario_id}', "
                f"found '{data.get('scenario_id')}'."
            )

        expected = data["expected"]

        primary_only = self._load_analysis(
            expected["primary_only"]
        )

        cross_system = self._load_analysis(
            expected["cross_system"]
        )

        identity_data = data.get("identity_resolution", {})

        identity_resolution = ExpectedIdentityResolution(
            status=identity_data.get("expected_status")
        )

        return ScenarioGroundTruth(
            scenario_id=data["scenario_id"],
            description=data["description"],
            primary_only=primary_only,
            cross_system=cross_system,
            incremental_information=expected[
                "incremental_information"
            ],
            identity_resolution=identity_resolution,
        )

    @staticmethod
    def _load_analysis(data: dict) -> ExpectedAnalysis:
        return ExpectedAnalysis(
            finding=bool(data["finding"]),
            diagnosis_class=data["diagnosis_class"],
            confidence=data["confidence"],
            recommendation_class=data["recommendation_class"],
        )