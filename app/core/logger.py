"""
Логирование приложения Marketplace.

Используется единый логгер для всего проекта.
Позволяет выводить логи в консоль и при необходимости в файл.
"""

import logging
import sys

# ---------------------------
# Создаём основной логгер
# ---------------------------
logger = logging.getLogger("marketplace")
logger.setLevel(logging.INFO)  # Можно DEBUG для разработки

# ---------------------------
# Формат логов
# ---------------------------
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------
# Консольный хэндлер (stdout)
# ---------------------------
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ---------------------------
# 🔹 Пример: файл логов
# ---------------------------
# file_handler = logging.FileHandler("marketplace.log")
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler)
