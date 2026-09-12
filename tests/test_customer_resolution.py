from experiment.domain.models import Customer
from experiment.resolution.customer import CustomerResolver


def make_crm_customer(
    name="Aarav Mehta",
    email="aarav@example.com",
    phone="+91-9000000001",
):
    return Customer(
        id="crm_cust_001",
        business_id="biz_001",
        name=name,
        email=email,
        phone=phone,
    )


def test_exact_email_match_is_confident():
    resolver = CustomerResolver()

    result = resolver.resolve(
        make_crm_customer(),
        {
            "id": "comm_cust_001",
            "name": "Aarav Mehta",
            "email": "aarav@example.com",
            "phone": "+91-9000000001",
        },
    )

    assert result.status == "confident_match"
    assert result.confidence == 1.0
    assert result.reason == "Exact email match."


def test_exact_phone_match_is_confident():
    resolver = CustomerResolver()

    result = resolver.resolve(
        make_crm_customer(email="crm@example.com"),
        {
            "id": "comm_cust_001",
            "name": "Aarav Mehta",
            "email": "different@example.com",
            "phone": "+91-9000000001",
        },
    )

    assert result.status == "confident_match"
    assert result.confidence == 1.0
    assert result.reason == "Exact phone match."


def test_name_only_match_is_ambiguous():
    resolver = CustomerResolver()

    result = resolver.resolve(
        make_crm_customer(email="crm@example.com", phone="+91-9111111111"),
        {
            "id": "comm_cust_001",
            "name": "Aarav Mehta",
            "email": "different@example.com",
            "phone": "+91-9222222222",
        },
    )

    assert result.status == "ambiguous_match"
    assert result.confidence == 0.6


def test_no_match_does_not_create_relationship():
    resolver = CustomerResolver()

    result = resolver.resolve(
        make_crm_customer(),
        {
            "id": "comm_cust_999",
            "name": "Completely Different",
            "email": "different@example.com",
            "phone": "+91-9999999999",
        },
    )

    assert result.status == "no_match"
    assert result.confidence == 0.0