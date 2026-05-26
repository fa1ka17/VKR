"""
Модуль панели упражнений.

Реализует интерактивный учебный модуль: список заданий, редактор кода,
кнопки «Проверить» / «Подсказка» / «Решение», панель обратной связи
и статистику прогресса.
"""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from core.exercises import ALL_EXERCISES, LEVEL_COLORS, LEVEL_LABELS, Exercise
from core.type_checker import CheckResult, check_exercise, run_mypy
from ui.editor import CodeEditor


class ExercisePanel(tk.Frame):
    """
    Панель с набором учебных упражнений.

    Паттерн наблюдатель реализован через привязку ListboxSelect:
    выбор задания в боковом списке вызывает on_exercise_selected,
    который обновляет все дочерние компоненты.
    """

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, bg="#2b2b2b")
        self._exercises = ALL_EXERCISES
        self._current_index: int = 0
        self._hint_index: int = 0                   # текущий индекс подсказки
        self._completed: set[str] = set()            # id выполненных упражнений
        self._no_hint_completed: set[str] = set()    # выполнено без подсказок
        self._hint_used: bool = False                # использована ли подсказка в текущем

        self._build()
        self._load_exercise(0)

    # -----------------------------------------------------------------------
    # Построение интерфейса
    # -----------------------------------------------------------------------

    def _build(self) -> None:
        seg_font = tkfont.Font(family="Segoe UI", size=10)
        bold_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        # ── Боковая панель ────────────────────────────────────────────────
        sidebar = tk.Frame(self, bg="#3c3f41", width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(4, 0), pady=4)
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="Упражнения", bg="#3c3f41", fg="#bbbbbb",
            font=bold_font,
        ).pack(anchor=tk.W, padx=8, pady=(8, 4))

        list_frame = tk.Frame(sidebar, bg="#3c3f41")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=4)

        self._listbox = tk.Listbox(
            list_frame,
            bg="#313335",
            fg="#bbbbbb",
            selectbackground="#214283",
            selectforeground="#ffffff",
            font=seg_font,
            relief=tk.FLAT,
            borderwidth=0,
            activestyle="none",
        )
        lb_scroll = tk.Scrollbar(list_frame, command=self._listbox.yview)
        self._listbox.config(yscrollcommand=lb_scroll.set)
        lb_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._listbox.pack(fill=tk.BOTH, expand=True)

        for ex in self._exercises:
            level_label = LEVEL_LABELS.get(ex.level, ex.level)
            self._listbox.insert(tk.END, f"  {ex.title}\n  [{level_label}]")

        self._listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        # Статистика прогресса
        self._progress_var = tk.StringVar(value="")
        tk.Label(
            sidebar, textvariable=self._progress_var,
            bg="#3c3f41", fg="#6bcb77", font=seg_font,
            justify=tk.LEFT, wraplength=200,
        ).pack(anchor=tk.W, padx=8, pady=(4, 8))

        # ── Основная рабочая область ──────────────────────────────────────
        main = tk.Frame(self, bg="#2b2b2b")
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                  padx=4, pady=4)

        paned = ttk.PanedWindow(main, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Левая колонка: описание + редактор + кнопки
        left = tk.Frame(paned, bg="#2b2b2b")
        paned.add(left, weight=3)

        self._desc_text = tk.Text(
            left,
            font=seg_font,
            bg="#2b2b2b",
            fg="#bbbbbb",
            height=8,
            state=tk.DISABLED,
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=6,
            pady=4,
        )
        self._desc_text.pack(fill=tk.X, pady=(0, 4))

        tk.Label(left, text="Ваш код:", bg="#2b2b2b", fg="#888888",
                 font=seg_font).pack(anchor=tk.W)

        self._editor = CodeEditor(left, height=14)
        self._editor.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(left, bg="#2b2b2b")
        btn_frame.pack(fill=tk.X, pady=(4, 0))

        btn_style = dict(
            bg="#4b5c78", fg="#ffffff", font=bold_font,
            relief=tk.FLAT, padx=10, pady=4,
            activebackground="#5a6f90", activeforeground="#ffffff",
            cursor="hand2",
        )

        self._check_btn = tk.Button(
            btn_frame, text="✓ Проверить",
            command=self._on_check, **btn_style
        )
        self._check_btn.pack(side=tk.LEFT, padx=(0, 6))

        self._hint_btn = tk.Button(
            btn_frame, text="💡 Подсказка",
            command=self._on_hint, **btn_style
        )
        self._hint_btn.pack(side=tk.LEFT, padx=(0, 6))

        self._solution_btn = tk.Button(
            btn_frame, text="👁 Решение",
            command=self._on_show_solution, **btn_style
        )
        self._solution_btn.pack(side=tk.LEFT)

        # Правая колонка: подсказки + результаты проверки
        right = tk.Frame(paned, bg="#2b2b2b")
        paned.add(right, weight=2)

        tk.Label(right, text="Подсказки:", bg="#2b2b2b", fg="#888888",
                 font=seg_font).pack(anchor=tk.W)

        hint_frame = tk.Frame(right, bg="#2b2b2b")
        hint_frame.pack(fill=tk.X)

        self._hint_text = tk.Text(
            hint_frame,
            font=seg_font,
            bg="#313335",
            fg="#ffd166",
            height=5,
            state=tk.DISABLED,
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=6,
            pady=4,
        )
        self._hint_text.pack(fill=tk.BOTH)

        tk.Label(right, text="Результат:", bg="#2b2b2b", fg="#888888",
                 font=seg_font).pack(anchor=tk.W, pady=(8, 0))

        self._feedback_text = tk.Text(
            right,
            font=seg_font,
            bg="#313335",
            fg="#bbbbbb",
            state=tk.DISABLED,
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=6,
            pady=4,
        )
        self._feedback_text.pack(fill=tk.BOTH, expand=True)

        self._feedback_text.tag_config("ok",      foreground="#6bcb77")
        self._feedback_text.tag_config("error",   foreground="#ff6b6b")
        self._feedback_text.tag_config("missing", foreground="#ffd166")
        self._feedback_text.tag_config("mypy_ok", foreground="#6bcb77")
        self._feedback_text.tag_config("mypy_err",foreground="#ff6b6b")

    # -----------------------------------------------------------------------
    # Обработчики событий
    # -----------------------------------------------------------------------

    def _on_listbox_select(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        sel = self._listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx != self._current_index:
            self._load_exercise(idx)

    def _on_check(self) -> None:
        """Запускает двухэтапную проверку в отдельном потоке."""
        self._check_btn.config(state=tk.DISABLED, text="Проверяю…")
        source = self._editor.get_text().rstrip("\n")
        ex = self._exercises[self._current_index]
        threading.Thread(
            target=self._run_check,
            args=(source, ex),
            daemon=True,
        ).start()

    def _run_check(self, source: str, ex: Exercise) -> None:
        """Выполняется в фоновом потоке."""
        struct_ok, missing = check_exercise(source, ex.check_patterns)
        mypy_result: CheckResult | None = None
        if struct_ok:
            mypy_result = run_mypy(source)
        self.after(0, self._show_check_result, struct_ok, missing, mypy_result, ex)

    def _show_check_result(
        self,
        struct_ok: bool,
        missing: list[str],
        mypy_result: CheckResult | None,
        ex: Exercise,
    ) -> None:
        """Обновляет панель обратной связи (вызывается в главном потоке)."""
        self._check_btn.config(state=tk.NORMAL, text="✓ Проверить")
        self._feedback_text.config(state=tk.NORMAL)
        self._feedback_text.delete("1.0", tk.END)

        if not struct_ok:
            self._feedback_text.insert(tk.END, "❌ Не хватает аннотаций:\n\n", "error")
            for p in missing:
                self._feedback_text.insert(tk.END, f"  • {p}\n", "missing")
        elif mypy_result is not None and not mypy_result.ok:
            self._feedback_text.insert(tk.END, "⚠ Аннотации добавлены, но mypy нашёл ошибки:\n\n", "mypy_err")
            for issue in mypy_result.issues:
                prefix = "❌" if issue.severity == "error" else "⚠"
                code_part = f" [{issue.code}]" if issue.code else ""
                self._feedback_text.insert(
                    tk.END,
                    f"{prefix} Строка {issue.line}{code_part}: {issue.message}\n\n",
                    "mypy_err",
                )
        else:
            self._feedback_text.insert(tk.END, "✓ Правильно! Упражнение выполнено.\n", "ok")
            self._mark_completed(ex.id)

        self._feedback_text.config(state=tk.DISABLED)

    def _on_hint(self) -> None:
        ex = self._exercises[self._current_index]
        if self._hint_index >= len(ex.hints):
            self._set_hint_text("Подсказок больше нет. Нажмите «Решение», чтобы увидеть ответ.")
            return
        self._hint_used = True
        hint = ex.hints[self._hint_index]
        self._set_hint_text(f"Подсказка {self._hint_index + 1} из {len(ex.hints)}:\n\n{hint}")
        self._hint_index += 1

    def _on_show_solution(self) -> None:
        ex = self._exercises[self._current_index]
        self._editor.set_text(ex.solution_code)
        self._set_hint_text("Показано эталонное решение.")

    # -----------------------------------------------------------------------
    # Вспомогательные методы
    # -----------------------------------------------------------------------

    def _load_exercise(self, index: int) -> None:
        """Загружает упражнение с указанным индексом."""
        self._current_index = index
        self._hint_index = 0
        self._hint_used = False
        ex = self._exercises[index]

        # Выделяем в списке
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(index)
        self._listbox.see(index)

        # Описание
        self._desc_text.config(state=tk.NORMAL)
        self._desc_text.delete("1.0", tk.END)
        level_label = LEVEL_LABELS.get(ex.level, ex.level)
        level_color = LEVEL_COLORS.get(ex.level, "#888888")
        self._desc_text.tag_config("level", foreground=level_color)
        self._desc_text.insert(tk.END, f"[{level_label}]  ", "level")
        self._desc_text.insert(tk.END, ex.description)
        self._desc_text.config(state=tk.DISABLED)

        # Редактор
        self._editor.set_text(ex.starter_code)

        # Сброс панелей
        self._set_hint_text("")
        self._feedback_text.config(state=tk.NORMAL)
        self._feedback_text.delete("1.0", tk.END)
        self._feedback_text.config(state=tk.DISABLED)

    def _mark_completed(self, ex_id: str) -> None:
        """Отмечает упражнение выполненным и обновляет статистику."""
        self._completed.add(ex_id)
        if not self._hint_used:
            self._no_hint_completed.add(ex_id)
        total = len(self._exercises)
        done = len(self._completed)
        no_hint = len(self._no_hint_completed)
        self._progress_var.set(
            f"Выполнено: {done}/{total}\n"
            f"Без подсказок: {no_hint}/{done}"
        )

    def _set_hint_text(self, text: str) -> None:
        self._hint_text.config(state=tk.NORMAL)
        self._hint_text.delete("1.0", tk.END)
        self._hint_text.insert("1.0", text)
        self._hint_text.config(state=tk.DISABLED)
