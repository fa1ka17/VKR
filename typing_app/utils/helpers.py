"""Вспомогательные функции для форматирования и работы со строками кода."""
from __future__ import annotations

import sys


def python_version_str() -> str:
    """Возвращает строку вида '3.11.4'."""
    v = sys.version_info
    return f"{v.major}.{v.minor}.{v.micro}"


def format_issues_plain(issues: list) -> str:  # type: ignore[type-arg]
    """
    Форматирует список TypeIssue в читаемый текст для копирования.
    Используется при сохранении/экспорте вывода.
    """
    if not issues:
        return "✓ Ошибок типов не обнаружено."
    lines: list[str] = []
    for issue in issues:
        prefix = {"error": "❌", "warning": "⚠", "note": "ℹ"}.get(
            issue.severity, "·"
        )
        code_part = f" [{issue.code}]" if issue.code else ""
        lines.append(
            f"{prefix} Строка {issue.line}:{issue.col}{code_part}  {issue.message}"
        )
    return "\n".join(lines)


def truncate(text: str, max_len: int = 200) -> str:
    """Обрезает текст до max_len символов, добавляя '…'."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"
