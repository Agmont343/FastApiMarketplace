from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    """Схема для создания продукта."""

    name: str = Field(
        ..., min_length=3, max_length=100, description="Название продукта"
    )
    price: float = Field(..., gt=0, description="Цена продукта, >0")


class ProductResponse(BaseModel):
    """Схема ответа для продукта."""

    id: int = Field(..., description="Уникальный идентификатор продукта")
    name: str = Field(..., description="Название продукта")
    price: float = Field(..., description="Цена продукта")
    in_stock: bool = Field(..., description="Продукт в наличии")

    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):
    """Схема для обновления продукта (частичные изменения)."""

    name: Optional[str] = Field(
        None, min_length=3, max_length=100, description="Новое название продукта"
    )
    price: Optional[float] = Field(None, gt=0, description="Новая цена продукта")
    in_stock: Optional[bool] = Field(None, description="В наличии или нет")
