from pathlib import Path

from experiment.adapters.communication import CommunicationAdapter
from experiment.adapters.crm import CRMAdapter


ROOT = Path(__file__).resolve().parents[1]


def test_crm_adapter_loads_all_records():
    adapter = CRMAdapter(ROOT / "scenarios" / "data" / "crm.json")

    entities = adapter.load_entities()

    assert len(entities) == 11

    business, customer, employee, opportunity, quote = entities[0]

    assert business.id == "biz_001"
    assert customer.name == "Aarav Mehta"
    assert employee.name == "Rahul Sharma"
    assert opportunity.id == "opp_001"
    assert opportunity.stage == "quote_sent"
    assert quote.id == "quote_001"


def test_communication_adapter_loads_available_communications():
    adapter = CommunicationAdapter(
        ROOT / "scenarios" / "data" / "communications.json"
    )

    communications = adapter.load_communications()

    assert len(communications) == 9

    first = communications[0]

    assert first.id == "comm_001"
    assert first.customer_id == "comm_cust_001"
    assert first.direction == "outbound"
    assert first.topic == "quote"