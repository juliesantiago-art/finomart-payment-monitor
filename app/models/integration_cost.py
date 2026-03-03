from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IntegrationCost(Base):
    __tablename__ = "integration_costs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_method_id: Mapped[str] = mapped_column(String(64), ForeignKey("payment_methods.id"), nullable=False)
    monthly_fee_usd: Mapped[float] = mapped_column(Float, default=0.0)
    per_transaction_fee_usd: Mapped[float] = mapped_column(Float, default=0.0)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    payment_method: Mapped["PaymentMethod"] = relationship("PaymentMethod", back_populates="costs")
