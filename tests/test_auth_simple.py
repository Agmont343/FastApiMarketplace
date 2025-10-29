"""
Простые тесты аутентификации без сложных фикстур.
"""

import pytest
import sys
import os
import httpx
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole


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


@pytest.mark.asyncio
async def test_register_user():
    """Тест регистрации нового пользователя."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session = TestingSessionLocal()
    try:
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            test_user_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            response = await client.post("/auth/register/", json=test_user_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == test_user_data["email"]
            assert "id" in data
            assert "hashed_password" not in data
    finally:
        await session.close()
        app.dependency_overrides.clear()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_register_duplicate_email():
    """Тест регистрации с дублирующимся email."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session = TestingSessionLocal()
    try:
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            test_user_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            await client.post("/auth/register/", json=test_user_data)
            
            response = await client.post("/auth/register/", json=test_user_data)
            
            assert response.status_code == 400
            assert "уже зарегистрирован" in response.json()["detail"]
    finally:
        await session.close()
        app.dependency_overrides.clear()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_login_success():
    """Тест успешного входа."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session = TestingSessionLocal()
    try:
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            test_user_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            await client.post("/auth/register/", json=test_user_data)
            
            response = await client.post("/auth/login", json=test_user_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == test_user_data["email"]
    finally:
        await session.close()
        app.dependency_overrides.clear()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Тест входа с неверными данными."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session = TestingSessionLocal()
    try:
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            test_user_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            response = await client.post("/auth/login", json=test_user_data)
            
            assert response.status_code == 401
            assert "Неверные учётные данные" in response.json()["detail"]
    finally:
        await session.close()
        app.dependency_overrides.clear()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_get_current_user_unauthorized():
    """Тест получения текущего пользователя без авторизации."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session = TestingSessionLocal()
    try:
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/auth/me")
            
            assert response.status_code == 401
    finally:
        await session.close()
        app.dependency_overrides.clear()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_logout():
    """Тест выхода из системы."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session = TestingSessionLocal()
    try:
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            test_user_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            await client.post("/auth/register/", json=test_user_data)
            
            response = await client.post("/auth/logout")
            
            assert response.status_code == 200
            assert "logged out" in response.json()["msg"]
    finally:
        await session.close()
        app.dependency_overrides.clear()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

