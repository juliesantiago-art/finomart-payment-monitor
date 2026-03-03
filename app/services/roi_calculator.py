from app.schemas.insights import ROIResult
from app.schemas.metrics import PaymentMethodMetrics


def calculate_roi(metrics: list[PaymentMethodMetrics]) -> list[ROIResult]:
    results: list[ROIResult] = []

    for m in metrics:
        net_rev = m.net_revenue_usd
        total_cost = m.total_cost_usd

        if total_cost > 0:
            roi_pct = (net_rev - total_cost) / total_cost * 100
        elif net_rev > 0:
            roi_pct = float("inf")
        else:
            roi_pct = 0.0

        # Cap at sensible display value
        if roi_pct == float("inf"):
            roi_pct = 9999.0

        if roi_pct > 50:
            recommendation = "KEEP"
        elif roi_pct >= 0:
            recommendation = "NEGOTIATE"
        else:
            recommendation = "REMOVE"

        # Breakeven: monthly_fee / margin_per_tx where margin_per_tx = net_rev/tx_count
        # If no per-tx margin, use the per-tx cost as floor
        monthly_fee = m.monthly_fee_usd
        per_tx_cost = (total_cost - monthly_fee) / m.total_transactions if m.total_transactions > 0 else 0.0
        margin_per_tx = net_rev / m.total_transactions if m.total_transactions > 0 else 0.0

        net_margin_per_tx = margin_per_tx - per_tx_cost
        if net_margin_per_tx > 0:
            breakeven = int(monthly_fee / net_margin_per_tx) + 1
        elif monthly_fee == 0:
            breakeven = 0
        else:
            breakeven = -1  # never breaks even with current margins

        results.append(
            ROIResult(
                payment_method_id=m.payment_method_id,
                name=m.name,
                country=m.country,
                net_revenue_usd=round(net_rev, 2),
                total_cost_usd=round(total_cost, 2),
                roi_pct=round(roi_pct, 2),
                recommendation=recommendation,
                breakeven_tx_count=breakeven,
            )
        )

    return results
