from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.config import FX_RATES, MARGIN_RATES, DEFAULT_MARGIN_RATE
from app.database import get_session
from app.models.transaction import Transaction
from app.schemas.transaction import IngestResponse, TransactionIngest, TransactionResponse

router = APIRouter()


@router.post("/transactions/ingest", response_model=IngestResponse, dependencies=[Depends(verify_api_key)])
async def ingest_transactions(
    payload: list[TransactionIngest],
    session: AsyncSession = Depends(get_session),
):
    rows = []
    for item in payload:
        fx = FX_RATES.get(item.currency, 1.0)
        usd_amount = item.amount * fx
        margin = MARGIN_RATES.get(item.payment_method_id, DEFAULT_MARGIN_RATE)
        net_rev = usd_amount * margin if item.status == "approved" else 0.0

        tx = Transaction(
            payment_method_id=item.payment_method_id,
            country=item.country,
            amount=item.amount,
            currency=item.currency,
            usd_amount=round(usd_amount, 4),
            net_revenue_usd=round(net_rev, 4),
            status=item.status,
            chargeback_flag=item.chargeback_flag,
            settlement_speed_days=item.settlement_speed_days,
            fx_spread_pct=item.fx_spread_pct,
            installment_count=item.installment_count,
            created_at=item.created_at,
        )
        rows.append(tx)

    session.add_all(rows)
    await session.commit()

    return IngestResponse(inserted=len(rows), message=f"Successfully ingested {len(rows)} transactions")


@router.get("/transactions", response_model=list[TransactionResponse], dependencies=[Depends(verify_api_key)])
async def list_transactions(
    country: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    query = select(Transaction)
    if country:
        query = query.where(Transaction.country == country)
    if status:
        query = query.where(Transaction.status == status)
    query = query.order_by(Transaction.created_at.desc()).limit(limit).offset(offset)

    result = await session.execute(query)
    return result.scalars().all()
