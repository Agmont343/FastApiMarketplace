from __future__ import annotations

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderItem(Base):
    """Позиция в заказе (связь заказа и продукта)."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")  # noqa: F821
    product: Mapped["Product"] = relationship(  # noqa: F821
        back_populates="order_items"
    )

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_order_item_quantity_positive"),
        CheckConstraint("price >= 0", name="check_order_item_price_positive"),
        Index("ix_order_items_order_product", "order_id", "product_id"),
    )

    def __repr__(self) -> str:
        """Читаемое представление объекта."""
        return (
            f"<{self.__class__.__name__} id={self.id} "
            f"quantity={self.quantity} price={self.price}>"
        )

    def calculate_price(self):
        """Пересчитывает price как quantity * product.price."""
        if self.product:
            self.price = self.quantity * self.product.price
