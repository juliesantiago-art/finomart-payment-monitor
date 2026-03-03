import pytest

from tests.conftest import AUTH_HEADERS
from tests.helpers import seed_payment_method, seed_transactions


@pytest.mark.asyncio
async def test_html_report_requires_auth(client):
    resp = await client.get("/api/v1/reports/html")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_html_report_contains_sections(client, session):
    await seed_payment_method(session, id="visa_mx", country="MX", monthly_fee=100.0, per_tx_fee=0.10)
    await seed_transactions(session, "visa_mx", "MX", "MXN", count=60, status="approved",
                            usd_amount=10.0, net_revenue_usd=0.25)
    await session.commit()

    resp = await client.get("/api/v1/reports/html", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    html = resp.text

    assert "Portfolio Overview" in html
    assert "Top Performers" in html
    assert "Flagged Insights" in html
    assert "ROI Analysis" in html
    assert "Trend Summary" in html
    assert "Market Gaps" in html
    assert "FinoMart Payment Method Health Report" in html


@pytest.mark.asyncio
async def test_html_report_contains_method_name(client, session):
    await seed_payment_method(session, id="pix_br", name="PIX", country="BR", monthly_fee=50.0)
    await seed_transactions(session, "pix_br", "BR", "BRL", count=30, status="approved",
                            usd_amount=20.0, net_revenue_usd=0.30)
    await session.commit()

    resp = await client.get("/api/v1/reports/html", headers=AUTH_HEADERS)
    assert "PIX" in resp.text


@pytest.mark.asyncio
async def test_summary_endpoint(client, session):
    await seed_payment_method(session, id="visa_mx", country="MX", monthly_fee=100.0, per_tx_fee=0.10)
    await seed_transactions(session, "visa_mx", "MX", "MXN", count=70, status="approved",
                            usd_amount=10.0, net_revenue_usd=0.25)
    await session.commit()

    resp = await client.get("/api/v1/reports/summary", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_methods" in data
    assert "active_count" in data
    assert "total_net_revenue_usd" in data
    assert data["total_methods"] >= 1


@pytest.mark.asyncio
async def test_html_report_zombie_flagged(client, session):
    # Seed a zombie: dormant with monthly fee
    await seed_payment_method(session, id="webpay_cl", name="Webpay", type="card",
                               country="CL", monthly_fee=200.0, per_tx_fee=0.15)
    await seed_transactions(session, "webpay_cl", "CL", "CLP", count=3, status="approved",
                            usd_amount=5.0, net_revenue_usd=0.11)
    await session.commit()

    resp = await client.get("/api/v1/reports/html", headers=AUTH_HEADERS)
    html = resp.text
    assert "zombie" in html.lower() or "Zombie" in html
