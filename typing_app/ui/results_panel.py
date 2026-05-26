"""
Модуль панели результатов.

Отображает диагностические сообщения mypy и вывод выполненного кода
с цветовой кодировкой: красный — ошибки, жёлтый — предупреждения, серый — note.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

from core.type_checker import TypeIssue


class ResultsPanel(tk.Frame):
    """
    Прокручиваемая панель для отображения результатов анализа типов.

    Поддерживает:
    - Цветовую кодировку сообщений (error/warning/note)
    - Кликабельные ссылки на номера строк
    - Переключение между вкладками «Mypy» и «Вывод»
    """

    def __init__(
        self,
        master: tk.Widget,
        on_line_click: Callable[[int], None] | None = None,
    ) -> None:
        super().__init__(master, bg="#3c3f41")
        self._on_line_click = on_line_click
        self._build()

    # -----------------------------------------------------------------------
    # Построение виджета
    # -----------------------------------------------------------------------

    def _build(self) -> None:
        mono = tkfont.Font(family="Courier New", size=10)
        label_font = tkfont.Font(family="Segoe UI", size=9)

        # Заголовок
        header = tk.Frame(self, bg="#3c3f41")
        header.pack(fill=tk.X, padx=4, pady=(4, 0))
        tk.Label(
            header, text="Результаты", bg="#3c3f41", fg="#bbbbbb",
            font=label_font,
        ).pack(side=tk.LEFT)

        # Кнопки переключения вкладок
        self._tab_var = tk.StringVar(value="mypy")
        for label, val in [("mypy", "mypy"), ("Вывод кода", "run")]:
            rb = tk.Radiobutton(
                header, text=label, variable=self._tab_var, value=val,
                command=self._on_tab_switch,
                bg="#3c3f41", fg="#bbbbbb", selectcolor="#4b4b4b",
                font=label_font, relief=tk.FLAT,
                activebackground="#3c3f41", activeforeground="#ffffff",
            )
            rb.pack(side=tk.LEFT, padx=6)

        # Текстовый виджет + прокрутка
        frame = tk.Frame(self, bg="#2b2b2b")
        frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._text = tk.Text(
            frame,
            font=mono,
            bg="#2b2b2b",
            fg="#bbbbbb",
            state=tk.DISABLED,
            relief=tk.FLAT,
            borderwidth=0,
            padx=6,
            pady=4,
            wrap=tk.WORD,
            cursor="arrow",
        )
        scroll = tk.Scrollbar(frame, command=self._text.yview)
        self._text.config(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._text.pack(fill=tk.BOTH, expand=True)

        # Теги цветов
        self._text.tag_config("error",   foreground="#ff6b6b")
        self._text.tag_config("warning", foreground="#ffd166")
        self._text.tag_config("note",    foreground="#888888")
        self._text.tag_config("ok",      foreground="#6bcb77")
        self._text.tag_config("header",  foreground="#a0c4ff", font=(
            "Segoe UI", 10, "bold"
        ))
        self._text.tag_config("link",    foreground="#69b4ff",
                               underline=True)
        self._text.tag_bind("link", "<Button-1>", self._on_link_click)
        self._text.tag_bind("link", "<Enter>",
                            lambda _: self._text.config(cursor="hand2"))
        self._text.tag_bind("link", "<Leave>",
                            lambda _: self._text.config(cursor="arrow"))

        # Хранилища данных для двух вкладок
        self._mypy_issues: list[TypeIssue] = []
        self._run_output: str = ""
        self._line_map: dict[str, int] = {}   # имя тега → номер строки кода

    # -----------------------------------------------------------------------
    # Публичный API
    # -----------------------------------------------------------------------

    def show_mypy_result(
        self,
        issues: list[TypeIssue],
        ok: bool,
    ) -> None:
        """Сохраняет результат mypy и обновляет панель, если выбрана вкладка mypy."""
        self._mypy_issues = issues
        if self._tab_var.get() == "mypy":
            self._render_mypy(issues, ok)

    def show_run_output(self, stdout: str, stderr: str, timed_out: bool) -> None:
        """Сохраняет и отображает вывод выполнения кода."""
        parts: list[str] = []
        if stdout:
            parts.append(stdout)
        if stderr:
            parts.append(f"[stderr]\n{stderr}")
        if timed_out:
            parts.append("⚠ Превышен лимит времени выполнения (10 с).")
        self._run_output = "\n".join(parts) if parts else "(нет вывода)"
        if self._tab_var.get() == "run":
            self._render_run()

    def clear(self) -> None:
        """Очищает панель."""
        self._mypy_issues = []
        self._run_output = ""
        self._write("")

    # -----------------------------------------------------------------------
    # Внутренние методы
    # -----------------------------------------------------------------------

    def _on_tab_switch(self) -> None:
        if self._tab_var.get() == "mypy":
            self._render_mypy(self._mypy_issues, len(self._mypy_issues) == 0)
        else:
            self._render_run()

    def _render_mypy(self, issues: list[TypeIssue], ok: bool) -> None:
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._line_map = {}

        self._text.insert(tk.END, "— Результаты mypy —\n", "header")

        if ok and not issues:
            self._text.insert(tk.END, "\n✓ Ошибок типов не обнаружено.\n", "ok")
        else:
            for issue in issues:
                prefix = {"error": "❌", "warning": "⚠", "note": "ℹ"}.get(
                    issue.severity, "·"
                )
                # Кликабельная ссылка на строку
                link_tag = f"link_{issue.line}_{id(issue)}"
                self._line_map[link_tag] = issue.line

                self._text.insert(tk.END, f"\n{prefix} Строка ")
                self._text.insert(tk.END, str(issue.line), (issue.severity, link_tag, "link"))
                code_part = f" [{issue.code}]" if issue.code else ""
                self._text.insert(
                    tk.END,
                    f":{issue.col}{code_part}\n  {issue.message}\n",
                    issue.severity,
                )

        self._text.config(state=tk.DISABLED)

    def _render_run(self) -> None:
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.insert(tk.END, "— Вывод выполнения —\n", "header")
        self._text.insert(tk.END, "\n" + self._run_output)
        self._text.config(state=tk.DISABLED)

    def _write(self, text: str) -> None:
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        if text:
            self._text.insert(tk.END, text)
        self._text.config(state=tk.DISABLED)

    def _on_link_click(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        """Обрабатывает клик по номеру строки."""
        if self._on_line_click is None:
            return
        for tag in self._text.tag_names(tk.CURRENT):
            if tag in self._line_map:
                self._on_line_click(self._line_map[tag])
                break
