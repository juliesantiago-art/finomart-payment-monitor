import pytest

from tests.conftest import AUTH_HEADERS
from tests.helpers import seed_payment_method, seed_transactions


@pytest.mark.asyncio
async def test_metrics_requires_auth(client):
    response = await client.get("/api/v1/metrics")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_metrics_returns_empty_without_data(client):
    response = await client.get("/api/v1/metrics", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["methods"] == []


@pytest.mark.asyncio
async def test_ingest_and_retrieve_metrics(client, session):
    await seed_payment_method(session, id="visa_mx", country="MX", monthly_fee=100.0, per_tx_fee=0.10)
    await session.commit()

    # Ingest transactions via API
    txns = [
        {
            "payment_method_id": "visa_mx",
            "country": "MX",
            "amount": 500.0,
            "currency": "MXN",
            "status": "approved",
            "chargeback_flag": False,
            "installment_count": 1,
            "created_at": "2025-06-15T10:00:00+00:00",
        }
        for _ in range(10)
    ]
    ingest_response = await client.post("/api/v1/transactions/ingest", json=txns, headers=AUTH_HEADERS)
    assert ingest_response.status_code == 200
    assert ingest_response.json()["inserted"] == 10

    # Get metrics
    metrics_response = await client.get("/api/v1/metrics?country=MX", headers=AUTH_HEADERS)
    assert metrics_response.status_code == 200
    methods = metrics_response.json()["methods"]
    assert len(methods) == 1
    assert methods[0]["payment_method_id"] == "visa_mx"
    assert methods[0]["total_transactions"] == 10
    assert methods[0]["approved_count"] == 10


@pytest.mark.asyncio
async def test_metrics_pagination(client, session):
    await seed_payment_method(session, id="pix_br", country="BR", monthly_fee=50.0)
    await seed_transactions(session, "pix_br", "BR", "BRL", count=5, status="approved",
                            usd_amount=10.0, net_revenue_usd=0.15)
    await session.commit()

    resp = await client.get("/api/v1/transactions?limit=3&offset=0", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 3

    resp2 = await client.get("/api/v1/transactions?limit=3&offset=3", headers=AUTH_HEADERS)
    assert resp2.status_code == 200
    assert len(resp2.json()) == 2


@pytest.mark.asyncio
async def test_metrics_method_filter(client, session):
    await seed_payment_method(session, id="spei_mx", name="SPEI", type="bank_transfer", country="MX")
    await seed_payment_method(session, id="oxxo_mx", name="OXXO", type="cash", country="MX")
    await session.commit()

    resp = await client.get("/api/v1/metrics?method_type=bank_transfer", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    methods = resp.json()["methods"]
    assert all(m["type"] == "bank_transfer" for m in methods)


@pytest.mark.asyncio
async def test_metrics_single_method_not_found(client):
    resp = await client.get("/api/v1/metrics/nonexistent_method", headers=AUTH_HEADERS)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_ingest_limit_201_items(client, session):
    await seed_payment_method(session, id="visa_mx", country="MX")
    await session.commit()

    txns = [
        {
            "payment_method_id": "visa_mx",
            "country": "MX",
            "amount": 100.0,
            "currency": "MXN",
            "status": "approved",
            "installment_count": 1,
            "created_at": "2025-06-15T10:00:00+00:00",
        }
    ] * 201
    # Ingest should work (no limit on ingest endpoint, only GET transactions)
    resp = await client.post("/api/v1/transactions/ingest", json=txns, headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["inserted"] == 201
