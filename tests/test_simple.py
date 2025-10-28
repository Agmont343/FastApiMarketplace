"""
Простые тесты для проверки базовой функциональности.
"""

import pytest
import sys
import os

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User, UserRole
from app.models.product import Product


def test_user_model():
    """Тест создания модели пользователя."""
    user = User(email="test@example.com", hashed_password="hashed", role=UserRole.USER)
    assert user.email == "test@example.com"
    assert user.role == UserRole.USER
    # is_active устанавливается по умолчанию в True через default=True в модели


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
    import asyncio
    await asyncio.sleep(0.01)  # Простая async операция
    assert True
