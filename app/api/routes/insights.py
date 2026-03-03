from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_session
from app.schemas.insights import InsightsResponse
from app.services.insight_detector import detect_insights
from app.services.metrics_engine import compute_metrics

router = APIRouter()


@router.get("/insights", response_model=InsightsResponse, dependencies=[Depends(verify_api_key)])
async def get_insights(
    country: Optional[str] = Query(None),
    insight_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    metrics = await compute_metrics(session, country=country, date_from=date_from, date_to=date_to)
    insights = detect_insights(metrics, country_filter=country, insight_type_filter=insight_type)
    return InsightsResponse(total=len(insights), insights=insights)
