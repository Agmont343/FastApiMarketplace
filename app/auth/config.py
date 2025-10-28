"""
Конфигурация аутентификации AuthX для Marketplace.

Настраивает JWT-токены, куки и секретный ключ.
"""

from datetime import timedelta

from authx import AuthXConfig

from app.core.config import settings

# Получаем секретный ключ из централизованных настроек
secret_key = settings.SECRET_KEY
if not secret_key:
    raise ValueError(
        "SECRET_KEY не задан!"
    )  # критическая ошибка, без ключа auth не работает

# Создаём объект конфигурации AuthX
config = AuthXConfig()

# --- Основные настройки JWT ---
config.JWT_SECRET_KEY = secret_key  # секретный ключ для подписи JWT
config.JWT_ACCESS_COOKIE_NAME = "access_token"  # имя куки с access токеном
config.JWT_TOKEN_LOCATION = ["cookies"]  # где хранится JWT (cookies, headers и т.д.)

# Настройки безопасности cookie зависят от режима DEBUG
is_dev = bool(settings.DEBUG)
config.JWT_COOKIE_CSRF_PROTECT = not is_dev
config.JWT_COOKIE_SECURE = not is_dev
config.JWT_COOKIE_HTTP_ONLY = True
config.JWT_COOKIE_SAMESITE = "lax" if is_dev else "strict"

# --- Время жизни токенов ---
config.JWT_ACCESS_TOKEN_EXPIRES = settings.ACCESS_TOKEN_EXPIRE  # timedelta
config.JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
