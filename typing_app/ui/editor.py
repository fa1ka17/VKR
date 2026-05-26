"""
Модуль редактора кода.

Реализует виджет CodeEditor на базе tk.Text с подсветкой синтаксиса Python
через библиотеку Pygments.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont

try:
    from pygments import lex
    from pygments.lexers import PythonLexer
    from pygments.token import (
        Comment, Error, Keyword, Name, Number, Operator,
        Punctuation, String, Token,
    )
    _PYGMENTS_AVAILABLE = True
except ImportError:
    _PYGMENTS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Цветовая схема токенов (тёмная тема)
# ---------------------------------------------------------------------------

_TOKEN_COLORS: dict[str, str] = {
    "Token.Keyword":                   "#cc7832",
    "Token.Keyword.Constant":          "#cc7832",
    "Token.Keyword.Declaration":       "#cc7832",
    "Token.Keyword.Namespace":         "#cc7832",
    "Token.Name.Builtin":              "#8888c6",
    "Token.Name.Builtin.Pseudo":       "#8888c6",
    "Token.Name.Class":                "#ffc66d",
    "Token.Name.Function":             "#ffc66d",
    "Token.Name.Decorator":            "#bbb529",
    "Token.Literal.String":            "#6a8759",
    "Token.Literal.String.Doc":        "#629755",
    "Token.Literal.Number":            "#6897bb",
    "Token.Literal.Number.Integer":    "#6897bb",
    "Token.Literal.Number.Float":      "#6897bb",
    "Token.Comment":                   "#808080",
    "Token.Comment.Single":            "#808080",
    "Token.Operator":                  "#a9b7c6",
    "Token.Punctuation":               "#a9b7c6",
    "Token.Error":                     "#ff0000",
}


class CodeEditor(tk.Frame):
    """
    Редактор кода с подсветкой синтаксиса Python.

    Использует tk.Text + Pygments для раскраски токенов.
    При недоступности Pygments работает как обычный текстовый редактор.
    """

    def __init__(self, master: tk.Widget, **kwargs: object) -> None:
        bg = "#2b2b2b"
        super().__init__(master, bg=bg)

        # --- Шрифт ---
        mono_font = tkfont.Font(family="Courier New", size=11)

        # --- Виджет Text ---
        self._text = tk.Text(
            self,
            font=mono_font,
            bg=bg,
            fg="#a9b7c6",
            insertbackground="#ffffff",
            selectbackground="#214283",
            selectforeground="#ffffff",
            relief=tk.FLAT,
            borderwidth=0,
            padx=8,
            pady=6,
            undo=True,
            wrap=tk.NONE,
            **{k: v for k, v in kwargs.items()
               if k not in ("width", "height")},
        )

        # --- Горизонтальная полоса прокрутки ---
        hscroll = tk.Scrollbar(self, orient=tk.HORIZONTAL,
                               command=self._text.xview)
        vscroll = tk.Scrollbar(self, orient=tk.VERTICAL,
                               command=self._text.yview)
        self._text.config(xscrollcommand=hscroll.set,
                          yscrollcommand=vscroll.set)

        hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Теги подсветки ---
        if _PYGMENTS_AVAILABLE:
            self._setup_tags()

        # --- Привязки ---
        self._text.bind("<Tab>", self._on_tab)
        self._text.bind("<KeyRelease>", self._schedule_highlight)
        self._highlight_job: str | None = None

    # -----------------------------------------------------------------------
    # Публичный API
    # -----------------------------------------------------------------------

    def get_text(self) -> str:
        """Возвращает текущее содержимое редактора."""
        return self._text.get("1.0", tk.END)

    def set_text(self, content: str) -> None:
        """Заменяет содержимое редактора и применяет подсветку."""
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", content)
        self._apply_highlighting()

    def set_readonly(self, readonly: bool) -> None:
        """Переводит редактор в режим только для чтения."""
        state = tk.DISABLED if readonly else tk.NORMAL
        self._text.config(state=state)

    def highlight_line(self, line: int, color: str = "#3d1a1a") -> None:
        """Выделяет фон указанной строки (для отображения ошибок)."""
        self._text.tag_add(f"err_line_{line}", f"{line}.0", f"{line}.end")
        self._text.tag_config(f"err_line_{line}", background=color)

    def clear_line_highlights(self) -> None:
        """Сбрасывает подсветку строк с ошибками."""
        for tag in self._text.tag_names():
            if tag.startswith("err_line_"):
                self._text.tag_delete(tag)

    def jump_to_line(self, line: int) -> None:
        """Перемещает курсор к указанной строке."""
        self._text.see(f"{line}.0")
        self._text.mark_set(tk.INSERT, f"{line}.0")
        self._text.focus_set()

    # -----------------------------------------------------------------------
    # Внутренние методы
    # -----------------------------------------------------------------------

    def _setup_tags(self) -> None:
        """Создаёт теги форматирования для каждого типа токена Pygments."""
        for token_str, color in _TOKEN_COLORS.items():
            self._text.tag_config(token_str, foreground=color)

    def _schedule_highlight(self, _event: tk.Event | None = None) -> None:  # type: ignore[type-arg]
        """Планирует применение подсветки через 200 мс (дебаунс)."""
        if self._highlight_job:
            self._text.after_cancel(self._highlight_job)
        self._highlight_job = self._text.after(200, self._apply_highlighting)

    def _apply_highlighting(self) -> None:
        """Применяет подсветку синтаксиса через Pygments."""
        if not _PYGMENTS_AVAILABLE:
            return

        content = self._text.get("1.0", tk.END)

        # Снимаем все токенизационные теги
        for tag in self._text.tag_names():
            if tag.startswith("Token."):
                self._text.tag_remove(tag, "1.0", tk.END)

        self._text.mark_set("range_start", "1.0")
        for token_type, value in lex(content, PythonLexer()):
            tag = str(token_type)
            self._text.mark_set(
                "range_end",
                f"range_start + {len(value)}c",
            )
            if tag in _TOKEN_COLORS:
                self._text.tag_add(tag, "range_start", "range_end")
            self._text.mark_set("range_start", "range_end")

    def _on_tab(self, event: tk.Event) -> str:  # type: ignore[type-arg]
        """Заменяет Tab четырьмя пробелами."""
        self._text.insert(tk.INSERT, "    ")
        return "break"
