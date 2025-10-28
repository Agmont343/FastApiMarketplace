from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    """Модель товара в маркетплейсе."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Связь с элементами заказов
    order_items: Mapped[List["OrderItem"]] = relationship(  # noqa: F821
        back_populates="product", cascade="all, delete-orphan"
    )

    # Ограничения и индекс
    __table_args__ = (
        CheckConstraint("price >= 0", name="check_product_price_positive"),
        Index("ix_products_name_price", "name", "price"),
    )

    def __repr__(self) -> str:
        """Читаемое представление объекта."""
        return (
            f"<{self.__class__.__name__} id={self.id} "
            f"name={self.name} price={self.price}>"
        )
