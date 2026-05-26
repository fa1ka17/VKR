"""
Модуль главного окна приложения.

Реализует MainWindow — корневой виджет tk.Tk с тремя вкладками:
«Примеры», «Упражнения» и «О приложении».
"""
from __future__ import annotations

import sys
import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from core.examples import ALL_EXAMPLES, Example
from core.type_checker import (
    CheckResult, RunResult,
    run_code_only, run_mypy,
)
from ui.editor import CodeEditor
from ui.exercise_panel import ExercisePanel
from ui.results_panel import ResultsPanel
from utils.helpers import python_version_str


class MainWindow:
    """Главное окно приложения."""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.title(
            f"Статическая и динамическая типизация · Python {python_version_str()}"
        )
        self._root.minsize(1100, 700)
        self._root.configure(bg="#2b2b2b")

        self._apply_ttk_theme()
        self._build()

    # -----------------------------------------------------------------------
    # Запуск
    # -----------------------------------------------------------------------

    def run(self) -> None:
        """Запускает главный цикл обработки событий."""
        self._root.mainloop()

    # -----------------------------------------------------------------------
    # Построение интерфейса
    # -----------------------------------------------------------------------

    def _apply_ttk_theme(self) -> None:
        style = ttk.Style(self._root)
        style.theme_use("clam")
        style.configure(
            "TNotebook",
            background="#3c3f41",
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background="#3c3f41",
            foreground="#bbbbbb",
            padding=[12, 6],
            font=("Segoe UI", 10),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#4b5c78")],
            foreground=[("selected", "#ffffff")],
        )
        style.configure("TPanedwindow", background="#2b2b2b")
        style.configure("Sash", sashthickness=4, background="#555555")

    def _build(self) -> None:
        notebook = ttk.Notebook(self._root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Вкладка «Примеры»
        examples_tab = tk.Frame(notebook, bg="#2b2b2b")
        notebook.add(examples_tab, text=" 📖 Примеры ")
        self._build_examples_tab(examples_tab)

        # Вкладка «Упражнения»
        exercises_tab = tk.Frame(notebook, bg="#2b2b2b")
        notebook.add(exercises_tab, text=" ✏ Упражнения ")
        ExercisePanel(exercises_tab).pack(fill=tk.BOTH, expand=True)

        # Вкладка «О приложении»
        about_tab = tk.Frame(notebook, bg="#2b2b2b")
        notebook.add(about_tab, text=" ℹ О приложении ")
        self._build_about_tab(about_tab)

    # -----------------------------------------------------------------------
    # Вкладка «Примеры»
    # -----------------------------------------------------------------------

    def _build_examples_tab(self, parent: tk.Frame) -> None:
        seg_font = tkfont.Font(family="Segoe UI", size=10)
        bold_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        # Боковая панель со списком примеров
        sidebar = tk.Frame(parent, bg="#3c3f41", width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(4, 0), pady=4)
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="Темы", bg="#3c3f41", fg="#bbbbbb",
            font=bold_font,
        ).pack(anchor=tk.W, padx=8, pady=(8, 4))

        self._ex_listbox = tk.Listbox(
            sidebar,
            bg="#313335",
            fg="#bbbbbb",
            selectbackground="#214283",
            selectforeground="#ffffff",
            font=seg_font,
            relief=tk.FLAT,
            borderwidth=0,
            activestyle="none",
        )
        self._ex_listbox.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        for ex in ALL_EXAMPLES:
            self._ex_listbox.insert(tk.END, f"  {ex.title}")

        self._ex_listbox.bind("<<ListboxSelect>>", self._on_example_select)

        # Основная область: описание + notebook с тремя вариантами
        main = tk.Frame(parent, bg="#2b2b2b")
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Описание сценария
        self._example_desc = tk.Text(
            main,
            font=seg_font,
            bg="#2b2b2b",
            fg="#bbbbbb",
            height=4,
            state=tk.DISABLED,
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=6,
            pady=4,
        )
        self._example_desc.pack(fill=tk.X)

        # Вкладки: Динамическая / Статическая / Ошибка типа
        code_nb = ttk.Notebook(main)
        code_nb.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        self._editors: dict[str, CodeEditor] = {}
        self._results: dict[str, ResultsPanel] = {}

        tab_specs: list[tuple[str, str]] = [
            ("dynamic",  " 🐍 Динамическая "),
            ("typed",    " ✅ Статическая "),
            ("error",    " ❌ Ошибка типа "),
        ]
        for key, label in tab_specs:
            frame = tk.Frame(code_nb, bg="#2b2b2b")
            code_nb.add(frame, text=label)
            self._build_code_tab(frame, key)

        code_nb.bind("<<NotebookTabChanged>>", self._on_code_tab_changed)
        self._code_nb = code_nb

        # Учебный комментарий
        self._comment_var = tk.StringVar()
        tk.Label(
            main,
            textvariable=self._comment_var,
            bg="#2b2b2b",
            fg="#6bcb77",
            font=seg_font,
            wraplength=900,
            justify=tk.LEFT,
            pady=4,
        ).pack(fill=tk.X, padx=6)

        # Инициализация первого примера
        self._current_example_index: int = -1
        self._ex_listbox.selection_set(0)
        self._load_example(0)

    def _build_code_tab(self, parent: tk.Frame, key: str) -> None:
        """Строит одну вкладку с редактором, кнопками и панелью результатов."""
        bold_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        btn_style = dict(
            bg="#4b5c78", fg="#ffffff", font=bold_font,
            relief=tk.FLAT, padx=10, pady=4,
            activebackground="#5a6f90", activeforeground="#ffffff",
            cursor="hand2",
        )

        paned = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        top = tk.Frame(paned, bg="#2b2b2b")
        paned.add(top, weight=3)

        editor = CodeEditor(top)
        editor.pack(fill=tk.BOTH, expand=True)
        editor.set_readonly(True)
        self._editors[key] = editor

        btn_frame = tk.Frame(top, bg="#2b2b2b")
        btn_frame.pack(fill=tk.X, pady=(4, 0))

        run_btn = tk.Button(
            btn_frame, text="▶ Запустить",
            command=lambda k=key: self._on_run(k),
            **btn_style,
        )
        run_btn.pack(side=tk.LEFT, padx=(0, 6))

        if key in ("typed", "error"):
            mypy_btn = tk.Button(
                btn_frame, text="🔍 Проверить mypy",
                command=lambda k=key: self._on_run_mypy(k),
                **btn_style,
            )
            mypy_btn.pack(side=tk.LEFT)

        bottom = tk.Frame(paned, bg="#2b2b2b")
        paned.add(bottom, weight=2)

        results = ResultsPanel(
            bottom,
            on_line_click=lambda line, k=key: self._editors[k].jump_to_line(line),
        )
        results.pack(fill=tk.BOTH, expand=True)
        self._results[key] = results

    # -----------------------------------------------------------------------
    # Обработчики событий «Примеры»
    # -----------------------------------------------------------------------

    def _on_example_select(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        sel = self._ex_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx != self._current_example_index:
            self._load_example(idx)

    def _on_code_tab_changed(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        # Сбрасываем панели результатов при смене вкладки
        for r in self._results.values():
            r.clear()

    def _load_example(self, index: int) -> None:
        self._current_example_index = index
        ex = ALL_EXAMPLES[index]

        # Описание
        self._example_desc.config(state=tk.NORMAL)
        self._example_desc.delete("1.0", tk.END)
        self._example_desc.insert("1.0", ex.description)
        self._example_desc.config(state=tk.DISABLED)

        # Код в редакторах
        self._editors["dynamic"].set_text(ex.dynamic_code)
        self._editors["typed"].set_text(ex.typed_code)
        self._editors["error"].set_text(ex.error_code)

        # Учебный комментарий
        self._comment_var.set(f"💡  {ex.error_explanation}")

        # Сброс панелей результатов
        for r in self._results.values():
            r.clear()

    def _on_run(self, key: str) -> None:
        source = self._editors[key].get_text()
        self._results[key].clear()
        threading.Thread(
            target=self._do_run,
            args=(key, source),
            daemon=True,
        ).start()

    def _do_run(self, key: str, source: str) -> None:
        result: RunResult = run_code_only(source)
        self.after(lambda: self._results[key].show_run_output(
            result.stdout, result.stderr, result.timed_out
        ))

    def _on_run_mypy(self, key: str) -> None:
        source = self._editors[key].get_text()
        self._results[key].clear()
        # Переключаем панель на вкладку mypy
        self._results[key]._tab_var.set("mypy")
        threading.Thread(
            target=self._do_mypy,
            args=(key, source),
            daemon=True,
        ).start()

    def _do_mypy(self, key: str, source: str) -> None:
        result: CheckResult = run_mypy(source)
        # Подсветка строк с ошибками
        self.after(lambda r=result, k=key: self._show_mypy(r, k))

    def _show_mypy(self, result: CheckResult, key: str) -> None:
        editor = self._editors[key]
        editor.clear_line_highlights()
        for issue in result.issues:
            if issue.severity == "error":
                editor.highlight_line(issue.line)
        self._results[key].show_mypy_result(result.issues, result.ok)

    def after(self, fn: object) -> None:  # type: ignore[override]
        """Безопасный вызов функции в главном потоке через root.after."""
        self._root.after(0, fn)  # type: ignore[arg-type]

    # -----------------------------------------------------------------------
    # Вкладка «О приложении»
    # -----------------------------------------------------------------------

    def _build_about_tab(self, parent: tk.Frame) -> None:
        seg_font = tkfont.Font(family="Segoe UI", size=11)
        h1_font = tkfont.Font(family="Segoe UI", size=14, weight="bold")
        h2_font = tkfont.Font(family="Segoe UI", size=11, weight="bold")

        frame = tk.Frame(parent, bg="#2b2b2b")
        frame.pack(padx=40, pady=30, anchor=tk.NW)

        def lbl(text: str, font: tkfont.Font, fg: str = "#bbbbbb",
                pady: int = 4) -> None:
            tk.Label(
                frame, text=text, bg="#2b2b2b", fg=fg,
                font=font, justify=tk.LEFT, anchor=tk.W,
            ).pack(anchor=tk.W, pady=pady)

        lbl("Учебное приложение для изучения статической и динамической типизации",
            h1_font, "#ffffff", 0)
        lbl(f"Python {python_version_str()}  ·  tkinter  ·  Pygments  ·  mypy",
            seg_font, "#888888", 2)

        tk.Frame(frame, bg="#555555", height=1).pack(fill=tk.X, pady=10)

        lbl("Архитектура", h2_font, "#a0c4ff")
        lbl(
            "core/type_checker.py  — интеграция с mypy, AST-анализ аннотаций\n"
            "core/examples.py      — 5 демонстрационных сценариев\n"
            "core/exercises.py     — 6 учебных упражнений\n"
            "ui/editor.py          — редактор кода с подсветкой синтаксиса\n"
            "ui/results_panel.py   — панель диагностических сообщений\n"
            "ui/exercise_panel.py  — интерактивный учебный модуль\n"
            "ui/main_window.py     — главное окно",
            seg_font,
        )

        tk.Frame(frame, bg="#555555", height=1).pack(fill=tk.X, pady=10)

        lbl("Установка зависимостей", h2_font, "#a0c4ff")
        lbl("pip install pygments mypy", seg_font, "#ffd166")

        lbl("Запуск", h2_font, "#a0c4ff")
        lbl("python main.py", seg_font, "#ffd166")

        tk.Frame(frame, bg="#555555", height=1).pack(fill=tk.X, pady=10)

        lbl("ВКР: «Разработка приложения для изучения статической и динамической типизации»",
            seg_font, "#888888")
        lbl("Автор: Ляпин Дмитрий Александрович, ПГНИУ ИКНТ, 2026", seg_font, "#888888", 0)
