"""
CRUD операции для пользователей (User) в Marketplace.

Содержит:
- Получение пользователя по ID или email
- Получение пользователя с проверкой существования (404)
"""

from typing import Optional

from sqlalchemy import select

from app.crud.utils import get_or_404
from app.database import SessionDep
from app.models.user import User


async def get_user_by_id(session: SessionDep, user_id: int) -> Optional[User]:
    """Возвращает пользователя по ID или None, если не найден."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_user_or_404(session: SessionDep, user_id: int) -> User:
    """Возвращает пользователя по ID или выбрасывает HTTPException 404."""
    user = await get_user_by_id(session, user_id)
    return await get_or_404(user, item_name="Пользователь")


async def get_user_by_email(session: SessionDep, email: str) -> Optional[User]:
    """Возвращает пользователя по email или None, если не найден."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_user_by_email_or_404(session: SessionDep, email: str) -> User:
    """Возвращает пользователя по email или выбрасывает HTTPException 404."""
    user = await get_user_by_email(session, email)
    return await get_or_404(user, item_name=f"Пользователь с email {email}")
