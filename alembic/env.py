import sys
import os
import asyncio
import logging

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base
from app.core.config import settings

from app.models import product, order, order_item, user

config = context.config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alembic.env")

target_metadata = Base.metadata

ASYNC_DATABASE_URL = str(settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Генерация SQL миграций без подключения к базе."""
    context.configure(
        url=ASYNC_DATABASE_URL.replace("asyncpg", "psycopg2"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online_async() -> None:
    """Применение миграций в async-режиме."""
    connectable = create_async_engine(
        ASYNC_DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(run_migrations)

    await connectable.dispose()


def run_migrations(connection):
    """Синхронный запуск миграций (через run_sync)."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запуск async миграций через asyncio."""
    asyncio.run(run_migrations_online_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()