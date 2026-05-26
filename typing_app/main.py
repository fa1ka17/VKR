"""
Точка входа в приложение.

Запуск:
    python main.py

Зависимости (установить один раз):
    pip install pygments mypy
"""
from __future__ import annotations

import sys

# Проверяем версию Python
if sys.version_info < (3, 10):
    print(
        f"Требуется Python 3.10 или выше. "
        f"Текущая версия: {sys.version_info.major}.{sys.version_info.minor}",
        file=sys.stderr,
    )
    sys.exit(1)

from ui.main_window import MainWindow


def main() -> None:
    window = MainWindow()
    window.run()


if __name__ == "__main__":
    main()
