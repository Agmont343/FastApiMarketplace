"""
Простые тесты для проверки базовой функциональности без сложных фикстур.
"""

import pytest
import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User, UserRole
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.database import Base


# Тестовая база данных (SQLite в памяти)
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def test_user_model():
    """Тест создания модели пользователя."""
    user = User(email="test@example.com", hashed_password="hashed", role=UserRole.USER)
    assert user.email == "test@example.com"
    assert user.role == UserRole.USER


def test_product_model():
    """Тест создания модели продукта."""
    product = Product(name="Test Product", price=9.99)
    assert product.name == "Test Product"
    assert product.price == 9.99


def test_user_role_enum():
    """Тест enum ролей пользователя."""
    assert UserRole.USER == "user"
    assert UserRole.ADMIN == "admin"
    assert UserRole.SUPERADMIN == "superadmin"
    assert UserRole.MANAGER == "manager"


@pytest.mark.asyncio
async def test_async_basic():
    """Базовый тест async функциональности."""
    await asyncio.sleep(0.01)  # Простая async операция
    assert True


@pytest.mark.asyncio
async def test_create_user_in_db():
    """Тест создания пользователя в базе данных."""
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаем сессию
    session = TestingSessionLocal()
    try:
        user = User(email="testuser@example.com", hashed_password="hashed", role=UserRole.USER)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        assert user.id is not None
        assert user.email == "testuser@example.com"
        assert user.role == UserRole.USER
    finally:
        await session.close()
        # Очищаем таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_product_in_db():
    """Тест создания продукта в базе данных."""
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаем сессию
    session = TestingSessionLocal()
    try:
        product = Product(name="Test Product", price=9.99)
        session.add(product)
        await session.commit()
        await session.refresh(product)

        assert product.id is not None
        assert product.name == "Test Product"
        assert product.price == 9.99
    finally:
        await session.close()
        # Очищаем таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_order_with_items():
    """Тест создания заказа с позициями."""
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаем сессию
    session = TestingSessionLocal()
    try:
        # Создаем пользователя
        user = User(email="order@test.com", hashed_password="hashed", role=UserRole.USER)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Создаем продукты
        p1 = Product(name="P1", price=10.0)
        p2 = Product(name="P2", price=5.0)
        session.add_all([p1, p2])
        await session.commit()
        await session.refresh(p1)
        await session.refresh(p2)

        # Создаем заказ
        order = Order(user_id=user.id, delivery_address="Somewhere", status=OrderStatus.CREATED)
        session.add(order)
        await session.commit()
        await session.refresh(order)

        # Создаем позиции заказа
        oi1 = OrderItem(order_id=order.id, product_id=p1.id, quantity=2, price=20.0)
        oi2 = OrderItem(order_id=order.id, product_id=p2.id, quantity=1, price=5.0)
        session.add_all([oi1, oi2])
        await session.commit()

        # Проверяем
        total = sum(item.price for item in [oi1, oi2])
        assert total == 25.0
        assert order.user_id == user.id
        assert order.status == OrderStatus.CREATED
    finally:
        await session.close()
        # Очищаем таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
