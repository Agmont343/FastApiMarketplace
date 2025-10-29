import sys
import os
import asyncio
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem

async def main():
    async with AsyncSessionLocal() as session:
        user = await session.get(User, 1)
        if not user:
            print("Пользователь с id=1 не найден, создайте сначала пользователя!")
            return

        product = await session.get(Product, 1)
        if not product:
            print("Продукт с id=1 не найден!")
            return

        new_order = Order(
            user_id=user.id,
            delivery_address="Test address",
            status=OrderStatus.CREATED
        )

        order_item = OrderItem(
            product_id=product.id,
            quantity=1,
            price=product.price
        )
        new_order.items.append(order_item)
        new_order.calculate_total()

        session.add(new_order)
        await session.commit()
        await session.refresh(new_order)

        stmt = select(Order).options(selectinload(Order.items)).where(Order.id == new_order.id)
        result = await session.execute(stmt)
        order_with_items = result.scalar_one()

        print(f"Создан заказ: {order_with_items}")
        print("Все позиции заказа:")
        for item in order_with_items.items:
            print(item)

if __name__ == "__main__":
    asyncio.run(main())
