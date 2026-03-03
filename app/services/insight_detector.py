import statistics
from typing import Optional

from app.schemas.insights import Insight
from app.schemas.metrics import PaymentMethodMetrics


def detect_insights(
    metrics: list[PaymentMethodMetrics],
    country_filter: Optional[str] = None,
    insight_type_filter: Optional[str] = None,
) -> list[Insight]:
    insights: list[Insight] = []

    # Group metrics by country for comparative analysis
    by_country: dict[str, list[PaymentMethodMetrics]] = {}
    for m in metrics:
        by_country.setdefault(m.country, []).append(m)

    for country, methods in by_country.items():
        if country_filter and country != country_filter:
            continue

        approval_rates = [m.approval_rate for m in methods if m.total_transactions > 0]
        country_avg_approval = statistics.mean(approval_rates) if approval_rates else 0.0
        tx_counts = [m.total_transactions for m in methods]
        country_median_tx = statistics.median(tx_counts) if tx_counts else 0

        for m in methods:
            # 1. Zombie: dormant + has monthly fee
            if m.activity_status == "dormant" and m.monthly_fee_usd > 0:
                insights.append(
                    Insight(
                        payment_method_id=m.payment_method_id,
                        payment_method_name=m.name,
                        country=m.country,
                        insight_type="zombie",
                        metric="total_transactions",
                        value=float(m.total_transactions),
                        recommended_action=f"Consider deactivating — only {m.total_transactions} tx/90d but costs ${m.monthly_fee_usd:.2f}/mo",
                    )
                )

            # 2. Hidden Gem: above-avg approval, >5% revenue contribution, below-median tx count
            if (
                m.approval_rate > country_avg_approval
                and m.revenue_contribution_pct > 5.0
                and m.total_transactions < country_median_tx
            ):
                insights.append(
                    Insight(
                        payment_method_id=m.payment_method_id,
                        payment_method_name=m.name,
                        country=m.country,
                        insight_type="hidden_gem",
                        metric="revenue_contribution_pct",
                        value=m.revenue_contribution_pct,
                        recommended_action="Promote in checkout — high conversion and revenue despite low volume",
                    )
                )

            # 3. Performance Alert: approval rate more than 15pp below country average
            if m.approval_rate < (country_avg_approval - 0.15) and m.total_transactions > 0:
                insights.append(
                    Insight(
                        payment_method_id=m.payment_method_id,
                        payment_method_name=m.name,
                        country=m.country,
                        insight_type="performance_alert",
                        metric="approval_rate",
                        value=round(m.approval_rate, 4),
                        recommended_action=f"Investigate technical issues — approval rate {m.approval_rate:.1%} vs country avg {country_avg_approval:.1%}",
                    )
                )

            # 4. Cost Trap: negative net cost efficiency
            if m.net_cost_efficiency_usd < 0:
                insights.append(
                    Insight(
                        payment_method_id=m.payment_method_id,
                        payment_method_name=m.name,
                        country=m.country,
                        insight_type="cost_trap",
                        metric="net_cost_efficiency_usd",
                        value=round(m.net_cost_efficiency_usd, 2),
                        recommended_action=f"Renegotiate fees or remove — costs exceed revenue by ${abs(m.net_cost_efficiency_usd):.2f}",
                    )
                )

    if insight_type_filter:
        insights = [i for i in insights if i.insight_type == insight_type_filter]

    return insights
