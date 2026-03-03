"""Shared test helpers for seeding data."""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IntegrationCost, PaymentMethod, Transaction


async def seed_payment_method(
    session: AsyncSession,
    id: str = "visa_mx",
    name: str = "Visa",
    type: str = "card",
    country: str = "MX",
    monthly_fee: float = 100.0,
    per_tx_fee: float = 0.10,
) -> PaymentMethod:
    pm = PaymentMethod(id=id, name=name, type=type, country=country, is_active=True)
    session.add(pm)
    await session.flush()

    cost = IntegrationCost(
        payment_method_id=id,
        monthly_fee_usd=monthly_fee,
        per_transaction_fee_usd=per_tx_fee,
        effective_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    session.add(cost)
    await session.flush()
    return pm


async def seed_transactions(
    session: AsyncSession,
    payment_method_id: str,
    country: str,
    currency: str,
    count: int,
    status: str = "approved",
    amount: float = 100.0,
    usd_amount: float = 10.0,
    net_revenue_usd: float = 0.25,
    chargeback: bool = False,
    created_at: datetime = None,
) -> list[Transaction]:
    if created_at is None:
        created_at = datetime(2025, 6, 15, tzinfo=timezone.utc)

    txs = []
    for _ in range(count):
        tx = Transaction(
            payment_method_id=payment_method_id,
            country=country,
            amount=amount,
            currency=currency,
            usd_amount=usd_amount,
            net_revenue_usd=net_revenue_usd if status == "approved" else 0.0,
            status=status,
            chargeback_flag=chargeback,
            settlement_speed_days=2 if status == "approved" else None,
            created_at=created_at,
        )
        session.add(tx)
        txs.append(tx)

    await session.flush()
    return txs
