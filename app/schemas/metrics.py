from typing import Optional
from pydantic import BaseModel


class PaymentMethodMetrics(BaseModel):
    payment_method_id: str
    name: str
    type: str
    country: str
    currency: str
    total_transactions: int
    approved_count: int
    tpv_local: float
    tpv_usd: float
    net_revenue_usd: float
    approval_rate: float
    chargeback_rate: float
    avg_transaction_value_local: float
    avg_settlement_days: Optional[float]
    revenue_contribution_pct: float
    net_cost_efficiency_usd: float
    monthly_fee_usd: float
    total_cost_usd: float
    activity_status: str  # active / declining / dormant


class MetricsResponse(BaseModel):
    country: Optional[str]
    date_from: Optional[str]
    date_to: Optional[str]
    method_type: Optional[str]
    methods: list[PaymentMethodMetrics]
