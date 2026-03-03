"""Admin endpoints for seeding reference data (payment methods, costs)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_session
from app.models.integration_cost import IntegrationCost
from app.models.payment_method import PaymentMethod

router = APIRouter()


class PaymentMethodCreate:
    pass


from pydantic import BaseModel
from typing import Optional


class PMCreate(BaseModel):
    id: str
    name: str
    type: str
    country: str
    is_active: bool = True


class CostCreate(BaseModel):
    payment_method_id: str
    monthly_fee_usd: float
    per_transaction_fee_usd: float
    effective_from: str  # ISO date string


@router.post("/admin/payment-methods", dependencies=[Depends(verify_api_key)])
async def create_payment_method(pm: PMCreate, session: AsyncSession = Depends(get_session)):
    existing = await session.get(PaymentMethod, pm.id)
    if existing:
        return {"status": "exists", "id": pm.id}
    obj = PaymentMethod(id=pm.id, name=pm.name, type=pm.type, country=pm.country, is_active=pm.is_active)
    session.add(obj)
    await session.commit()
    return {"status": "created", "id": pm.id}


@router.post("/admin/integration-costs", dependencies=[Depends(verify_api_key)])
async def create_integration_cost(cost: CostCreate, session: AsyncSession = Depends(get_session)):
    effective = datetime.fromisoformat(cost.effective_from).replace(tzinfo=timezone.utc)
    obj = IntegrationCost(
        payment_method_id=cost.payment_method_id,
        monthly_fee_usd=cost.monthly_fee_usd,
        per_transaction_fee_usd=cost.per_transaction_fee_usd,
        effective_from=effective,
    )
    session.add(obj)
    await session.commit()
    return {"status": "created"}


@router.post("/admin/seed", dependencies=[Depends(verify_api_key)])
async def bulk_seed(
    payload: dict,
    session: AsyncSession = Depends(get_session),
):
    """Bulk seed payment methods and integration costs from generate_test_data output."""
    pm_count = 0
    cost_count = 0

    for pm_data in payload.get("payment_methods", []):
        existing = await session.get(PaymentMethod, pm_data["id"])
        if not existing:
            obj = PaymentMethod(**pm_data)
            session.add(obj)
            pm_count += 1

    await session.flush()

    for cost_data in payload.get("integration_costs", []):
        effective = datetime.fromisoformat(cost_data["effective_from"]).replace(tzinfo=timezone.utc)
        obj = IntegrationCost(
            payment_method_id=cost_data["payment_method_id"],
            monthly_fee_usd=cost_data["monthly_fee_usd"],
            per_transaction_fee_usd=cost_data["per_transaction_fee_usd"],
            effective_from=effective,
        )
        session.add(obj)
        cost_count += 1

    await session.commit()
    return {"payment_methods_seeded": pm_count, "costs_seeded": cost_count}
