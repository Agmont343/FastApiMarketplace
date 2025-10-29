"""
Инициализация системы аутентификации (AuthX).

Содержит:
- создание экземпляра AuthX с конфигом
- функцию setup_auth для интеграции с FastAPI приложением
"""

from authx import AuthX

from .config import config

auth = AuthX(config=config)


def setup_auth(app):
    """
    Подключает обработку ошибок AuthX к FastAPI приложению.

    Args:
        app: экземпляр FastAPI
    """
    auth.handle_errors(app)
