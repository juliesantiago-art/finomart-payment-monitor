from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_session
from app.schemas.metrics import MetricsResponse, PaymentMethodMetrics
from app.services.metrics_engine import compute_metrics

router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse, dependencies=[Depends(verify_api_key)])
async def get_metrics(
    country: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    method_type: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    methods = await compute_metrics(session, country=country, date_from=date_from, date_to=date_to, method_type=method_type)
    return MetricsResponse(
        country=country,
        date_from=str(date_from) if date_from else None,
        date_to=str(date_to) if date_to else None,
        method_type=method_type,
        methods=methods,
    )


@router.get("/metrics/{payment_method_id}", response_model=PaymentMethodMetrics, dependencies=[Depends(verify_api_key)])
async def get_method_metrics(
    payment_method_id: str,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    all_methods = await compute_metrics(session, date_from=date_from, date_to=date_to)
    match = next((m for m in all_methods if m.payment_method_id == payment_method_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Payment method '{payment_method_id}' not found")
    return match
