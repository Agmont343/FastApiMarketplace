"""
Вспомогательные функции для CRUD операций.

Содержит:
- Проверку существования объекта и генерацию HTTP 404
"""

from typing import Any, Optional

from fastapi import HTTPException, status


async def get_or_404(item: Optional[Any], item_name: str = "Item"):
    """Возвращает объект или кидает HTTPException 404, если не найден."""
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{item_name} не найден"
        )
    return item
