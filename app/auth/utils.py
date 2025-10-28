"""
Утилиты для работы с паролями.

Содержит:
- Хэширование пароля
- Проверку пароля с хэшем
"""

from passlib.context import CryptContext

# ---------------------------
# Настройка контекста PassLib для bcrypt
# ---------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Хэширует пароль с помощью bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли пароль с хэшем."""
    return pwd_context.verify(plain_password, hashed_password)
