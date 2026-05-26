"""
Модуль демонстрационных примеров.

Каждый сценарий представлен тремя вариантами кода:
  - dynamic_code  — без аннотаций типов
  - typed_code    — с полными аннотациями (корректен для mypy --strict)
  - error_code    — намеренная ошибка типа (mypy обнаруживает её)
"""
from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Структура данных
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Example:
    """Демонстрационный сценарий для раздела «Примеры»."""
    id: str
    title: str
    description: str
    dynamic_code: str
    typed_code: str
    error_code: str
    error_explanation: str


# ===========================================================================
# Сценарий 1. Базовые типы переменных
# ===========================================================================

_BASIC_DYNAMIC = '''\
# Динамическая типизация: переменные не имеют фиксированного типа

def greet(name):
    return "Привет, " + name + "!"

age = 20
age = "двадцать"   # Python не возражает — тип сменился!

result = greet("Дима")
print(result)
print(age)

# Ошибка обнаруживается только при запуске:
# bad = 42 + "строка"   # -> TypeError: unsupported operand type(s)
'''

_BASIC_TYPED = '''\
# Статическая типизация: аннотации фиксируют типы

def greet(name: str) -> str:
    return "Привет, " + name + "!"

age: int = 20
# age = "двадцать"  # mypy: Incompatible types in assignment [assignment]

result: str = greet("Дима")
print(result)
print(age)
'''

_BASIC_ERROR = '''\
# Намеренная ошибка: переменной типа int присваивается str

def greet(name: str) -> str:
    return "Привет, " + name + "!"

age: int = 20
age = "двадцать"       # [assignment]  <- mypy поймает здесь

count: int = 5
total: str = count + 10   # [assignment] <- и здесь
'''

BASIC_TYPES = Example(
    id="basic_types",
    title="Базовые типы переменных",
    description=(
        "Демонстрация аннотаций int, float, str, bool. "
        "В динамическом варианте переменная может в любой момент сменить тип — "
        "Python не возражает. Статический вариант фиксирует типы и позволяет mypy "
        "обнаружить ошибки до запуска."
    ),
    dynamic_code=_BASIC_DYNAMIC,
    typed_code=_BASIC_TYPED,
    error_code=_BASIC_ERROR,
    error_explanation=(
        "Переменной age с типом int присваивается значение str. "
        "Mypy сообщает об ошибке [assignment] и указывает точную строку."
    ),
)


# ===========================================================================
# Сценарий 2. Типизация функций
# ===========================================================================

_FUNC_DYNAMIC = '''\
# Функции без аннотаций: тип аргументов не контролируется

def find_user(user_id):
    users = {1: "Аня", 2: "Борис"}
    return users.get(user_id)

def send_email(address, subject):
    print(f"Отправка '{subject}' на {address}")

user = find_user(1)
# Без аннотаций IDE не знает, что user может быть None:
print(user.upper())      # AttributeError, если user is None
send_email(42, "Тест")   # Передали int вместо str — тихая ошибка
'''

_FUNC_TYPED = '''\
from typing import Optional

def find_user(user_id: int) -> Optional[str]:
    users: dict[int, str] = {1: "Аня", 2: "Борис"}
    return users.get(user_id)

def send_email(address: str, subject: str) -> None:
    print(f"Отправка \'{subject}\' на {address}")

user = find_user(1)
if user is not None:
    print(user.upper())   # mypy знает: здесь user: str

# send_email(42, "Тест")  # mypy: Argument 1 has incompatible type "int"
'''

_FUNC_ERROR = '''\
from typing import Optional

def find_user(user_id: int) -> Optional[str]:
    users: dict[int, str] = {1: "Аня", 2: "Борис"}
    return users.get(user_id)

def send_email(address: str, subject: str) -> None:
    print(f"Отправка \'{subject}\' на {address}")

user = find_user(1)
print(user.upper())      # [union-attr]: Item "None" of "str | None" has no attribute "upper"

send_email(42, "Тест")   # [arg-type]: Argument 1 to "send_email" has incompatible type "int"
'''

FUNCTION_TYPES = Example(
    id="function_types",
    title="Типизация функций",
    description=(
        "Аннотации параметров и возвращаемых значений функций. "
        "Optional[str] сообщает, что функция может вернуть None. "
        "mypy требует явной проверки 'if user is not None' перед использованием результата."
    ),
    dynamic_code=_FUNC_DYNAMIC,
    typed_code=_FUNC_TYPED,
    error_code=_FUNC_ERROR,
    error_explanation=(
        "Два нарушения: использование Optional-значения без проверки на None "
        "([union-attr]) и передача int вместо str в аргументе функции ([arg-type])."
    ),
)


# ===========================================================================
# Сценарий 3. Коллекции и обобщённые типы
# ===========================================================================

_COLL_DYNAMIC = '''\
# Коллекции без аннотаций: содержимое не проверяется

def sum_scores(scores):
    return sum(scores)

def word_count(text):
    result = {}
    for word in text.split():
        result[word] = result.get(word, 0) + 1
    return result

data = [1, 2, "три", 4]          # смешанный список — ошибка при sum()
print(sum_scores([10, 20, 30]))
counts = word_count("привет мир привет")
print(counts)
'''

_COLL_TYPED = '''\
def sum_scores(scores: list[int]) -> int:
    return sum(scores)

def word_count(text: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for word in text.split():
        result[word] = result.get(word, 0) + 1
    return result

def first_last(items: list[str]) -> tuple[str, str]:
    return items[0], items[-1]

# data: list[int] = [1, 2, "три", 4]  # mypy: [list-item] тут же поймает ошибку
scores: list[int] = [10, 20, 30]
print(sum_scores(scores))

counts: dict[str, int] = word_count("привет мир привет")
print(counts)
'''

_COLL_ERROR = '''\
def sum_scores(scores: list[int]) -> int:
    return sum(scores)

data: list[int] = [1, 2, "три", 4]   # [list-item]: str несовместим с int
total: int = sum_scores(data)

mapping: dict[str, int] = {"a": 1, "b": "два"}  # [dict-item]: str вместо int
'''

COLLECTIONS = Example(
    id="collections",
    title="Коллекции и обобщённые типы",
    description=(
        "Параметризованные типы list[int], dict[str, int], tuple[str, str]. "
        "Синтаксис Python 3.9+ позволяет писать типы прямо без импорта из typing. "
        "mypy проверяет содержимое коллекций и сообщает о несовместимых элементах."
    ),
    dynamic_code=_COLL_DYNAMIC,
    typed_code=_COLL_TYPED,
    error_code=_COLL_ERROR,
    error_explanation=(
        "Элемент 'три' (str) несовместим с list[int] — ошибка [list-item]. "
        "Значение 'два' (str) несовместимо с dict[str, int] — ошибка [dict-item]."
    ),
)


# ===========================================================================
# Сценарий 4. Optional и работа с None
# ===========================================================================

_OPT_DYNAMIC = '''\
# Работа с None без аннотаций: ошибки скрыты до выполнения

def get_config(key):
    config = {"host": "localhost", "port": "8080"}
    return config.get(key)

host = get_config("host")
missing = get_config("db_name")

print(host.upper())      # OK
print(missing.upper())   # AttributeError: NoneType has no attribute upper
'''

_OPT_TYPED = '''\
# Три паттерна безопасной работы с Optional

def get_config(key: str) -> str | None:
    config: dict[str, str] = {"host": "localhost", "port": "8080"}
    return config.get(key)

# Паттерн 1: явная проверка
host = get_config("host")
if host is not None:
    print(host.upper())

# Паттерн 2: значение по умолчанию
port = get_config("port") or "3000"
print(port)

# Паттерн 3: assert (убеждаемся, что значение есть)
name = get_config("host")
assert name is not None, "host не настроен"
print(name.upper())  # mypy знает: здесь name: str
'''

_OPT_ERROR = '''\
def get_config(key: str) -> str | None:
    config: dict[str, str] = {"host": "localhost"}
    return config.get(key)

value = get_config("host")
# Обращение без проверки на None:
print(value.upper())    # [union-attr]: Item "None" of "str | None" has no attribute "upper"
length = len(value)     # [union-attr]: тоже ошибка
'''

OPTIONAL_NONE = Example(
    id="optional_none",
    title="Optional и работа с None",
    description=(
        "str | None (или Optional[str]) — тип, означающий «строка или None». "
        "mypy требует явной проверки на None перед использованием такого значения. "
        "Три безопасных паттерна: if-проверка, оператор or, assert."
    ),
    dynamic_code=_OPT_DYNAMIC,
    typed_code=_OPT_TYPED,
    error_code=_OPT_ERROR,
    error_explanation=(
        "Обращение к атрибуту .upper() и функции len() без проверки на None. "
        "Mypy сообщает [union-attr]: объект может быть None, у которого нет этих методов."
    ),
)


# ===========================================================================
# Сценарий 5. Утиная типизация и Protocol
# ===========================================================================

_DUCK_DYNAMIC = '''\
# Утиная типизация: если у объекта есть нужный метод — он подходит

class Circle:
    def __init__(self, r):
        self.r = r
    def area(self):
        return 3.14159 * self.r ** 2

class Rectangle:
    def __init__(self, w, h):
        self.w, self.h = w, h
    def area(self):
        return self.w * self.h

class Triangle:
    def __init__(self, b, h):
        self.b, self.h = b, h
    # Забыли реализовать area() — ошибка обнаружится только при вызове

def print_area(shape):
    print(f"Площадь: {shape.area():.2f}")

for s in [Circle(5), Rectangle(3, 4)]:
    print_area(s)
'''

_DUCK_TYPED = '''\
from typing import Protocol

class HasArea(Protocol):
    """Протокол: любой объект с методом area() -> float."""
    def area(self) -> float: ...

class Circle:
    def __init__(self, r: float) -> None:
        self.r = r
    def area(self) -> float:
        return 3.14159 * self.r ** 2

class Rectangle:
    def __init__(self, w: float, h: float) -> None:
        self.w, self.h = w, h
    def area(self) -> float:
        return self.w * self.h

def print_area(shape: HasArea) -> None:
    print(f"Площадь: {shape.area():.2f}")

for s in [Circle(5.0), Rectangle(3.0, 4.0)]:
    print_area(s)
'''

_DUCK_ERROR = '''\
from typing import Protocol

class HasArea(Protocol):
    def area(self) -> float: ...

class Triangle:
    def __init__(self, b: float, h: float) -> None:
        self.b, self.h = b, h
    # area() не реализован!

class Circle:
    def __init__(self, r: float) -> None:
        self.r = r
    def area(self) -> float:
        return 3.14159 * self.r ** 2

def print_area(shape: HasArea) -> None:
    print(f"Площадь: {shape.area():.2f}")

print_area(Triangle(3.0, 4.0))  # [arg-type]: Triangle не совместим с HasArea
print_area(Circle(5.0))
'''

DUCK_TYPING = Example(
    id="duck_typing",
    title="Утиная типизация и Protocol",
    description=(
        "Protocol описывает структурный интерфейс: любой класс с нужными методами "
        "автоматически совместим, без наследования. "
        "Если класс не реализует требуемый метод — mypy сообщит об ошибке до запуска."
    ),
    dynamic_code=_DUCK_DYNAMIC,
    typed_code=_DUCK_TYPED,
    error_code=_DUCK_ERROR,
    error_explanation=(
        "Класс Triangle не реализует метод area() — он не совместим с HasArea. "
        "Mypy обнаруживает [arg-type] при передаче Triangle в функцию print_area."
    ),
)


# ---------------------------------------------------------------------------
# Список всех сценариев в порядке отображения
# ---------------------------------------------------------------------------

ALL_EXAMPLES: list[Example] = [
    BASIC_TYPES,
    FUNCTION_TYPES,
    COLLECTIONS,
    OPTIONAL_NONE,
    DUCK_TYPING,
]
