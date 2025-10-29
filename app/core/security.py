"""
Функции безопасности для проекта Marketplace.

Содержит проверки прав доступа пользователей, такие как проверка ролей.
"""

from typing import List

from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole


def role_required(allowed_roles: List[UserRole]):
    """Создаёт зависимость для проверки ролей пользователя."""

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения действия.",
            )
        return current_user

    return dependency


admin_required = role_required([UserRole.ADMIN, UserRole.SUPERADMIN])
