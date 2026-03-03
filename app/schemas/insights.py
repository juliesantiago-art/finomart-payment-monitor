from typing import Optional
from pydantic import BaseModel


class Insight(BaseModel):
    payment_method_id: str
    payment_method_name: str
    country: str
    insight_type: str  # zombie / hidden_gem / performance_alert / cost_trap
    metric: str
    value: float
    recommended_action: str


class InsightsResponse(BaseModel):
    total: int
    insights: list[Insight]


class TrendPoint(BaseModel):
    period: str
    tx_count: int
    net_revenue_usd: float
    approval_rate: float
    chargeback_rate: float


class MethodTrend(BaseModel):
    payment_method_id: str
    name: str
    country: str
    flags: list[str]
    weekly_trend: list[TrendPoint]
    monthly_trend: list[TrendPoint]


class TrendsResponse(BaseModel):
    methods: list[MethodTrend]


class ROIResult(BaseModel):
    payment_method_id: str
    name: str
    country: str
    net_revenue_usd: float
    total_cost_usd: float
    roi_pct: float
    recommendation: str  # KEEP / NEGOTIATE / REMOVE
    breakeven_tx_count: int


class ROIResponse(BaseModel):
    methods: list[ROIResult]


class MarketGap(BaseModel):
    country: str
    method_id: str
    method_name: str
    method_type: str
    popularity_score: int
    estimated_revenue_uplift_usd: float


class GapsResponse(BaseModel):
    total_gaps: int
    gaps: list[MarketGap]


class PortfolioSummary(BaseModel):
    total_methods: int
    active_count: int
    declining_count: int
    dormant_count: int
    total_net_revenue_usd: float
    total_cost_usd: float
    total_roi_pct: float
    avg_approval_rate: float
    zombie_count: int
    hidden_gem_count: int
    cost_trap_count: int
    performance_alert_count: int
