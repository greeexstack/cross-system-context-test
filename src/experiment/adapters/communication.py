import json
from datetime import datetime
from pathlib import Path

from experiment.domain.models import Communication


class CommunicationAdapter:
    def __init__(self, source_path: str | Path):
        self.source_path = Path(source_path)

    def load(self) -> list[dict]:
        with self.source_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return data["records"]

    def load_scenario(
        self,
        scenario_id: str,
    ) -> dict:
        for record in self.load():
            if record["scenario_id"] == scenario_id:
                return record

        raise ValueError(
            f"Communication scenario not found: {scenario_id}"
        )

    def load_communications(self) -> list[Communication]:
        records = self.load()
        communications = []

        for record in records:
            customer = record["customer"]
            communication_records = record["communications"]

            if communication_records is None:
                continue

            for item in communication_records:
             communications.append(
              Communication(
                id=item["id"],
                business_id="biz_001",
                customer_id=customer["id"],
                direction=item["direction"],
                timestamp=datetime.fromisoformat(
                item["timestamp"]
             ),
                channel=item["channel"],
             topic=item["topic"],
             content=item["content"],
             customer_name=customer.get("name"),
             customer_email=customer.get("email"),
             customer_phone=customer.get("phone"),
    )
)

        return communications