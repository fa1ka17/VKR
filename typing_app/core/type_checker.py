"""
Модуль проверки типов.

Обеспечивает интеграцию с инструментом статического анализа mypy,
а также AST-анализ аннотаций типов в пользовательском коде.
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Структуры данных
# ---------------------------------------------------------------------------

@dataclass
class TypeIssue:
    """Одно диагностическое сообщение mypy."""
    line: int
    col: int
    severity: str          # 'error' | 'warning' | 'note'
    message: str
    code: str              # код ошибки mypy, например 'arg-type'


@dataclass
class CheckResult:
    """Результат проверки типов."""
    ok: bool
    issues: list[TypeIssue] = field(default_factory=list)


@dataclass
class AnnotationStats:
    """Статистика аннотаций в коде."""
    params: int = 0
    returns: int = 0
    variables: int = 0


@dataclass
class RunResult:
    """Результат выполнения кода в подпроцессе."""
    stdout: str
    stderr: str
    timed_out: bool = False


# ---------------------------------------------------------------------------
# Русскоязычные пояснения к кодам ошибок mypy
# ---------------------------------------------------------------------------

ERROR_EXPLANATIONS: dict[str, str] = {
    "arg-type": (
        "Тип переданного аргумента не совпадает с ожидаемым типом параметра функции. "
        "Проверьте, что вы передаёте значение правильного типа."
    ),
    "return-value": (
        "Тип возвращаемого значения не совпадает с объявленным возвращаемым типом функции. "
        "Проверьте аннотацию -> в сигнатуре функции."
    ),
    "assignment": (
        "Переменной присваивается значение типа, несовместимого с объявленным типом переменной."
    ),
    "union-attr": (
        "Переменная может иметь значение None, но вы обращаетесь к ней без предварительной проверки. "
        "Добавьте проверку вида 'if value is not None' перед использованием."
    ),
    "attr-defined": (
        "Обращение к атрибуту или методу, которого нет у данного типа. "
        "Проверьте правильность имени атрибута и тип объекта."
    ),
    "name-defined": (
        "Имя не определено в данной области видимости. "
        "Возможно, вы забыли импортировать тип из модуля typing."
    ),
    "no-untyped-def": (
        "Функция не имеет аннотаций типов. "
        "Добавьте аннотации к параметрам и возвращаемому значению."
    ),
    "no-untyped-call": (
        "Вызов функции без аннотаций типов в типизированном контексте. "
        "Добавьте аннотации к вызываемой функции."
    ),
    "operator": (
        "Операция применяется к значениям несовместимых типов. "
        "Проверьте типы операндов."
    ),
    "index": (
        "Индексирование применяется к объекту, не поддерживающему данный тип индекса."
    ),
    "call-overload": (
        "Ни одна из перегрузок функции не подходит для данных типов аргументов."
    ),
    "override": (
        "Переопределённый метод несовместим по типам с методом базового класса."
    ),
    "misc": (
        "Прочая ошибка типизации. Прочитайте сообщение mypy для подробностей."
    ),
}

MAX_CODE_LEN: int = 50_000   # символов — защита от слишком большого ввода
_MYPY_PATTERN = re.compile(
    r"^.+:(\d+):(\d+): (error|warning|note): (.+?)(?:\s+\[(.+?)\])?$"
)


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------

def run_mypy(source: str) -> CheckResult:
    """
    Запускает mypy --strict на переданном исходном коде.

    Код записывается во временный файл, mypy запускается как подпроцесс.
    Временный файл гарантированно удаляется по завершении.

    :param source: Строка с Python-кодом.
    :return: CheckResult с флагом ok и списком TypeIssue.
    """
    if len(source) > MAX_CODE_LEN:
        issue = TypeIssue(
            line=0, col=0, severity="error",
            message=(
                f"Код слишком длинный ({len(source)} символов). "
                f"Максимум: {MAX_CODE_LEN} символов."
            ),
            code="misc",
        )
        return CheckResult(ok=False, issues=[issue])

    with tempfile.NamedTemporaryFile(
        suffix=".py",
        prefix="typing_check_",
        mode="w",
        encoding="utf-8",
        delete=False,
    ) as tmp:
        tmp.write(source)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [
                "mypy",
                "--strict",
                "--no-error-summary",
                "--show-column-numbers",
                "--show-error-codes",
                tmp_path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        issues = _parse_mypy_output(result.stdout, tmp_path)
        return CheckResult(ok=len(issues) == 0, issues=issues)
    except subprocess.TimeoutExpired:
        issue = TypeIssue(
            line=0, col=0, severity="error",
            message="Превышен лимит времени анализа (15 с). Упростите код.",
            code="misc",
        )
        return CheckResult(ok=False, issues=[issue])
    except FileNotFoundError:
        issue = TypeIssue(
            line=0, col=0, severity="error",
            message=(
                "Инструмент mypy не найден. "
                "Установите его: pip install mypy"
            ),
            code="misc",
        )
        return CheckResult(ok=False, issues=[issue])
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def run_code_only(source: str) -> RunResult:
    """
    Выполняет Python-код в изолированном подпроцессе и возвращает вывод.

    :param source: Строка с Python-кодом.
    :return: RunResult со stdout, stderr и флагом timed_out.
    """
    with tempfile.NamedTemporaryFile(
        suffix=".py",
        prefix="run_code_",
        mode="w",
        encoding="utf-8",
        delete=False,
    ) as tmp:
        tmp.write(source)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return RunResult(stdout=result.stdout, stderr=result.stderr)
    except subprocess.TimeoutExpired:
        return RunResult(
            stdout="",
            stderr="Превышен лимит времени выполнения (10 с).",
            timed_out=True,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def count_annotations(source: str) -> AnnotationStats:
    """
    Считает аннотации типов в коде через обход AST.

    :param source: Строка с Python-кодом.
    :return: AnnotationStats с количеством аннотированных параметров,
             возвращаемых значений и переменных.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return AnnotationStats()

    annotated_params = 0
    annotated_returns = 0
    annotated_vars = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            annotated_params += sum(
                1 for a in node.args.args if a.annotation is not None
            )
            if node.returns is not None:
                annotated_returns += 1
        elif isinstance(node, ast.AnnAssign):
            annotated_vars += 1

    return AnnotationStats(
        params=annotated_params,
        returns=annotated_returns,
        variables=annotated_vars,
    )


def check_exercise(source: str, required_patterns: list[str]) -> tuple[bool, list[str]]:
    """
    Проверяет наличие обязательных строковых паттернов в коде упражнения.

    :param source: Код, введённый пользователем.
    :param required_patterns: Список строк, которые должны присутствовать в коде.
    :return: Кортеж (успех, список отсутствующих паттернов).
    """
    missing: list[str] = [p for p in required_patterns if p not in source]
    return len(missing) == 0, missing


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _parse_mypy_output(output: str, tmp_path: str) -> list[TypeIssue]:
    """Разбирает стандартный вывод mypy и возвращает список TypeIssue."""
    issues: list[TypeIssue] = []
    for raw_line in output.splitlines():
        # Нормализуем путь — заменяем временное имя файла на пустышку
        line = raw_line.replace(tmp_path, "<code>")
        m = _MYPY_PATTERN.match(line)
        if m is None:
            continue
        line_no = int(m.group(1))
        col_no = int(m.group(2))
        severity = m.group(3)
        message = m.group(4)
        code = m.group(5) or ""

        # Добавляем русскоязычное пояснение, если оно есть
        if code in ERROR_EXPLANATIONS:
            message = f"{message}\n  → {ERROR_EXPLANATIONS[code]}"

        issues.append(
            TypeIssue(
                line=line_no,
                col=col_no,
                severity=severity,
                message=message,
                code=code,
            )
        )
    return issues
