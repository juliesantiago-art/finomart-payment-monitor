from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # card/wallet/bank_transfer/cash/bnpl
    country: Mapped[str] = mapped_column(String(4), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    transactions: Mapped[list] = relationship("Transaction", back_populates="payment_method", lazy="select")
    costs: Mapped[list] = relationship("IntegrationCost", back_populates="payment_method", lazy="select")
