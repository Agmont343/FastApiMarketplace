"""
Настройка подключения к базе данных с SQLAlchemy Async.
Определяет движок, сессию, базовый класс моделей и зависимость для FastAPI.
"""

from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ---------------------------
# Настройка движка базы данных
# ---------------------------
engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=settings.DEBUG,  # Логирование SQL-запросов в режиме DEBUG
)

# ---------------------------
# Асинхронная сессия
# ---------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # ORM объекты остаются доступными после commit
)


# ---------------------------
# Базовый класс для моделей
# ---------------------------
class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy.

    Все модели должны наследоваться от этого класса.
    """

    pass


# ---------------------------
# Зависимости для FastAPI
# ---------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Генератор асинхронной сессии для эндпоинтов FastAPI.

    Используется через Depends, чтобы получать session в роутерах.
    """
    async with AsyncSessionLocal() as session:
        yield session


# Типизированная зависимость для удобного использования в роутерах
SessionDep: type = Annotated[AsyncSession, Depends(get_db)]
