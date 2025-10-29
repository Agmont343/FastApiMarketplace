"""
Простые тесты API без сложных фикстур.
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app


def test_app_creation():
    """Тест создания FastAPI приложения."""
    assert app is not None
    assert app.title == "Marketplace API"


def test_health_check():
    """Тест доступности приложения."""
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    """Тест наличия OpenAPI схемы."""
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "info" in data
    assert data["info"]["title"] == "Marketplace API"


def test_auth_endpoints_exist():
    """Тест наличия эндпоинтов аутентификации."""
    client = TestClient(app)
    
    response = client.post("/auth/register/")
    assert response.status_code == 422
    
    response = client.post("/auth/login")
    assert response.status_code == 422
