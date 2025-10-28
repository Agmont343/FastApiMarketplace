"""
CRUD операции для заказов (Order) в Marketplace.

Содержит:
- Создание, чтение, обновление и удаление заказов
- Управление позициями (OrderItem)
- Вспомогательные функции (проверка редактируемости, пересчёт total_price)
"""

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.crud.utils import get_or_404
from app.database import SessionDep
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate

# ------------------- ВСПОМОГАТЕЛЬНЫЕ -------------------


def ensure_order_editable(order: Order) -> None:
    """Проверяет, что заказ можно редактировать (только в статусе CREATED)."""
    if order.status != OrderStatus.CREATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя редактировать закрытый заказ",
        )


async def recalculate_total(session: SessionDep, order: Order) -> None:
    """Пересчитывает общую сумму заказа (total_price)."""
    result = await session.execute(
        select(OrderItem).where(OrderItem.order_id == order.id)
    )
    items = result.scalars().all()
    order.total_price = sum(item.price for item in items)
    await session.flush()
    await session.refresh(order)


async def get_products_by_ids(
    session: SessionDep, product_ids: List[int]
) -> dict[int, Product]:
    """Возвращает словарь продуктов по ID. Проверяет, что все найдены."""
    stmt = select(Product).where(Product.id.in_(product_ids))
    result = await session.execute(stmt)
    products = {p.id: p for p in result.scalars().all()}

    missing = set(product_ids) - set(products.keys())
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Не найдены продукты: {missing}",
        )
    return products


async def get_order_item(
    session: SessionDep, order_id: int, product_id: int
) -> Optional[OrderItem]:
    stmt = select(OrderItem).where(
        OrderItem.order_id == order_id,
        OrderItem.product_id == product_id,
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_order_item_or_404(
    session: SessionDep, order_id: int, product_id: int
) -> OrderItem:
    """Возвращает позицию заказа или 404, если не найдена."""
    item = await get_order_item(session, order_id, product_id)
    return await get_or_404(item, item_name=f"Товар id={product_id} не найден в заказе")


async def get_order_by_id(
    session: SessionDep,
    order_id: int,
    options: Optional[list] = None,
    for_update: bool = False,
) -> Optional[Order]:
    """Возвращает заказ по ID или None."""
    stmt_options = [selectinload(Order.items).selectinload(OrderItem.product)]
    if options:
        stmt_options.extend(options)

    stmt = select(Order).where(Order.id == order_id).options(*stmt_options)
    if for_update:
        stmt = stmt.with_for_update(of=Order)

    result = await session.execute(stmt)
    return result.scalars().first()


async def get_order_or_404(
    session: SessionDep,
    order_id: int,
    options: Optional[list] = None,
    for_update: bool = False,
) -> Order:
    """Возвращает заказ или 404."""
    order = await get_order_by_id(
        session, order_id, options=options, for_update=for_update
    )
    return await get_or_404(order, item_name=f"Заказ id={order_id}")


# ------------------- CRUD -------------------


async def create_order(
    session: SessionDep, user_id: int, order_data: OrderCreate
) -> Order:
    """Создаёт заказ и рассчитывает его сумму."""
    if not order_data.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заказ должен содержать хотя бы одну позицию",
        )

    product_ids = [item.product_id for item in order_data.items]
    products = await get_products_by_ids(session, product_ids)

    db_order = Order(
        user_id=user_id,
        delivery_address=order_data.delivery_address,
        total_price=0.0,
        status=OrderStatus.CREATED,
    )
    session.add(db_order)
    await session.flush()

    for item in order_data.items:
        product = products[item.product_id]

        if not product.in_stock:
            raise HTTPException(
                status_code=400, detail=f"Продукт id={item.product_id} отсутствует"
            )
        if item.quantity <= 0:
            raise HTTPException(
                status_code=400, detail="Количество товара должно быть > 0"
            )

        db_item = OrderItem(
            order_id=db_order.id,
            product_id=product.id,
            quantity=item.quantity,
            price=product.price * item.quantity,
        )
        session.add(db_item)

    await session.flush()
    await recalculate_total(session, db_order)
    await session.commit()

    stmt = (
        select(Order)
        .where(Order.id == db_order.id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def list_orders(
    session: SessionDep, user_id: int, options: Optional[list] = None
) -> List[Order]:
    """Возвращает список заказов пользователя (новые сверху)."""
    if options is None:
        options = [selectinload(Order.items).selectinload(OrderItem.product)]

    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .options(*options)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def update_order_status(
    session: SessionDep, order_id: int, new_status: OrderStatus
) -> Order:
    """Обновляет статус заказа."""
    order = await get_order_or_404(session, order_id, for_update=True)
    order.status = new_status
    await session.commit()
    await session.refresh(order)
    return order


async def delete_order(session: SessionDep, order_id: int) -> None:
    """Удаляет заказ по ID."""
    order = await get_order_or_404(session, order_id, for_update=True)
    await session.delete(order)
    await session.commit()


async def add_item_to_order(
    session: SessionDep, order: Order, product_id: int, quantity: int
) -> OrderItem:
    """Добавляет товар в заказ или увеличивает количество существующего."""
    ensure_order_editable(order)

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Количество должно быть > 0")

    products = await get_products_by_ids(session, [product_id])
    product = products[product_id]

    stmt = select(OrderItem).where(
        OrderItem.order_id == order.id, OrderItem.product_id == product_id
    )
    result = await session.execute(stmt)
    existing_item = result.scalars().first()

    if existing_item:
        existing_item.quantity += quantity
        existing_item.price = product.price * existing_item.quantity
        db_item = existing_item
    else:
        db_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            price=product.price * quantity,
        )
        session.add(db_item)

    await recalculate_total(session, order)
    await session.commit()
    return db_item


async def remove_item_from_order(
    session: SessionDep, order: Order, product_id: int
) -> None:
    """Удаляет товар из заказа."""
    ensure_order_editable(order)
    db_item = await get_order_item_or_404(session, order.id, product_id)
    await session.delete(db_item)
    await recalculate_total(session, order)
    await session.commit()


async def update_item_quantity(
    session: SessionDep, order: Order, product_id: int, new_quantity: int
) -> OrderItem:
    """Обновляет количество товара в заказе."""
    ensure_order_editable(order)

    if new_quantity <= 0:
        raise HTTPException(status_code=400, detail="Количество должно быть > 0")

    db_item = await get_order_item_or_404(session, order.id, product_id)
    db_item.quantity = new_quantity
    db_item.price = db_item.product.price * new_quantity

    await recalculate_total(session, order)
    await session.commit()
    return db_item


async def clear_order_items(session: SessionDep, order: Order) -> None:
    """Удаляет все позиции из заказа."""
    ensure_order_editable(order)
    await session.execute(delete(OrderItem).where(OrderItem.order_id == order.id))
    await recalculate_total(session, order)
    await session.commit()
