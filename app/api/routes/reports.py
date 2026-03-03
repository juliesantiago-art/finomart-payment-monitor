from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_session
from app.schemas.insights import PortfolioSummary
from app.services.insight_detector import detect_insights
from app.services.market_gap_detector import detect_market_gaps
from app.services.metrics_engine import compute_metrics
from app.services.report_generator import build_portfolio_summary, generate_html_report
from app.services.roi_calculator import calculate_roi
from app.services.trend_analyzer import compute_trends

router = APIRouter()


async def _gather_report_data(
    session: AsyncSession,
    country: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
):
    metrics = await compute_metrics(session, country=country, date_from=date_from, date_to=date_to)
    insights = detect_insights(metrics, country_filter=country)
    roi_results = calculate_roi(metrics)
    trends = await compute_trends(session, country=country, date_from=date_from, date_to=date_to)
    gaps = await detect_market_gaps(session, country_filter=country)
    summary = build_portfolio_summary(metrics, insights, roi_results)
    return metrics, insights, roi_results, trends, gaps, summary


@router.get("/reports/html", response_class=HTMLResponse, dependencies=[Depends(verify_api_key)])
async def get_html_report(
    country: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    metrics, insights, roi_results, trends, gaps, summary = await _gather_report_data(
        session, country, date_from, date_to
    )
    html = generate_html_report(metrics, insights, roi_results, trends, gaps, summary)
    return HTMLResponse(content=html)


@router.get("/reports/summary", response_model=PortfolioSummary, dependencies=[Depends(verify_api_key)])
async def get_portfolio_summary(
    country: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    metrics, insights, roi_results, _, _, summary = await _gather_report_data(
        session, country, date_from, date_to
    )
    return summary
