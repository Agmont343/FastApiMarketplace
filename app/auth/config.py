"""
Конфигурация аутентификации AuthX для Marketplace.

Настраивает JWT-токены, куки и секретный ключ.
"""

from datetime import timedelta

from authx import AuthXConfig

from app.core.config import settings

secret_key = settings.SECRET_KEY
if not secret_key:
    raise ValueError("SECRET_KEY не задан!")

config = AuthXConfig()

config.JWT_SECRET_KEY = secret_key
config.JWT_ACCESS_COOKIE_NAME = "access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]

is_dev = bool(settings.DEBUG)
config.JWT_COOKIE_CSRF_PROTECT = not is_dev
config.JWT_COOKIE_SECURE = not is_dev
config.JWT_COOKIE_HTTP_ONLY = True
config.JWT_COOKIE_SAMESITE = "lax" if is_dev else "strict"

config.JWT_ACCESS_TOKEN_EXPIRES = settings.ACCESS_TOKEN_EXPIRE
config.JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
