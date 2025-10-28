"""
CRUD операции для продуктов (Product) в Marketplace.

Содержит:
- Создание, чтение, обновление и удаление продуктов
- Вспомогательные функции для поиска продукта
"""

from typing import List, Optional

from sqlalchemy import select

from app.crud.utils import get_or_404
from app.database import SessionDep
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

# ------------------- ВСПОМОГАТЕЛЬНЫЕ -------------------


async def get_product_by_id(session: SessionDep, product_id: int) -> Optional[Product]:
    """Возвращает продукт по ID или None."""
    stmt = select(Product).where(Product.id == product_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_product_or_404(session: SessionDep, product_id: int) -> Product:
    """Возвращает продукт по ID или 404, если не найден."""
    product = await get_product_by_id(session, product_id)
    return await get_or_404(product, item_name=f"Продукт id={product_id}")


# ------------------- CRUD -------------------


async def create_product(session: SessionDep, product_data: ProductCreate) -> Product:
    """Создаёт новый продукт."""
    db_product = Product(**product_data.dict())
    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product


async def list_products(
    session: SessionDep,
    in_stock: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[Product]:
    """Возвращает список продуктов с фильтрацией по наличию и цене."""
    stmt = select(Product)

    if in_stock is not None:
        stmt = stmt.where(Product.in_stock == in_stock)
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)

    result = await session.execute(stmt)
    return result.scalars().all()


async def update_product(
    session: SessionDep, product_id: int, update_data: ProductUpdate
) -> Product:
    """Обновляет продукт."""
    db_product = await get_product_or_404(session, product_id)
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(db_product, field, value)
    await session.commit()
    await session.refresh(db_product)
    return db_product


async def delete_product(session: SessionDep, product_id: int) -> None:
    """Удаляет продукт по ID."""
    db_product = await get_product_or_404(session, product_id)
    await session.delete(db_product)
    await session.commit()
