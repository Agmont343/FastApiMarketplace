"""
Маршруты для работы с заказами (Orders).

Содержит:
- CRUD операций с заказами
- Управление позициями заказов (OrderItem)
- Получение заказов текущего пользователя
"""

from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.crud.order import add_item_to_order, clear_order_items, create_order
from app.crud.order import delete_order as crud_delete_order
from app.crud.order import (
    get_order_or_404,
    list_orders,
    recalculate_total,
    update_item_quantity,
    update_order_status,
)
from app.database import SessionDep
from app.dependencies.auth import get_current_user
from app.models.order import Order as OrderModel
from app.models.order import OrderStatus
from app.models.order_item import OrderItem
from app.models.user import User
from app.schemas.order import OrderCreate, OrderItemCreate, OrderResponse

router = APIRouter(
    prefix="/orders",
    tags=["Заказы"],
    responses={404: {"description": "Заказ не найден"}},
)

# Константа для подгрузки позиций и продуктов при выборке заказов
ORDER_EAGER_LOAD = [selectinload(OrderModel.items).selectinload(OrderItem.product)]


# ------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ -------------------


async def get_user_order(
    session: SessionDep,
    order_id: int,
    current_user: User = Depends(get_current_user),
) -> OrderModel:
    """Загружает заказ текущего пользователя с подгрузкой позиций и продуктов."""
    order = await get_order_or_404(session, order_id, options=ORDER_EAGER_LOAD)
    if order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order


# ------------------- МАРШРУТЫ -------------------


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый заказ",
    description="Создает новый заказ с товарами и адресом доставки.",
    response_description="Созданный заказ с позициями и total_price",
)
async def create_new_order(
    session: SessionDep,
    order: OrderCreate,
    current_user: User = Depends(get_current_user),
) -> OrderModel:
    """Создаёт заказ для текущего пользователя с полной загрузкой items и product."""
    db_order = await create_order(session, current_user.id, order)
    return await get_order_or_404(session, db_order.id, options=ORDER_EAGER_LOAD)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Получить заказ по ID",
    description="Возвращает информацию о заказе, включая позиции и товары.",
)
async def read_order(order: OrderModel = Depends(get_user_order)) -> OrderModel:
    """Возвращает заказ текущего пользователя."""
    return order


@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="Список заказов пользователя",
    description="Возвращает список всех заказов текущего пользователя.",
)
async def get_orders(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> List[OrderModel]:
    """Возвращает все заказы текущего пользователя с подгрузкой items и product."""
    return await list_orders(session, current_user.id, options=ORDER_EAGER_LOAD)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Обновить статус заказа",
    description="Позволяет изменить статус заказа.",
)
async def patch_order_status(
    session: SessionDep,
    new_status: OrderStatus = Body(..., description="Новый статус заказа"),
    order: OrderModel = Depends(get_user_order),
) -> OrderModel:
    """Обновляет статус заказа текущего пользователя."""
    updated = await update_order_status(session, order.id, new_status)
    return await get_order_or_404(session, updated.id, options=ORDER_EAGER_LOAD)


@router.delete(
    "/{order_id}",
    summary="Удалить заказ",
    description="Удаляет заказ. Только заказ в статусе 'created' может быть удален.",
)
async def delete_order_route(
    session: SessionDep,
    order: OrderModel = Depends(get_user_order),
) -> JSONResponse:
    """Удаляет заказ текущего пользователя, если статус 'created'."""
    if order.status != OrderStatus.CREATED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Можно удалить только заказ в статусе 'created'",
        )
    await crud_delete_order(session, order.id)
    await session.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Заказ {order.id} успешно удалён"},
    )


@router.post(
    "/{order_id}/items",
    response_model=OrderResponse,
    summary="Добавить товар в заказ",
    description="Добавляет выбранный товар в заказ с указанным количеством.",
)
async def add_order_item(
    session: SessionDep,
    order: OrderModel = Depends(get_user_order),
    item: OrderItemCreate = Body(...),
) -> OrderModel:
    """Добавляет товар в заказ и пересчитывает total_price."""
    await add_item_to_order(session, order, item.product_id, item.quantity)
    await session.commit()
    return await get_order_or_404(session, order.id, options=ORDER_EAGER_LOAD)


@router.delete(
    "/{order_id}/items/{product_id}",
    summary="Удалить товар из заказа",
    description="Удаляет выбранный товар из заказа по product_id.",
)
async def delete_item_from_order(
    session: SessionDep,
    order: OrderModel = Depends(get_user_order),
    product_id: int = Path(..., description="ID продукта для удаления из заказа"),
) -> JSONResponse:
    """Удаляет товар из заказа и пересчитывает total_price."""
    stmt = (
        select(OrderItem)
        .where(OrderItem.order_id == order.id, OrderItem.product_id == product_id)
        .options(selectinload(OrderItem.product))
    )
    result = await session.execute(stmt)
    db_item = result.scalars().first()

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар с product_id={product_id} не найден в заказе",
        )

    product_name = db_item.product.name
    await session.delete(db_item)
    await recalculate_total(session, order)
    await session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Товар '{product_name}' успешно удалён из заказа {order.id}"
        },
    )


@router.patch(
    "/{order_id}/items/{product_id}",
    response_model=OrderResponse,
    summary="Изменить количество товара в заказе",
    description="Обновляет количество товара в заказе по product_id.",
)
async def patch_item_quantity(
    session: SessionDep,
    order: OrderModel = Depends(get_user_order),
    product_id: int = Path(..., description="ID товара"),
    new_quantity: int = Body(
        ..., gt=0, embed=True, description="Новое количество товара"
    ),
) -> OrderModel:
    """Изменяет количество товара в заказе и пересчитывает total_price."""
    await update_item_quantity(session, order, product_id, new_quantity)
    await session.commit()
    return await get_order_or_404(session, order.id, options=ORDER_EAGER_LOAD)


@router.delete(
    "/{order_id}/items",
    response_model=OrderResponse,
    summary="Очистить все позиции заказа",
    description="Удаляет все товары из заказа и сбрасывает total_price.",
)
async def delete_all_items(
    session: SessionDep,
    order: OrderModel = Depends(get_user_order),
) -> JSONResponse:
    """Удаляет все позиции заказа текущего пользователя."""
    await clear_order_items(session, order)
    await session.commit()
    return JSONResponse(
        status_code=200,
        content={"message": f"Все позиции заказа {order.id} успешно удалены"},
    )
