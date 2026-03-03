from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import YUNO_CATALOG
from app.models.payment_method import PaymentMethod
from app.schemas.insights import MarketGap, GapsResponse

# Estimated avg monthly revenue uplift per popularity point (rough heuristic in USD)
REVENUE_PER_POPULARITY_POINT = 500.0
MIN_POPULARITY_FOR_GAP = 7


async def detect_market_gaps(
    session: AsyncSession,
    country_filter: Optional[str] = None,
) -> GapsResponse:
    # Fetch active methods
    query = select(PaymentMethod).where(PaymentMethod.is_active == True)
    if country_filter:
        query = query.where(PaymentMethod.country == country_filter)
    result = await session.execute(query)
    active_methods = result.scalars().all()

    active_ids_by_country: dict[str, set[str]] = {}
    for pm in active_methods:
        active_ids_by_country.setdefault(pm.country, set()).add(pm.id)

    gaps: list[MarketGap] = []
    countries = [country_filter] if country_filter else list(YUNO_CATALOG.keys())

    for country in countries:
        catalog = YUNO_CATALOG.get(country, [])
        active_ids = active_ids_by_country.get(country, set())

        for method in catalog:
            if method["popularity_score"] >= MIN_POPULARITY_FOR_GAP and method["id"] not in active_ids:
                estimated_uplift = method["popularity_score"] * REVENUE_PER_POPULARITY_POINT
                gaps.append(
                    MarketGap(
                        country=country,
                        method_id=method["id"],
                        method_name=method["name"],
                        method_type=method["type"],
                        popularity_score=method["popularity_score"],
                        estimated_revenue_uplift_usd=estimated_uplift,
                    )
                )

    gaps.sort(key=lambda g: g.popularity_score, reverse=True)

    return GapsResponse(total_gaps=len(gaps), gaps=gaps)
