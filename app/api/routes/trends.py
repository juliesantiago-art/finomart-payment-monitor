from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_session
from app.schemas.insights import TrendsResponse
from app.services.trend_analyzer import compute_trends

router = APIRouter()


@router.get("/trends", response_model=TrendsResponse, dependencies=[Depends(verify_api_key)])
async def get_trends(
    country: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    methods = await compute_trends(session, country=country, date_from=date_from, date_to=date_to)
    return TrendsResponse(methods=methods)
