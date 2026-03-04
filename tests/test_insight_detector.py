import pytest

from app.schemas.metrics import PaymentMethodMetrics
from app.services.insight_detector import detect_insights


def make_metric(**kwargs) -> PaymentMethodMetrics:
    defaults = dict(
        payment_method_id="test_method",
        name="Test Method",
        type="card",
        country="MX",
        currency="MXN",
        total_transactions=60,
        approved_count=48,
        tpv_local=10000.0,
        tpv_usd=580.0,
        net_revenue_usd=14.5,
        approval_rate=0.80,
        chargeback_rate=0.01,
        avg_transaction_value_local=208.0,
        avg_settlement_days=2.0,
        revenue_contribution_pct=15.0,
        net_cost_efficiency_usd=10.0,
        monthly_fee_usd=0.0,
        total_cost_usd=4.5,
        activity_status="active",
    )
    defaults.update(kwargs)
    return PaymentMethodMetrics(**defaults)


def test_zombie_detection():
    metrics = [
        make_metric(
            payment_method_id="zombie_cl",
            country="CL",
            total_transactions=5,
            activity_status="dormant",
            monthly_fee_usd=200.0,
        )
    ]
    insights = detect_insights(metrics)
    zombie = [i for i in insights if i.insight_type == "zombie"]
    assert len(zombie) == 1
    assert zombie[0].payment_method_id == "zombie_cl"


def test_zombie_no_fee_no_flag():
    metrics = [
        make_metric(
            payment_method_id="free_zombie",
            country="MX",
            total_transactions=3,
            activity_status="dormant",
            monthly_fee_usd=0.0,
        )
    ]
    insights = detect_insights(metrics)
    zombie = [i for i in insights if i.insight_type == "zombie"]
    assert len(zombie) == 0


def test_hidden_gem_detection():
    # Country has two methods: hidden gem has high approval & revenue contrib, low tx count
    hidden = make_metric(
        payment_method_id="spei_mx",
        country="MX",
        total_transactions=25,
        approval_rate=0.92,
        revenue_contribution_pct=12.0,
        activity_status="declining",
    )
    regular = make_metric(
        payment_method_id="visa_mx",
        country="MX",
        total_transactions=80,
        approval_rate=0.75,
        revenue_contribution_pct=88.0,
        activity_status="active",
    )
    insights = detect_insights([hidden, regular])
    gems = [i for i in insights if i.insight_type == "hidden_gem"]
    assert any(i.payment_method_id == "spei_mx" for i in gems)


def test_performance_alert():
    # Country avg = (0.40 + 0.80) / 2 = 0.60; threshold = 0.60 - 0.15 = 0.45
    # oxxo at 0.40 is below 0.45 → alert fires
    alert = make_metric(
        payment_method_id="oxxo_mx",
        country="MX",
        total_transactions=60,
        approval_rate=0.40,
    )
    normal = make_metric(
        payment_method_id="visa_mx",
        country="MX",
        total_transactions=80,
        approval_rate=0.80,
    )
    insights = detect_insights([alert, normal])
    alerts = [i for i in insights if i.insight_type == "performance_alert"]
    assert any(i.payment_method_id == "oxxo_mx" for i in alerts)


def test_cost_trap_detection():
    metrics = [
        make_metric(
            payment_method_id="webpay_cl",
            country="CL",
            total_transactions=5,
            net_revenue_usd=2.0,
            net_cost_efficiency_usd=-198.0,  # revenue < costs
        )
    ]
    insights = detect_insights(metrics)
    traps = [i for i in insights if i.insight_type == "cost_trap"]
    assert len(traps) == 1
    assert traps[0].value == -198.0


def test_filter_by_insight_type():
    metrics = [
        make_metric(
            payment_method_id="zombie_cl",
            country="CL",
            total_transactions=5,
            activity_status="dormant",
            monthly_fee_usd=100.0,
        )
    ]
    insights = detect_insights(metrics, insight_type_filter="zombie")
    assert all(i.insight_type == "zombie" for i in insights)

    insights_none = detect_insights(metrics, insight_type_filter="hidden_gem")
    assert len(insights_none) == 0
