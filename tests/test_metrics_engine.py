from datetime import datetime, timezone

import pytest

from app.services.metrics_engine import compute_metrics
from tests.helpers import seed_payment_method, seed_transactions


@pytest.mark.asyncio
async def test_metrics_approval_rate(session):
    await seed_payment_method(session, id="visa_mx", country="MX", monthly_fee=100.0, per_tx_fee=0.10)

    await seed_transactions(session, "visa_mx", "MX", "MXN", count=80, status="approved",
                            usd_amount=10.0, net_revenue_usd=0.25)
    await seed_transactions(session, "visa_mx", "MX", "MXN", count=20, status="declined",
                            usd_amount=10.0, net_revenue_usd=0.0)
    await session.commit()

    metrics = await compute_metrics(session, country="MX")
    assert len(metrics) == 1
    m = metrics[0]
    assert m.total_transactions == 100
    assert m.approved_count == 80
    assert abs(m.approval_rate - 0.80) < 0.001


@pytest.mark.asyncio
async def test_metrics_net_revenue(session):
    await seed_payment_method(session, id="spei_mx", country="MX", monthly_fee=50.0, per_tx_fee=0.05)
    await seed_transactions(session, "spei_mx", "MX", "MXN", count=30, status="approved",
                            usd_amount=20.0, net_revenue_usd=0.30)
    await session.commit()

    metrics = await compute_metrics(session, country="MX")
    m = next(m for m in metrics if m.payment_method_id == "spei_mx")
    assert abs(m.net_revenue_usd - 9.0) < 0.01  # 30 * 0.30


@pytest.mark.asyncio
async def test_metrics_activity_status(session):
    await seed_payment_method(session, id="zombie_cl", name="Zombie", type="card", country="CL", monthly_fee=200.0)
    await seed_transactions(session, "zombie_cl", "CL", "CLP", count=5, status="approved",
                            usd_amount=5.0, net_revenue_usd=0.11)
    await session.commit()

    metrics = await compute_metrics(session, country="CL")
    m = metrics[0]
    assert m.activity_status == "dormant"
    assert m.total_transactions == 5


@pytest.mark.asyncio
async def test_metrics_cost_efficiency(session):
    # monthly_fee=100, per_tx=0.10, 10 transactions → total_cost = 100 + 10*0.10 = 101
    # net_revenue = 10 * 0.50 = 5 → efficiency = 5 - 101 = -96
    await seed_payment_method(session, id="trap_mx", country="MX", monthly_fee=100.0, per_tx_fee=0.10)
    await seed_transactions(session, "trap_mx", "MX", "MXN", count=10, status="approved",
                            usd_amount=20.0, net_revenue_usd=0.50)
    await session.commit()

    metrics = await compute_metrics(session, country="MX")
    m = next(m for m in metrics if m.payment_method_id == "trap_mx")
    assert m.net_cost_efficiency_usd < 0


@pytest.mark.asyncio
async def test_metrics_revenue_contribution_pct(session):
    await seed_payment_method(session, id="pix_br", country="BR", monthly_fee=50.0, per_tx_fee=0.05)
    await seed_payment_method(session, id="visa_br", name="Visa BR", type="card", country="BR",
                              monthly_fee=100.0, per_tx_fee=0.10)

    # pix_br: 20 tx * 1.0 revenue = 20 USD
    await seed_transactions(session, "pix_br", "BR", "BRL", count=20, status="approved",
                            usd_amount=50.0, net_revenue_usd=1.0)
    # visa_br: 40 tx * 0.5 revenue = 20 USD
    await seed_transactions(session, "visa_br", "BR", "BRL", count=40, status="approved",
                            usd_amount=20.0, net_revenue_usd=0.5)
    await session.commit()

    metrics = await compute_metrics(session, country="BR")
    pix = next(m for m in metrics if m.payment_method_id == "pix_br")
    visa = next(m for m in metrics if m.payment_method_id == "visa_br")
    # Total country rev = 20 + 20 = 40; each contributes 50%
    assert abs(pix.revenue_contribution_pct - 50.0) < 0.1
    assert abs(visa.revenue_contribution_pct - 50.0) < 0.1
