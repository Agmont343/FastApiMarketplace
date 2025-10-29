import sys
import os
import asyncio
from sqlalchemy.future import select

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.auth.utils import hash_password

async def main():
    async with AsyncSessionLocal() as session:
        new_user = User(
            email="testuser@example.com",
            hashed_password=hash_password("testpassword123"),
            is_active=True,
            role=UserRole.USER
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        print(f"Создан пользователь: {new_user}")

        result = await session.execute(select(User))
        users = result.scalars().all()
        print("Все пользователи в базе:")
        for u in users:
            print(u)

if __name__ == "__main__":
    asyncio.run(main())
