from datetime import datetime, timedelta, timezone

import pytest

from app.services.trend_analyzer import compute_trends, _detect_flags, _build_trend_points
from app.schemas.insights import TrendPoint
from tests.helpers import seed_payment_method, seed_transactions


@pytest.mark.asyncio
async def test_trend_declining_flag(session):
    await seed_payment_method(session, id="visa_mx", country="MX")

    # Week 1: Monday Jan 6
    week1 = datetime(2025, 1, 6, tzinfo=timezone.utc)
    # Week 2: Monday Jan 13 — volume drops 50%
    week2 = datetime(2025, 1, 13, tzinfo=timezone.utc)

    await seed_transactions(session, "visa_mx", "MX", "MXN", count=10, status="approved",
                            usd_amount=10.0, net_revenue_usd=0.25, created_at=week1)
    await seed_transactions(session, "visa_mx", "MX", "MXN", count=4, status="approved",
                            usd_amount=10.0, net_revenue_usd=0.25, created_at=week2)
    await session.commit()

    trends = await compute_trends(session, country="MX")
    assert len(trends) == 1
    assert "DECLINING" in trends[0].flags


@pytest.mark.asyncio
async def test_trend_growing_flag(session):
    await seed_payment_method(session, id="pix_br", country="BR")

    week1 = datetime(2025, 1, 6, tzinfo=timezone.utc)
    week2 = datetime(2025, 1, 13, tzinfo=timezone.utc)

    await seed_transactions(session, "pix_br", "BR", "BRL", count=5, status="approved",
                            usd_amount=20.0, net_revenue_usd=0.30, created_at=week1)
    await seed_transactions(session, "pix_br", "BR", "BRL", count=10, status="approved",
                            usd_amount=20.0, net_revenue_usd=0.30, created_at=week2)
    await session.commit()

    trends = await compute_trends(session, country="BR")
    assert "GROWING" in trends[0].flags


@pytest.mark.asyncio
async def test_trend_chargeback_spike(session):
    await seed_payment_method(session, id="oxxo_mx", country="MX")

    week1 = datetime(2025, 1, 6, tzinfo=timezone.utc)
    week2 = datetime(2025, 1, 13, tzinfo=timezone.utc)

    # Week 1: 10 approved, 1 chargeback
    await seed_transactions(session, "oxxo_mx", "MX", "MXN", count=9, status="approved",
                            usd_amount=10.0, net_revenue_usd=0.35, created_at=week1)
    await seed_transactions(session, "oxxo_mx", "MX", "MXN", count=1, status="approved",
                            usd_amount=10.0, net_revenue_usd=0.35, chargeback=True, created_at=week1)

    # Week 2: 10 approved, 5 chargebacks (spike!)
    await seed_transactions(session, "oxxo_mx", "MX", "MXN", count=5, status="approved",
                            usd_amount=10.0, net_revenue_usd=0.35, created_at=week2)
    await seed_transactions(session, "oxxo_mx", "MX", "MXN", count=5, status="approved",
                            usd_amount=10.0, net_revenue_usd=0.35, chargeback=True, created_at=week2)
    await session.commit()

    trends = await compute_trends(session, country="MX")
    assert "CHARGEBACK_SPIKE" in trends[0].flags


def test_detect_flags_no_data():
    points = [TrendPoint(period="2025-W01", tx_count=10, net_revenue_usd=5.0,
                         approval_rate=0.8, chargeback_rate=0.01)]
    flags = _detect_flags(points)
    assert flags == []


def test_detect_flags_stable():
    points = [
        TrendPoint(period="2025-W01", tx_count=10, net_revenue_usd=5.0, approval_rate=0.80, chargeback_rate=0.01),
        TrendPoint(period="2025-W02", tx_count=10, net_revenue_usd=5.0, approval_rate=0.80, chargeback_rate=0.01),
    ]
    flags = _detect_flags(points)
    assert "DECLINING" not in flags
    assert "GROWING" not in flags
