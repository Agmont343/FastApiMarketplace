"""
Маршруты аутентификации Marketplace.

Реализует JWT-аутентификацию через библиотеку AuthX:
- Регистрация нового пользователя с указанием роли
- Вход с установкой access/refresh токенов в cookies
- Обновление access токена по refresh токену
- Получение текущего пользователя
- Выход (очистка cookies)
- Эндпоинты для администраторов и проверки ролей
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.future import select

from app.auth import auth
from app.auth.utils import hash_password, verify_password
from app.core.security import admin_required as admin_required_dep
from app.core.security import role_required
from app.crud.user import get_user_by_email, get_user_or_404
from app.database import SessionDep
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.schemas.auth import UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================


def _create_and_set_access_cookie(
    user_id: int, response: Response, fresh: bool = False
) -> str:
    """Создаёт access токен и устанавливает его в HttpOnly cookie."""
    token = auth.create_access_token(uid=str(user_id), fresh=fresh)
    auth.set_access_cookies(token, response=response)
    return token


def _create_and_set_refresh_cookie(user_id: int, response: Response) -> str:
    """Создаёт refresh токен и устанавливает его в HttpOnly cookie."""
    token = auth.create_refresh_token(uid=str(user_id))
    auth.set_refresh_cookies(token, response=response)
    return token


# =========================================================
# РОУТЫ АУТЕНТИФИКАЦИИ
# =========================================================


@router.post(
    "/register/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создаёт нового пользователя и устанавливает JWT в HttpOnly cookie.",
    response_description="Возвращает данные зарегистрированного пользователя.",
)
async def register(user: UserRegister, session: SessionDep, response: Response):
    """Регистрирует нового пользователя и устанавливает токены в cookie."""
    existing = await get_user_by_email(session, user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегистрирован",
        )

    hashed = hash_password(user.password)
    email = user.email.strip().lower()
    db_user = User(email=email, hashed_password=hashed, role=UserRole.USER)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    _create_and_set_access_cookie(db_user.id, response, fresh=True)
    _create_and_set_refresh_cookie(db_user.id, response)
    response.set_cookie(key="logged_in", value="true", httponly=False, max_age=3600)

    return db_user


@router.post(
    "/login",
    response_model=UserResponse,
    summary="Вход в систему",
    description="Аутентифицирует пользователя и устанавливает JWT в HttpOnly cookie.",
    response_description="Возвращает данные вошедшего пользователя.",
)
async def login(user: UserLogin, session: SessionDep, response: Response):
    """Выполняет вход пользователя и устанавливает токены в cookie."""
    email = user.email.strip().lower()
    db_user = await get_user_by_email(session, email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учётные данные",
        )

    _create_and_set_access_cookie(db_user.id, response, fresh=True)
    _create_and_set_refresh_cookie(db_user.id, response)
    response.set_cookie(key="logged_in", value="true", httponly=False, max_age=3600)
    return db_user


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Получить текущего пользователя",
    description="Возвращает данные пользователя, извлечённые из access токена.",
    response_description="Данные текущего пользователя (id и email).",
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Возвращает данные текущего пользователя из access токена."""
    return current_user


@router.post(
    "/refresh",
    summary="Обновить access токен",
    description=(
        "Создаёт новый access токен из refresh токена и устанавливает его в cookie."
    ),
    response_description="Сообщение об успешном обновлении access токена.",
)
async def refresh_token(
    response: Response,
    refresh_payload: Optional[Any] = auth.REFRESH_REQUIRED,
):
    """Обновляет access токен по refresh токену."""
    if not refresh_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh токен отсутствует или недействителен",
        )

    sub = getattr(refresh_payload, "sub", None) or refresh_payload

    try:
        user_id = int(sub)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный формат subject в refresh токене",
        )

    _create_and_set_access_cookie(user_id, response)
    return {"msg": "Access токен успешно обновлён"}


@router.post(
    "/logout",
    summary="Выйти из системы",
    description="Удаляет access и refresh cookie, разлогинивает пользователя.",
    response_description="Сообщение об успешном выходе из системы.",
)
async def logout(response: Response):
    """Выполняет выход пользователя и удаляет все токены из cookie."""
    auth.unset_access_cookies(response)
    auth.unset_refresh_cookies(response)
    response.delete_cookie("logged_in")
    return {"msg": "logged out"}


# ------------------- ЭНДПОИНТЫ ТОЛЬКО ДЛЯ АДМИНА -------------------


class AssignRoleRequest(BaseModel):
    id: int = Field(..., description="ID пользователя")
    role: UserRole = UserRole.ADMIN


superadmin_required = role_required([UserRole.SUPERADMIN])
admin_required = admin_required_dep


@router.get(
    "/admin/users",
    response_model=List[UserResponse],
    summary="Список всех пользователей",
    description="Только для администратора. Возвращает всех пользователей.",
)
async def get_all_users(
    session: SessionDep,
    _: User = Depends(admin_required),
):
    """Возвращает всех пользователей (только для админа)."""
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users


@router.post(
    "/admin/assign-role",
    summary="Назначить роль пользователю",
    description=(
        "Только для суперадмина. Позволяет назначить одну из ролей пользователю."
    ),
)
async def assign_role(
    payload: AssignRoleRequest,
    session: SessionDep,
    _: User = Depends(superadmin_required),
):
    """Изменяет роль пользователя (только для суперадмина)."""

    if payload.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя назначать роль SUPERADMIN через этот эндпоинт",
        )

    user = await get_user_or_404(session, payload.id)

    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя менять роль суперадмина",
        )

    if user.role == payload.role:
        return {"msg": f"Пользователь {user.email} уже имеет роль {payload.role.value}"}

    user.role = payload.role
    await session.commit()
    await session.refresh(user)

    return UserResponse.model_validate(user)
