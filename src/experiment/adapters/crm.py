import json
from pathlib import Path

from experiment.domain.models import (
    Business,
    Customer,
    Employee,
    Opportunity,
    Quote,
)


class CRMAdapter:
    def __init__(self, source_path: str | Path):
        self.source_path = Path(source_path)

    def load(self) -> list[dict]:
        with self.source_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return data["records"]

    def load_entities(self) -> list[tuple[Business, Customer, Employee, Opportunity, Quote]]:
        records = self.load()
        entities = []

        for record in records:
            business_data = record["business"]
            customer_data = record["customer"]
            employee_data = record["employee"]
            opportunity_data = record["opportunity"]
            quote_data = record["quote"]

            business = Business(
                id=business_data["id"],
                name=business_data["name"],
            )

            customer = Customer(
                id=customer_data["id"],
                business_id=business.id,
                name=customer_data["name"],
                email=customer_data.get("email"),
                phone=customer_data.get("phone"),
            )

            employee = Employee(
                id=employee_data["id"],
                business_id=business.id,
                name=employee_data["name"],
            )

            opportunity = Opportunity(
                id=opportunity_data["id"],
                business_id=business.id,
                customer_id=customer.id,
                owner_id=employee.id,
                stage=opportunity_data["stage"],
                value=float(opportunity_data["value"]),
                quote_sent_at=self._parse_datetime(
                    opportunity_data.get("quote_sent_at")
                ),
                last_crm_activity_at=self._parse_datetime(
                    opportunity_data.get("last_crm_activity_at")
                ),
            )

            quote = Quote(
                id=quote_data["id"],
                opportunity_id=opportunity.id,
                amount=float(quote_data["amount"]),
                sent_at=self._parse_datetime(quote_data["sent_at"]),
            )

            entities.append(
                (business, customer, employee, opportunity, quote)
            )

        return entities

    @staticmethod
    def _parse_datetime(value: str | None):
        if value is None:
            return None

        from datetime import datetime

        return datetime.fromisoformat(value)