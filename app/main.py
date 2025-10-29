"""
Основной файл запуска FastAPI приложения Marketplace.

Инициализирует:
- FastAPI приложение
- Роутеры (auth, orders, products)
- Аутентификацию
- Middleware (CORS)
- Подключение к базе данных (создание таблиц через create_all в DEBUG режиме)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.auth import setup_auth
from app.auth.utils import hash_password
from app.core.config import settings
from app.core.logger import logger
from app.database import AsyncSessionLocal, Base, engine
from app.models.user import User, UserRole
from app.routers import auth_router, orders, products


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    try:
        if settings.DEBUG:
            logger.info("[DEV] Создаём таблицы через create_all...")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("[DEV] База данных готова")
        else:
            logger.info(
                "DEBUG=False: пропускаем create_all (используйте Alembic миграции)"
            )

        if settings.SUPERADMIN_EMAIL and settings.SUPERADMIN_PASSWORD:
            async with AsyncSessionLocal() as session:
                email = settings.SUPERADMIN_EMAIL.strip().lower()
                result = await session.execute(select(User).where(User.email == email))
                existing = result.scalars().first()
                if not existing:
                    sa_user = User(
                        email=email,
                        hashed_password=hash_password(settings.SUPERADMIN_PASSWORD),
                        role=UserRole.SUPERADMIN,
                    )
                    session.add(sa_user)
                    await session.commit()
                    logger.info("Суперадмин создан: %s", email)
                else:
                    logger.info("Суперадмин уже существует: %s", email)
    except Exception as e:
        logger.exception("Ошибка при создании таблиц: %s", e)
        raise

    yield

    logger.info("Приложение завершает работу")


app = FastAPI(title="Marketplace API", lifespan=lifespan)

if settings.CORS_ORIGINS_LIST:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS_LIST,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

setup_auth(app)

app.include_router(auth_router.router)
app.include_router(products.router)
app.include_router(orders.router)


logger.info(f"Marketplace API v1.0 starting (DEBUG={settings.DEBUG})")
