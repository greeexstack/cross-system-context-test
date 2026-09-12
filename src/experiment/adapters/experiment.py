import json
from datetime import datetime
from pathlib import Path


class ExperimentConfigAdapter:
    def __init__(self, source_path: str | Path):
        self.source_path = Path(source_path)

    def load_evaluation_at(self) -> datetime:
        with self.source_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return datetime.fromisoformat(data["evaluation_at"])