"""
Логирование приложения Marketplace.

Используется единый логгер для всего проекта.
Позволяет выводить логи в консоль и при необходимости в файл.
"""

import logging
import sys

logger = logging.getLogger("marketplace")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
