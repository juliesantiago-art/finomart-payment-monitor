from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integration_cost import IntegrationCost
from app.models.payment_method import PaymentMethod
from app.models.transaction import Transaction
from app.schemas.metrics import PaymentMethodMetrics

# Currency per country
COUNTRY_CURRENCY = {
    "MX": "MXN",
    "BR": "BRL",
    "CO": "COP",
    "AR": "ARS",
    "CL": "CLP",
    "PE": "PEN",
}


async def compute_metrics(
    session: AsyncSession,
    country: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    method_type: Optional[str] = None,
) -> list[PaymentMethodMetrics]:
    # Build base query filters
    tx_filters = []
    if country:
        tx_filters.append(Transaction.country == country)
    if date_from:
        dt_from = datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc)
        tx_filters.append(Transaction.created_at >= dt_from)
    if date_to:
        dt_to = datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, tzinfo=timezone.utc)
        tx_filters.append(Transaction.created_at <= dt_to)

    # Fetch all active payment methods
    pm_query = select(PaymentMethod).where(PaymentMethod.is_active == True)
    if country:
        pm_query = pm_query.where(PaymentMethod.country == country)
    if method_type:
        pm_query = pm_query.where(PaymentMethod.type == method_type)

    pm_result = await session.execute(pm_query)
    payment_methods = pm_result.scalars().all()

    if not payment_methods:
        return []

    method_ids = [pm.id for pm in payment_methods]

    # Aggregate transaction stats per method
    agg_query = (
        select(
            Transaction.payment_method_id,
            func.count(Transaction.id).label("total_transactions"),
            func.sum(
                case((Transaction.status == "approved", Transaction.amount), else_=0.0)
            ).label("tpv_local"),
            func.sum(
                case((Transaction.status == "approved", Transaction.usd_amount), else_=0.0)
            ).label("tpv_usd"),
            func.sum(
                case((Transaction.status == "approved", Transaction.net_revenue_usd), else_=0.0)
            ).label("net_revenue_usd"),
            func.sum(
                case((Transaction.status == "approved", 1), else_=0)
            ).label("approved_count"),
            func.sum(
                case(
                    ((Transaction.status == "approved") & (Transaction.chargeback_flag == True), 1),
                    else_=0,
                )
            ).label("chargeback_count"),
            func.avg(Transaction.settlement_speed_days).label("avg_settlement_days"),
        )
        .where(Transaction.payment_method_id.in_(method_ids))
    )
    for f in tx_filters:
        agg_query = agg_query.where(f)
    agg_query = agg_query.group_by(Transaction.payment_method_id)

    agg_result = await session.execute(agg_query)
    agg_rows = {row.payment_method_id: row for row in agg_result.all()}

    # Fetch latest integration costs
    cost_query = select(IntegrationCost).where(IntegrationCost.payment_method_id.in_(method_ids))
    cost_result = await session.execute(cost_query)
    all_costs = cost_result.scalars().all()
    # Keep only the latest cost per method
    costs_by_method: dict[str, IntegrationCost] = {}
    for cost in all_costs:
        existing = costs_by_method.get(cost.payment_method_id)
        if existing is None or cost.effective_from > existing.effective_from:
            costs_by_method[cost.payment_method_id] = cost

    # Compute country-level totals for contribution_pct
    country_revenue: dict[str, float] = {}
    for pm in payment_methods:
        row = agg_rows.get(pm.id)
        rev = row.net_revenue_usd if row and row.net_revenue_usd else 0.0
        country_revenue[pm.country] = country_revenue.get(pm.country, 0.0) + rev

    results: list[PaymentMethodMetrics] = []
    for pm in payment_methods:
        row = agg_rows.get(pm.id)
        cost = costs_by_method.get(pm.id)

        total_tx = int(row.total_transactions) if row else 0
        approved = int(row.approved_count) if row and row.approved_count else 0
        tpv_local = float(row.tpv_local) if row and row.tpv_local else 0.0
        tpv_usd = float(row.tpv_usd) if row and row.tpv_usd else 0.0
        net_rev = float(row.net_revenue_usd) if row and row.net_revenue_usd else 0.0
        chargeback_count = float(row.chargeback_count) if row and row.chargeback_count else 0.0
        avg_settlement = float(row.avg_settlement_days) if row and row.avg_settlement_days else None

        approval_rate = approved / total_tx if total_tx > 0 else 0.0
        chargeback_rate = chargeback_count / approved if approved > 0 else 0.0
        avg_tx_value_local = tpv_local / approved if approved > 0 else 0.0

        country_total_rev = country_revenue.get(pm.country, 0.0)
        revenue_contribution_pct = (net_rev / country_total_rev * 100) if country_total_rev > 0 else 0.0

        monthly_fee = cost.monthly_fee_usd if cost else 0.0
        per_tx_fee = cost.per_transaction_fee_usd if cost else 0.0
        total_cost = monthly_fee + per_tx_fee * total_tx
        net_cost_efficiency = net_rev - total_cost

        # Activity status: active >50 tx/90d, declining 10-50, dormant <10
        if total_tx >= 50:
            activity_status = "active"
        elif total_tx >= 10:
            activity_status = "declining"
        else:
            activity_status = "dormant"

        results.append(
            PaymentMethodMetrics(
                payment_method_id=pm.id,
                name=pm.name,
                type=pm.type,
                country=pm.country,
                currency=COUNTRY_CURRENCY.get(pm.country, "USD"),
                total_transactions=total_tx,
                approved_count=approved,
                tpv_local=round(tpv_local, 2),
                tpv_usd=round(tpv_usd, 2),
                net_revenue_usd=round(net_rev, 2),
                approval_rate=round(approval_rate, 4),
                chargeback_rate=round(chargeback_rate, 4),
                avg_transaction_value_local=round(avg_tx_value_local, 2),
                avg_settlement_days=round(avg_settlement, 2) if avg_settlement else None,
                revenue_contribution_pct=round(revenue_contribution_pct, 2),
                net_cost_efficiency_usd=round(net_cost_efficiency, 2),
                monthly_fee_usd=monthly_fee,
                total_cost_usd=round(total_cost, 2),
                activity_status=activity_status,
            )
        )

    return results
