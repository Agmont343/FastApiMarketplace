from __future__ import annotations

import enum
from datetime import datetime
from typing import List

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderStatus(str, enum.Enum):
    """Статусы заказа."""

    CREATED = "created"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(Base):
    """Модель заказа пользователя."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    delivery_address: Mapped[str] = mapped_column(String(255), nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.CREATED, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), index=True
    )

    # Связи
    user: Mapped["User"] = relationship(back_populates="orders")  # noqa: F821
    items: Mapped[List["OrderItem"]] = relationship(  # noqa: F821
        back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("total_price >= 0", name="check_order_total_price_positive"),
        Index("ix_orders_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        """Читаемое представление объекта."""
        return (
            f"<{self.__class__.__name__} id={self.id} "
            f"user_id={self.user_id} status={self.status}>"
        )

    def calculate_total(self):
        """Подсчитать общую сумму заказа на основе позиций."""
        self.total_price = sum(item.price for item in self.items)
