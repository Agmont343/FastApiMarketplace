"""
Конфигурация приложения Marketplace через Pydantic BaseSettings.

Поддерживает:
- Настройки базы данных
- JWT / аутентификацию
- Общие настройки (DEBUG)
- CORS
"""

from datetime import timedelta

from pydantic import Field
from pydantic.networks import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Настройки приложения Marketplace.

    Значения подтягиваются из .env или переменных окружения системы.
    """

    # --- База данных ---
    DATABASE_URL: PostgresDsn  # Проверка на корректный формат URL PostgreSQL

    # --- Общие ---
    DEBUG: bool = False  # Включает логирование SQL-запросов и debug-логи

    # --- JWT / Auth ---
    SECRET_KEY: str  # Секретный ключ для подписи токенов
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # Access токен по умолчанию 7 дней
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Refresh токен по умолчанию 7 дней

    # --- Bootstrap супер-админа ---
    SUPERADMIN_EMAIL: str | None = None
    SUPERADMIN_PASSWORD: str | None = None

    # --- CORS ---
    BACKEND_CORS_ORIGINS: str = Field(
        default="", description="Список разрешённых фронтенд URL через запятую"
    )

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """
        Возвращает async-DSN для SQLAlchemy (postgresql+asyncpg://...).

        Допускает входящие схемы "postgresql://" и "postgres://" и
        преобразует их к "postgresql+asyncpg://" для работы с create_async_engine.
        """
        raw = str(self.DATABASE_URL)
        if raw.startswith("postgresql+asyncpg://"):
            return raw
        if raw.startswith("postgresql://"):
            return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
        if raw.startswith("postgres://"):
            return raw.replace("postgres://", "postgresql+asyncpg://", 1)
        # По умолчанию просто добавляем драйвер, если схема нестандартная
        return raw if "+" in raw else raw.replace("://", "+asyncpg://", 1)

    @property
    def ACCESS_TOKEN_EXPIRE(self) -> timedelta:
        """
        Таймаут access-токена в виде timedelta.
        Используется для генерации JWT.
        """
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        """
        Парсит BACKEND_CORS_ORIGINS в список URL.
        """
        if not self.BACKEND_CORS_ORIGINS:
            return []
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Создаём глобальный объект с настройками для всего проекта
settings = Settings()
