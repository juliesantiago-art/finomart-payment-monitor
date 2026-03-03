from datetime import datetime, timezone

import pytest

from app.models import IntegrationCost, PaymentMethod, Transaction


@pytest.mark.asyncio
async def test_payment_method_create(session):
    pm = PaymentMethod(id="test_visa", name="Visa Test", type="card", country="MX", is_active=True)
    session.add(pm)
    await session.commit()
    await session.refresh(pm)
    assert pm.id == "test_visa"
    assert pm.country == "MX"


@pytest.mark.asyncio
async def test_integration_cost_create(session):
    pm = PaymentMethod(id="test_pm", name="Test PM", type="wallet", country="BR", is_active=True)
    session.add(pm)
    await session.flush()

    cost = IntegrationCost(
        payment_method_id="test_pm",
        monthly_fee_usd=99.99,
        per_transaction_fee_usd=0.10,
        effective_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    session.add(cost)
    await session.commit()
    await session.refresh(cost)
    assert cost.monthly_fee_usd == 99.99
    assert cost.per_transaction_fee_usd == 0.10


@pytest.mark.asyncio
async def test_transaction_create_with_all_fields(session):
    pm = PaymentMethod(id="test_card", name="Card Test", type="card", country="MX", is_active=True)
    session.add(pm)
    await session.flush()

    tx = Transaction(
        payment_method_id="test_card",
        country="MX",
        amount=500.0,
        currency="MXN",
        usd_amount=29.0,       # 500 * 0.058
        net_revenue_usd=0.725, # 29 * 0.025
        status="approved",
        chargeback_flag=False,
        settlement_speed_days=2,
        fx_spread_pct=1.5,
        installment_count=3,
        created_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)

    assert tx.usd_amount == 29.0
    assert tx.net_revenue_usd == 0.725
    assert tx.chargeback_flag is False
    assert tx.settlement_speed_days == 2
    assert tx.fx_spread_pct == 1.5
    assert tx.installment_count == 3


@pytest.mark.asyncio
async def test_declined_transaction_zero_revenue(session):
    pm = PaymentMethod(id="test_card2", name="Card2", type="card", country="BR", is_active=True)
    session.add(pm)
    await session.flush()

    tx = Transaction(
        payment_method_id="test_card2",
        country="BR",
        amount=100.0,
        currency="BRL",
        usd_amount=20.0,
        net_revenue_usd=0.0,  # declined → no revenue
        status="declined",
        created_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    assert tx.net_revenue_usd == 0.0
    assert tx.status == "declined"
