"""
Маршруты для управления товарами (Products).

Содержит CRUD-операции:
- Создание, получение, обновление и удаление товаров
- Фильтрация по наличию и диапазону цен
"""

from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query, status

from app.crud.product import (
    create_product,
    delete_product,
    get_product_by_id,
    list_products,
    update_product,
)
from app.database import SessionDep
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(
    prefix="/products",
    tags=["Товары"],
    responses={404: {"description": "Товар не найден"}},
)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый товар",
    description="Создаёт новый товар в системе. Требуется указать название и цену.",
    response_description="Информация о созданном товаре.",
)
async def create_new_product(session: SessionDep, product: ProductCreate):
    """Создаёт новый товар"""
    db_product = await create_product(session, product)
    return db_product


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить товар по ID",
    description="Возвращает информацию о товаре по его уникальному идентификатору.",
    response_description="Информация о найденном товаре.",
)
async def read_product(
    session: SessionDep, product_id: int = Path(..., description="ID товара")
):
    """Возвращает товар по ID"""
    db_product = await get_product_by_id(session, product_id)
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден"
        )
    return db_product


@router.get(
    "/",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Список товаров",
    description="Возвращает список товаров с фильтрацией по наличию и диапазону цен.",
    response_description="Список найденных товаров.",
)
async def get_product_list(
    session: SessionDep,
    in_stock: Optional[bool] = Query(None, description="Только товары в наличии"),
    min_price: Optional[float] = Query(None, description="Минимальная цена"),
    max_price: Optional[float] = Query(None, description="Максимальная цена"),
):
    """Возвращает список товаров с фильтрацией"""
    products = await list_products(session, in_stock, min_price, max_price)
    return products


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить товар",
    description="Обновляет данные существующего товара по ID.",
    response_description="Информация об обновлённом товаре.",
)
async def patch_product(
    session: SessionDep,
    product_id: int = Path(..., description="ID продукта для обновления"),
    update_data: ProductUpdate = Body(...),
):
    """Обновляет данные товара"""
    updated_product = await update_product(session, product_id, update_data)
    return updated_product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить товар",
    description="Удаляет товар по ID.",
    response_description="Сообщение об успешном удалении.",
)
async def remove_product(
    session: SessionDep,
    product_id: int = Path(..., description="ID продукта для удаления"),
):
    """Удаляет товар по ID и возвращает сообщение с названием товара."""
    db_product = await get_product_by_id(session, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    await delete_product(session, product_id)
    return {"message": f"Товар '{db_product.name}' успешно удалён"}
