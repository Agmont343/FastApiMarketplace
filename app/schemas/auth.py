from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserLogin(BaseModel):
    """Схема для входа пользователя."""

    email: EmailStr = Field(..., description="Электронная почта пользователя")
    password: str = Field(..., min_length=8, description="Пароль (минимум 8 символов)")


class UserRegister(UserLogin):
    """Схема для регистрации пользователя (наследует UserLogin)."""

    pass


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя."""

    id: int = Field(..., description="Уникальный идентификатор пользователя")
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    role: UserRole = Field(..., description="Роль пользователя")

    model_config = ConfigDict(from_attributes=True)
