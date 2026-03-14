"""Парсер Form.xcore → FormSchema.

Разбирает Xcore DSL (Eclipse EMF) и строит Python-модель
классов, интерфейсов, перечислений и свойств форм 1С.

Стратегия: двухпроходный парсинг.
1. Препроцессинг: убираем строчные комментарии, склеиваем многострочные объявления
2. Парсинг: идём по строкам, распознаём top-level конструкции
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import (
    FormSchema,
    XcoreClass,
    XcoreEnum,
    XcoreEnumValue,
    XcoreProperty,
    XcoreType,
)

_RE_ECORE = re.compile(r'nsPrefix="(\w+)".*nsURI="([^"]+)"')
_RE_ENUM_VALUE = re.compile(r"^\s*(\w+)\s*=\s*(\d+)")


def parse_xcore(path: Path) -> FormSchema:
    """Парсит файл .xcore и возвращает FormSchema."""
    text = path.read_text(encoding="utf-8")
    return _parse_text(text)


def _parse_text(text: str) -> FormSchema:
    schema = FormSchema()
    lines = text.splitlines()
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()

        # Пустые и комментарии
        if not line or line.startswith("//"):
            i += 1
            continue

        # @Ecore annotation
        if line.startswith("@Ecore"):
            m = _RE_ECORE.search(line)
            if m:
                schema.ns_prefix = m.group(1)
                schema.ns_uri = m.group(2)
            i += 1
            continue

        # Другие аннотации верхнего уровня — пропустить
        if line.startswith("@") or line.startswith("annotation "):
            i += 1
            continue

        # package
        if line.startswith("package "):
            schema.package = line.split(None, 1)[1].strip()
            i += 1
            continue

        # import
        if line.startswith("import "):
            schema.imports.append(line.split(None, 1)[1].strip())
            i += 1
            continue

        # type X wraps Y
        if line.startswith("type "):
            m = re.match(r"type\s+(\w+)\s+wraps\s+([\w.$]+)", line)
            if m:
                schema.types[m.group(1)] = XcoreType(name=m.group(1), wraps=m.group(2))
            i += 1
            continue

        # enum
        if line.startswith("enum "):
            enum_name = line.split()[1].rstrip("{").strip()
            i, body = _collect_block(lines, i)
            schema.enums[enum_name] = _parse_enum_body(enum_name, body)
            continue

        # class / abstract class / interface
        if line.startswith(("class ", "abstract class ", "interface ")):
            # Собираем объявление до { (может быть многострочным)
            decl = line
            j = i
            while "{" not in decl and j + 1 < n:
                j += 1
                next_l = lines[j].strip()
                if next_l.startswith("//"):
                    continue
                decl += " " + next_l

            # Парсим объявление
            header = decl.split("{")[0].strip()
            cls = _parse_class_header(header)

            if cls is None:
                # wraps — это type-обёртка
                m = re.match(r"(?:abstract\s+)?class\s+(\w+)\s+wraps\s+([\w.$]+)", header)
                if m:
                    schema.types[m.group(1)] = XcoreType(name=m.group(1), wraps=m.group(2))
                i, _ = _collect_block(lines, i)
                continue

            # Собираем тело блока
            i, body = _collect_block(lines, i)
            cls.properties = _parse_properties(body)
            schema.classes[cls.name] = cls
            continue

        i += 1

    return schema


def _collect_block(lines: list[str], start: int) -> tuple[int, str]:
    """Собирает содержимое блока { ... } и возвращает (next_index, body_text).

    Если блока нет — возвращает (start+1, "").
    """
    i = start
    n = len(lines)

    # Найти открывающую скобку
    while i < n and "{" not in lines[i]:
        i += 1

    if i >= n:
        return start + 1, ""

    # Считаем скобки
    depth = 0
    body_lines = []
    while i < n:
        line = lines[i]
        depth += line.count("{") - line.count("}")

        # Добавляем строку в тело (кроме первой { и последней })
        body_lines.append(line)
        i += 1

        if depth <= 0:
            break

    # Убираем первую и последнюю строки (с { и })
    body = "\n".join(body_lines)
    # Удаляем всё до первой { и после последней }
    idx_open = body.index("{")
    idx_close = body.rindex("}")
    inner = body[idx_open + 1:idx_close]
    return i, inner


def _parse_class_header(header: str) -> XcoreClass | None:
    """Парсит заголовок класса/интерфейса."""
    # Убираем inline-комментарий
    comment = ""
    if "//" in header:
        header, comment = header.split("//", 1)
        header = header.strip()
        comment = comment.strip()

    # Определяем kind
    if header.startswith("abstract class "):
        kind = "abstract class"
        rest = header[len("abstract class "):]
    elif header.startswith("class "):
        kind = "class"
        rest = header[len("class "):]
    elif header.startswith("interface "):
        kind = "interface"
        rest = header[len("interface "):]
    else:
        return None

    # wraps → это type, не класс
    if " wraps " in rest:
        return None

    # name extends A, B, C
    parts = re.split(r"\s+extends\s+", rest, maxsplit=1)
    name = parts[0].strip()

    extends = []
    if len(parts) > 1:
        extends = [s.strip() for s in parts[1].split(",") if s.strip()]

    return XcoreClass(name=name, kind=kind, extends=extends, comment=comment)


def _parse_enum_body(name: str, body: str) -> XcoreEnum:
    """Парсит тело enum."""
    enum = XcoreEnum(name=name)
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        # Извлечь комментарий
        comment = ""
        if "//" in line:
            line, comment = line.split("//", 1)
            line = line.strip()
            comment = comment.strip()

        m = _RE_ENUM_VALUE.match(line)
        if m:
            enum.values.append(XcoreEnumValue(
                name=m.group(1),
                value=int(m.group(2)),
                comment=comment,
            ))
    return enum


def _parse_properties(body: str) -> list[XcoreProperty]:
    """Парсит свойства из тела класса/интерфейса."""
    props: list[XcoreProperty] = []

    for line in body.splitlines():
        line = line.strip()

        # Пропускаем пустые, комментарии, аннотации, маркеры #start/#end
        if not line or line.startswith("//") or line.startswith("@") or line.startswith("#"):
            continue

        # op — методы: пропускаем (тело уже внутри body, но мы не парсим вложенные {})
        if line.startswith("op "):
            continue

        # Строки с { или } — внутренние блоки (op тела), пропускаем
        if "{" in line or "}" in line:
            continue

        prop = _parse_property_line(line)
        if prop:
            props.append(prop)

    return props


def _parse_property_line(line: str) -> XcoreProperty | None:
    """Парсит одну строку свойства."""
    is_contains = False
    is_refers = False
    is_unsettable = False
    is_transient = False
    comment = ""

    # Inline-комментарий
    if "//" in line:
        line, comment = line.split("//", 1)
        line = line.strip()
        comment = comment.strip()

    tokens = line.split()
    if not tokens:
        return None

    idx = 0

    # Модификаторы
    while idx < len(tokens):
        t = tokens[idx]
        if t == "contains":
            is_contains = True
        elif t == "refers":
            is_refers = True
        elif t == "unsettable":
            is_unsettable = True
        elif t == "transient":
            is_transient = True
        else:
            break
        idx += 1

    if idx >= len(tokens):
        return None

    # Тип
    type_name = tokens[idx]
    idx += 1

    # Множественность: Type[] или Type [1]
    is_list = False
    multiplicity = ""
    if type_name.endswith("[]"):
        type_name = type_name[:-2]
        is_list = True
    if idx < len(tokens) and tokens[idx].startswith("["):
        multiplicity = tokens[idx]
        is_list = is_list or multiplicity == "[]"
        idx += 1

    if idx >= len(tokens):
        return None

    # Имя
    prop_name = tokens[idx]
    idx += 1

    # Дефолтное значение
    default = ""
    if idx < len(tokens) and tokens[idx] == "=":
        idx += 1
        if idx < len(tokens):
            default = tokens[idx].strip('"')

    # Фильтр невалидных имён
    if not re.match(r"^[a-zA-Z_]\w*$", prop_name):
        return None

    return XcoreProperty(
        name=prop_name,
        type=type_name,
        is_list=is_list,
        is_containment=is_contains,
        is_reference=is_refers,
        is_unsettable=is_unsettable,
        is_transient=is_transient,
        default=default,
        comment=comment,
        multiplicity=multiplicity,
    )
