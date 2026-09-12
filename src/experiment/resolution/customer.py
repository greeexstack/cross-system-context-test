from dataclasses import dataclass
from typing import Optional

from experiment.domain.models import Customer


@dataclass(frozen=True)
class CustomerMatch:
    crm_customer_id: str
    communication_customer_id: str
    status: str
    confidence: float
    reason: str


class CustomerResolver:
    def resolve(
        self,
        crm_customer: Customer,
        communication_customer: dict,
    ) -> CustomerMatch:
        crm_email = self._normalize(crm_customer.email)
        communication_email = self._normalize(
            communication_customer.get("email")
        )

        crm_phone = self._normalize(crm_customer.phone)
        communication_phone = self._normalize(
            communication_customer.get("phone")
        )

        crm_name = self._normalize(crm_customer.name)
        communication_name = self._normalize(
            communication_customer.get("name")
        )

        if crm_email and communication_email and crm_email == communication_email:
            return CustomerMatch(
                crm_customer_id=crm_customer.id,
                communication_customer_id=communication_customer["id"],
                status="confident_match",
                confidence=1.0,
                reason="Exact email match.",
            )

        if crm_phone and communication_phone and crm_phone == communication_phone:
            return CustomerMatch(
                crm_customer_id=crm_customer.id,
                communication_customer_id=communication_customer["id"],
                status="confident_match",
                confidence=1.0,
                reason="Exact phone match.",
            )

        if crm_name and communication_name and crm_name == communication_name:
            return CustomerMatch(
                crm_customer_id=crm_customer.id,
                communication_customer_id=communication_customer["id"],
                status="ambiguous_match",
                confidence=0.6,
                reason="Name matches but no stronger identity signal matched.",
            )

        return CustomerMatch(
            crm_customer_id=crm_customer.id,
            communication_customer_id=communication_customer["id"],
            status="no_match",
            confidence=0.0,
            reason="No sufficiently strong identity signal matched.",
        )

    @staticmethod
    def _normalize(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        normalized = value.strip().lower()

        if not normalized:
            return None

        return normalized