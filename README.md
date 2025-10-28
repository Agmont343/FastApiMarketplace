## Marketplace API (FastAPI)

Небольшой учебный маркетплейс: FastAPI + SQLAlchemy Async + JWT (AuthX) + Alembic.

[![CI](https://img.shields.io/github/actions/workflow/status/Agmont343/marketplace/docker.yml?label=CI&logo=github)](https://github.com/Agmont343/marketplace/actions/workflows/docker.yml)
![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.118.0-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-CA2C2C)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

### Запуск локально (DEV)
1) Создайте файл `.env` по образцу ниже (см. раздел «env.example»).
2) Установите зависимости:
```
pip install -r requirements.txt
```
3) Запустите приложение (Swagger будет по `/docs`):
```
uvicorn app.main:app --reload
```

В DEV-режиме (`DEBUG=true`) таблицы создаются автоматически на старте с помощью `create_all` (для быстрого теста через Swagger).

### Docker

Проект полностью контейнеризован:

```bash
# Запуск всех сервисов
docker-compose up

# Запуск только приложения
docker build -t marketplace .
docker run -p 8000:8000 marketplace
```

### Требования
- Python 3.11+
- PostgreSQL 14+

### Переход на миграции Alembic (для PROD)
Когда убедитесь, что всё работает локально:
1) Установите `DEBUG=false` в `.env` — авто-`create_all` будет отключён.
2) Сгенерируйте миграции:
```
alembic revision --autogenerate -m "init"
```
3) Примените миграции:
```
alembic upgrade head
```

Alembic использует синхронный DSN из `DATABASE_URL`, а приложение — async-DSN, генерируемый автоматически (`postgresql+asyncpg://...`).

### Пример .env
```
# Синхронный DSN (для Alembic и базовой валидации)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/marketplace

# Секретный ключ (замените на безопасный)
SECRET_KEY=change_me_to_a_strong_secret

# DEV режим включает create_all и мягкие cookie-настройки
DEBUG=true

# Разрешённые источники CORS (через запятую)
BACKEND_CORS_ORIGINS=http://localhost:3000
```

### Аутентификация и безопасность
- В DEV: cookie Secure=False, SameSite=lax, CSRF выключен.
- В PROD: Secure=True, SameSite=strict, CSRF включён (управляется `DEBUG`).

### Основные команды
- Запуск DEV: `uvicorn app.main:app --reload`
- Запуск с Docker: `docker-compose up`
- Создание миграции: `alembic revision --autogenerate -m "msg"`
- Применение миграций: `alembic upgrade head`
- Запуск тестов: `pytest` (21 тест покрывают модели, API и аутентификацию)
- Линтинг: `flake8 app`
- Форматирование: `black app`
- Проверка безопасности: `safety check`

### Структура
- `app/routers` — маршруты (`products`, `orders`, `auth`).
- `app/crud` — слой доступа к данным.
- `app/models` — SQLAlchemy-модели.
- `app/schemas` — Pydantic-схемы.
- `app/auth` — JWT/AuthX конфиг и utils.
- `app/core/config.py` — настройки (Pydantic Settings).
- `alembic/` — миграции.

### CI/CD

Настроен автоматический пайплайн GitHub Actions:
- ✅ Тестирование (pytest)
- ✅ Линтинг (flake8, black, isort)
- ✅ Проверка безопасности (safety, bandit)
- ✅ Сборка Docker образа
- ✅ Публикация в Docker Hub

### Тестирование

Проект включает 21 тест, покрывающий:
- **Модели данных**: создание пользователей, продуктов, заказов и позиций заказов
- **API эндпоинты**: проверка доступности основных маршрутов
- **Аутентификация**: регистрация, вход, выход, проверка авторизации

```bash
# Запуск всех тестов
pytest

# Запуск с подробным выводом
pytest -v

# Запуск конкретного теста
pytest tests/test_auth_simple.py::test_register_user -v
```

### Разработка

```bash
# Установка зависимостей для разработки
pip install -r requirements.txt

# Запуск тестов
pytest

# Форматирование кода
black app
isort app

# Проверка стиля кода
flake8 app
```

### Лицензия
MIT License
