import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.product import Product


async def main():
    async with AsyncSessionLocal() as session:
        new_product = Product(name="Test Product", price=19.99)
        session.add(new_product)
        await session.commit()
        await session.refresh(new_product)

        print(f"Добавлен продукт: {new_product}")

        result = await session.execute(select(Product))
        products = result.scalars().all()
        print("Все продукты в базе:")
        for p in products:
            print(p)


if __name__ == "__main__":
    asyncio.run(main())
