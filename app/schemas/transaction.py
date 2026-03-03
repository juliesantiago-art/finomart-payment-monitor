from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class TransactionIngest(BaseModel):
    payment_method_id: str
    country: str
    amount: float
    currency: str
    status: str
    chargeback_flag: bool = False
    settlement_speed_days: Optional[int] = None
    fx_spread_pct: Optional[float] = None
    installment_count: int = 1
    created_at: datetime

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"approved", "declined", "pending", "refunded"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class TransactionResponse(BaseModel):
    id: int
    payment_method_id: str
    country: str
    amount: float
    currency: str
    usd_amount: float
    net_revenue_usd: float
    status: str
    chargeback_flag: bool
    settlement_speed_days: Optional[int]
    fx_spread_pct: Optional[float]
    installment_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    inserted: int
    message: str
