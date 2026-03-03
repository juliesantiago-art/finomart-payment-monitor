import pytest

from app.schemas.metrics import PaymentMethodMetrics
from app.services.roi_calculator import calculate_roi


def make_metric(
    id: str = "visa_mx",
    net_revenue: float = 500.0,
    monthly_fee: float = 100.0,
    total_cost: float = 110.0,
    tx_count: int = 100,
    country: str = "MX",
) -> PaymentMethodMetrics:
    return PaymentMethodMetrics(
        payment_method_id=id,
        name="Test",
        type="card",
        country=country,
        currency="MXN",
        total_transactions=tx_count,
        approved_count=tx_count,
        tpv_local=10000.0,
        tpv_usd=580.0,
        net_revenue_usd=net_revenue,
        approval_rate=0.80,
        chargeback_rate=0.01,
        avg_transaction_value_local=100.0,
        avg_settlement_days=2.0,
        revenue_contribution_pct=50.0,
        net_cost_efficiency_usd=net_revenue - total_cost,
        monthly_fee_usd=monthly_fee,
        total_cost_usd=total_cost,
        activity_status="active",
    )


def test_roi_keep():
    m = make_metric(net_revenue=500.0, total_cost=100.0)
    result = calculate_roi([m])[0]
    expected_roi = (500 - 100) / 100 * 100  # 400%
    assert abs(result.roi_pct - expected_roi) < 0.01
    assert result.recommendation == "KEEP"


def test_roi_negotiate():
    m = make_metric(net_revenue=120.0, total_cost=100.0)
    result = calculate_roi([m])[0]
    expected_roi = (120 - 100) / 100 * 100  # 20%
    assert abs(result.roi_pct - expected_roi) < 0.01
    assert result.recommendation == "NEGOTIATE"


def test_roi_remove():
    m = make_metric(net_revenue=50.0, total_cost=200.0)
    result = calculate_roi([m])[0]
    assert result.roi_pct < 0
    assert result.recommendation == "REMOVE"


def test_roi_breakeven():
    # monthly_fee=100, per_tx net margin = 0.50 - 0.10 = 0.40 per tx
    # breakeven = ceil(100 / 0.40) = 250 + 1
    m = make_metric(net_revenue=50.0, monthly_fee=100.0, total_cost=110.0, tx_count=100)
    result = calculate_roi([m])[0]
    assert result.breakeven_tx_count > 0


def test_roi_zero_cost():
    m = make_metric(net_revenue=100.0, monthly_fee=0.0, total_cost=0.0, tx_count=10)
    result = calculate_roi([m])[0]
    assert result.roi_pct == 9999.0
    assert result.recommendation == "KEEP"
