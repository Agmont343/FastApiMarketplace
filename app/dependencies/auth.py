"""Зависимости для аутентификации и получения текущего пользователя."""

from typing import Any, Optional

from fastapi import HTTPException, status

from app.auth import auth
from app.crud.user import get_user_or_404
from app.database import SessionDep
from app.models.user import User


async def get_current_user(
    session: SessionDep,
    token_payload: Optional[Any] = auth.ACCESS_REQUIRED,
) -> User:
    """Возвращает текущего пользователя из access токена или кидает HTTPException."""
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен отсутствует или недействителен",
        )

    sub = getattr(token_payload, "sub", None) or token_payload

    try:
        user_id = int(sub)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный формат subject в токене",
        )

    return await get_user_or_404(session, user_id)
