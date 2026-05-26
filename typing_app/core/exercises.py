"""
Модуль учебных упражнений.

Каждое упражнение описывается объектом Exercise с заготовкой кода,
эталонным решением, проверочными паттернами и подсказками.
"""
from __future__ import annotations

from dataclasses import dataclass, field

LEVEL_COLORS: dict[str, str] = {
    "beginner":     "#4caf50",   # зелёный
    "basic":        "#2196f3",   # синий
    "intermediate": "#ff9800",   # оранжевый
    "advanced":     "#f44336",   # красный
}

LEVEL_LABELS: dict[str, str] = {
    "beginner":     "Начальный",
    "basic":        "Базовый",
    "intermediate": "Средний",
    "advanced":     "Продвинутый",
}


@dataclass(frozen=True)
class Exercise:
    """Одно учебное упражнение."""
    id: str
    title: str
    level: str            # 'beginner' | 'basic' | 'intermediate' | 'advanced'
    description: str
    starter_code: str
    solution_code: str
    check_patterns: list[str]
    hints: list[str]


# ===========================================================================
# ex01 — аннотация простой функции
# ===========================================================================

EX01 = Exercise(
    id="ex01",
    title="ex01 · Функция приветствия",
    level="beginner",
    description=(
        "Добавьте аннотации типов к функции greet.\n\n"
        "• Параметр name должен иметь тип str\n"
        "• Функция должна возвращать str\n\n"
        "После добавления аннотаций нажмите «Проверить»."
    ),
    starter_code="""\
def greet(name):
    return "Привет, " + name + "!"

print(greet("Дима"))
""",
    solution_code="""\
def greet(name: str) -> str:
    return "Привет, " + name + "!"

print(greet("Дима"))
""",
    check_patterns=["name: str", "-> str"],
    hints=[
        "Аннотация параметра пишется после двоеточия: name: str",
        "Тип возвращаемого значения указывается после -> перед двоеточием функции.",
        "Итоговая сигнатура: def greet(name: str) -> str:",
    ],
)

# ===========================================================================
# ex02 — несколько параметров float
# ===========================================================================

EX02 = Exercise(
    id="ex02",
    title="ex02 · Индекс массы тела",
    level="beginner",
    description=(
        "Добавьте аннотации типов к функции calculate_bmi.\n\n"
        "• weight — масса в кг (float)\n"
        "• height — рост в метрах (float)\n"
        "• Функция возвращает float\n\n"
        "Формула: weight / height ** 2"
    ),
    starter_code="""\
def calculate_bmi(weight, height):
    return weight / height ** 2

print(f"ИМТ = {calculate_bmi(70.0, 1.75):.1f}")
""",
    solution_code="""\
def calculate_bmi(weight: float, height: float) -> float:
    return weight / height ** 2

print(f"ИМТ = {calculate_bmi(70.0, 1.75):.1f}")
""",
    check_patterns=["weight: float", "height: float", "-> float"],
    hints=[
        "Оба параметра имеют тип float — запись: weight: float, height: float",
        "Функция возвращает вещественное число float.",
        "Итоговая сигнатура: def calculate_bmi(weight: float, height: float) -> float:",
    ],
)

# ===========================================================================
# ex03 — возврат dict[str, int]
# ===========================================================================

EX03 = Exercise(
    id="ex03",
    title="ex03 · Подсчёт слов",
    level="basic",
    description=(
        "Аннотируйте функцию word_count.\n\n"
        "• Параметр text — строка str\n"
        "• Возвращаемый тип: словарь, где ключи — слова (str), "
        "значения — количество вхождений (int)\n"
        "• Используйте синтаксис Python 3.9+: dict[str, int]"
    ),
    starter_code="""\
def word_count(text):
    result = {}
    for word in text.split():
        result[word] = result.get(word, 0) + 1
    return result

counts = word_count("привет мир привет")
print(counts)
""",
    solution_code="""\
def word_count(text: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for word in text.split():
        result[word] = result.get(word, 0) + 1
    return result

counts = word_count("привет мир привет")
print(counts)
""",
    check_patterns=["text: str", "-> dict[str, int]"],
    hints=[
        "Параметр text — обычная строка: text: str",
        "Возвращаемый тип — словарь с ключами str и значениями int.",
        "Синтаксис: -> dict[str, int]  (без импорта из typing в Python 3.9+)",
    ],
)

# ===========================================================================
# ex04 — Optional[str]
# ===========================================================================

EX04 = Exercise(
    id="ex04",
    title="ex04 · Поиск пользователя",
    level="intermediate",
    description=(
        "Аннотируйте функцию find_user.\n\n"
        "• user_id — целое число int\n"
        "• Функция возвращает str, если пользователь найден, "
        "или None, если не найден\n"
        "• Используйте Optional[str] из typing (или str | None)\n"
        "• Добавьте проверку 'is not None' перед print"
    ),
    starter_code="""\
from typing import Optional

def find_user(user_id):
    users = {1: "Аня", 2: "Борис"}
    return users.get(user_id)

user = find_user(1)
print(user.upper())   # Небезопасно без проверки на None!
""",
    solution_code="""\
from typing import Optional

def find_user(user_id: int) -> Optional[str]:
    users: dict[int, str] = {1: "Аня", 2: "Борис"}
    return users.get(user_id)

user = find_user(1)
if user is not None:
    print(user.upper())
""",
    check_patterns=["user_id: int", "Optional[str]", "is not None"],
    hints=[
        "Параметр — целое число: user_id: int",
        "Функция может вернуть строку или None: возвращаемый тип Optional[str].",
        "Полная сигнатура: def find_user(user_id: int) -> Optional[str]:\n"
        "Перед .upper() добавьте: if user is not None:",
    ],
)

# ===========================================================================
# ex05 — атрибуты класса
# ===========================================================================

EX05 = Exercise(
    id="ex05",
    title="ex05 · Класс Point",
    level="intermediate",
    description=(
        "Аннотируйте класс Point.\n\n"
        "• Атрибуты x и y — числа float\n"
        "• __init__ не возвращает значение (-> None)\n"
        "• distance_to принимает other: Point и возвращает float\n\n"
        "Используйте self.x: float = x внутри __init__."
    ),
    starter_code="""\
import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

p1 = Point(0.0, 0.0)
p2 = Point(3.0, 4.0)
print(f"Расстояние: {p1.distance_to(p2):.1f}")
""",
    solution_code="""\
import math

class Point:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y

    def distance_to(self, other: "Point") -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

p1 = Point(0.0, 0.0)
p2 = Point(3.0, 4.0)
print(f"Расстояние: {p1.distance_to(p2):.1f}")
""",
    check_patterns=["x: float", "y: float", "-> float"],
    hints=[
        "Параметры __init__: x: float, y: float; __init__ возвращает -> None",
        "Объявите атрибуты явно: self.x: float = x  и  self.y: float = y",
        "Сигнатура distance_to: def distance_to(self, other: \"Point\") -> float:",
    ],
)

# ===========================================================================
# ex06 — объединение типов int | float
# ===========================================================================

EX06 = Exercise(
    id="ex06",
    title="ex06 · Объединение типов",
    level="advanced",
    description=(
        "Аннотируйте функцию stringify, используя синтаксис объединения типов (PEP 604).\n\n"
        "• Параметр value принимает int ИЛИ float — запишите: int | float\n"
        "• Функция возвращает str\n\n"
        "Синтаксис int | float введён в Python 3.10 и не требует Union из typing."
    ),
    starter_code="""\
def stringify(value):
    return str(value)

print(stringify(42))
print(stringify(3.14))
""",
    solution_code="""\
def stringify(value: int | float) -> str:
    return str(value)

print(stringify(42))
print(stringify(3.14))
""",
    check_patterns=["int | float", "-> str"],
    hints=[
        "Объединение типов пишется через вертикальную черту: int | float",
        "Функция всегда возвращает строку: -> str",
        "Итоговая сигнатура: def stringify(value: int | float) -> str:",
    ],
)

# ---------------------------------------------------------------------------
# Полный список упражнений
# ---------------------------------------------------------------------------

ALL_EXERCISES: list[Exercise] = [EX01, EX02, EX03, EX04, EX05, EX06]
