from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_session
from app.schemas.insights import GapsResponse
from app.services.market_gap_detector import detect_market_gaps

router = APIRouter()


@router.get("/market-gaps", response_model=GapsResponse, dependencies=[Depends(verify_api_key)])
async def get_market_gaps(
    country: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    return await detect_market_gaps(session, country_filter=country)
