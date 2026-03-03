import pytest

from tests.helpers import seed_payment_method


@pytest.mark.asyncio
async def test_gaps_detected_for_missing_high_popularity(client, session):
    # Only seed Visa MX (popularity 10) — SPEI (9), MercadoPago (8), OXXO (8), PayPal (8), Klarna (7), Amex (7) are missing
    await seed_payment_method(session, id="visa_mx", name="Visa", type="card", country="MX")
    await session.commit()

    resp = await client.get("/api/v1/market-gaps?country=MX", headers={"X-API-Key": "dev-api-key-change-in-production"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_gaps"] >= 1
    gap_ids = [g["method_id"] for g in data["gaps"]]
    assert "spei_mx" in gap_ids  # popularity 9, should be a gap


@pytest.mark.asyncio
async def test_gaps_not_flagged_when_method_active(client, session):
    # Seed all high-popularity MX methods
    methods = [
        ("visa_mx", "Visa", "card"),
        ("mastercard_mx", "Mastercard", "card"),
        ("spei_mx", "SPEI", "bank_transfer"),
        ("oxxo_mx", "OXXO", "cash"),
        ("mercadopago_mx", "MercadoPago", "wallet"),
        ("paypal_mx", "PayPal", "wallet"),
        ("amex_mx", "Amex", "card"),
        ("klarna_mx", "Klarna", "bnpl"),
    ]
    for id_, name, type_ in methods:
        await seed_payment_method(session, id=id_, name=name, type=type_, country="MX")
    await session.commit()

    resp = await client.get("/api/v1/market-gaps?country=MX", headers={"X-API-Key": "dev-api-key-change-in-production"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_gaps"] == 0


@pytest.mark.asyncio
async def test_gaps_all_countries(client, session):
    # Don't seed anything — expect gaps in all countries
    resp = await client.get("/api/v1/market-gaps", headers={"X-API-Key": "dev-api-key-change-in-production"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_gaps"] > 0
    countries = {g["country"] for g in data["gaps"]}
    assert len(countries) > 1
