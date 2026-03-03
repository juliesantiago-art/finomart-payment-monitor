import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_unauthenticated_metrics_returns_401(client):
    response = await client.get("/api/v1/metrics")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_transactions_returns_401(client):
    response = await client.get("/api/v1/transactions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_insights_returns_401(client):
    response = await client.get("/api/v1/insights")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_roi_returns_401(client):
    response = await client.get("/api/v1/roi")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unknown_route_returns_404(client):
    response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
