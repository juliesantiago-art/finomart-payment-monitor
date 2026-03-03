from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_session
from app.schemas.insights import ROIResponse
from app.services.metrics_engine import compute_metrics
from app.services.roi_calculator import calculate_roi

router = APIRouter()


@router.get("/roi", response_model=ROIResponse, dependencies=[Depends(verify_api_key)])
async def get_roi(
    country: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("roi_pct", description="Sort by: roi_pct or recommendation"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    metrics = await compute_metrics(session, country=country, date_from=date_from, date_to=date_to)
    roi_results = calculate_roi(metrics)

    if sort_by == "recommendation":
        order = {"REMOVE": 0, "NEGOTIATE": 1, "KEEP": 2}
        roi_results.sort(key=lambda r: order.get(r.recommendation, 99))
    else:
        roi_results.sort(key=lambda r: r.roi_pct)

    return ROIResponse(methods=roi_results)
