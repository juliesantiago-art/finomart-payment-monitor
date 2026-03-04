from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment_method import PaymentMethod
from app.models.transaction import Transaction
from app.schemas.insights import MethodTrend, TrendPoint


def _week_label(dt: datetime) -> str:
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%Y-W%V")


def _month_label(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


async def compute_trends(
    session: AsyncSession,
    country: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[MethodTrend]:
    # Fetch payment methods
    pm_query = select(PaymentMethod).where(PaymentMethod.is_active == True)
    if country:
        pm_query = pm_query.where(PaymentMethod.country == country)
    pm_result = await session.execute(pm_query)
    payment_methods = pm_result.scalars().all()

    if not payment_methods:
        return []

    method_ids = [pm.id for pm in payment_methods]

    # Fetch raw transactions for bucketing
    tx_query = select(Transaction).where(Transaction.payment_method_id.in_(method_ids))
    if country:
        tx_query = tx_query.where(Transaction.country == country)
    if date_from:
        dt_from = datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc)
        tx_query = tx_query.where(Transaction.created_at >= dt_from)
    if date_to:
        dt_to = datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, tzinfo=timezone.utc)
        tx_query = tx_query.where(Transaction.created_at <= dt_to)

    tx_result = await session.execute(tx_query)
    transactions = tx_result.scalars().all()

    # Group by method → period → stats
    # Structure: {method_id: {period_label: {tx_count, revenue, approved, total, chargeback}}}
    weekly: dict[str, dict[str, dict]] = {m.id: {} for m in payment_methods}
    monthly: dict[str, dict[str, dict]] = {m.id: {} for m in payment_methods}

    for tx in transactions:
        mid = tx.payment_method_id
        wk = _week_label(tx.created_at)
        mo = _month_label(tx.created_at)

        for bucket, label in [(weekly, wk), (monthly, mo)]:
            if label not in bucket[mid]:
                bucket[mid][label] = {"tx_count": 0, "revenue": 0.0, "approved": 0, "total": 0, "chargeback": 0}
            d = bucket[mid][label]
            d["total"] += 1
            d["tx_count"] += 1
            if tx.status == "approved":
                d["approved"] += 1
                d["revenue"] += tx.net_revenue_usd
                if tx.chargeback_flag:
                    d["chargeback"] += 1

    pm_map = {pm.id: pm for pm in payment_methods}
    results: list[MethodTrend] = []

    for mid, pm in pm_map.items():
        # Build sorted trend points
        weekly_points = _build_trend_points(weekly[mid])
        monthly_points = _build_trend_points(monthly[mid])

        # Determine flags
        flags = _detect_flags(weekly_points)

        results.append(
            MethodTrend(
                payment_method_id=mid,
                name=pm.name,
                country=pm.country,
                flags=flags,
                weekly_trend=weekly_points,
                monthly_trend=monthly_points,
            )
        )

    return results


def _build_trend_points(period_data: dict[str, dict]) -> list[TrendPoint]:
    points = []
    for label in sorted(period_data.keys()):
        d = period_data[label]
        total = d["total"]
        approved = d["approved"]
        approval_rate = approved / total if total > 0 else 0.0
        chargeback_rate = d["chargeback"] / approved if approved > 0 else 0.0
        points.append(
            TrendPoint(
                period=label,
                tx_count=d["tx_count"],
                net_revenue_usd=round(d["revenue"], 2),
                approval_rate=round(approval_rate, 4),
                chargeback_rate=round(chargeback_rate, 4),
            )
        )
    return points


def _detect_flags(weekly_points: list[TrendPoint]) -> list[str]:
    flags: set[str] = set()
    if len(weekly_points) < 2:
        return list(flags)

    vol_changes: list[float] = []
    ar_changes: list[float] = []

    for i in range(1, len(weekly_points)):
        prev = weekly_points[i - 1]
        curr = weekly_points[i]

        vol_changes.append(
            (curr.tx_count - prev.tx_count) / prev.tx_count if prev.tx_count > 0 else 0.0
        )
        ar_changes.append(
            (curr.approval_rate - prev.approval_rate) / prev.approval_rate
            if prev.approval_rate > 0
            else 0.0
        )

        # Chargeback spike: doubles week-over-week (single occurrence is enough)
        if prev.chargeback_rate > 0 and curr.chargeback_rate >= prev.chargeback_rate * 2:
            flags.add("CHARGEBACK_SPIKE")

    # DECLINING/GROWING require two consecutive weeks of >20% change
    for changes in (vol_changes, ar_changes):
        for i in range(len(changes) - 1):
            if changes[i] <= -0.20 and changes[i + 1] <= -0.20:
                flags.add("DECLINING")
            if changes[i] >= 0.20 and changes[i + 1] >= 0.20:
                flags.add("GROWING")

    return sorted(flags)
