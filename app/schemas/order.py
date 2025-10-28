from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field, confloat, conint

from app.models.order import OrderStatus
from app.schemas.product import ProductResponse


class OrderItemCreate(BaseModel):
    """Схема для создания позиции заказа."""

    product_id: int = Field(..., description="ID продукта")
    quantity: conint(gt=0) = Field(..., description="Количество товара (>0)")


class OrderCreate(BaseModel):
    """Схема для создания заказа."""

    items: List[OrderItemCreate] = Field(..., description="Список товаров в заказе")
    delivery_address: str = Field(
        ..., min_length=10, max_length=255, description="Адрес доставки"
    )


class OrderItemResponse(BaseModel):
    """Схема ответа для позиции заказа."""

    id: int = Field(..., description="ID позиции заказа")
    product_id: int = Field(..., description="ID продукта")
    quantity: int = Field(..., description="Количество товара")
    price: confloat(gt=0) = Field(..., description="Цена позиции (>0)")
    product: ProductResponse

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """Схема ответа для заказа."""

    id: int = Field(..., description="Уникальный идентификатор заказа")
    user_id: int = Field(..., description="ID пользователя")
    items: List[OrderItemResponse] = Field(..., description="Список позиций заказа")
    delivery_address: str = Field(..., description="Адрес доставки")
    status: OrderStatus = Field(..., description="Статус заказа")
    created_at: datetime = Field(..., description="Дата создания заказа")

    model_config = ConfigDict(from_attributes=True)
