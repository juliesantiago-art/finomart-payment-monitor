from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_method_id: Mapped[str] = mapped_column(String(64), ForeignKey("payment_methods.id"), nullable=False)
    country: Mapped[str] = mapped_column(String(4), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)          # local currency
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    usd_amount: Mapped[float] = mapped_column(Float, nullable=False)       # computed at ingest
    net_revenue_usd: Mapped[float] = mapped_column(Float, default=0.0)    # computed at ingest
    status: Mapped[str] = mapped_column(String(16), nullable=False)        # approved/declined/pending/refunded
    chargeback_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    settlement_speed_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fx_spread_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    installment_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    payment_method: Mapped["PaymentMethod"] = relationship("PaymentMethod", back_populates="transactions")
