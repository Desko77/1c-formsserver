"""MCP-инструменты для работы со схемой форм."""

from __future__ import annotations

import json
from pathlib import Path

from mcp_forms.config import DATA_PATH, EDT_REFERENCE_PATH, FORM_PROMPT_EDT_MD


def get_form_schema() -> dict:
    """Получить JSON-схему элементов формы 1С.

    Возвращает структуру с описанием элементов, их свойств и типов данных.
    Используется для понимания доступных элементов при генерации форм.

    Returns:
        dict — JSON-схема формы
    """
    schema_path = DATA_PATH / "form_schema.json"
    if not schema_path.exists():
        return {"error": "form_schema.json не найден в %s" % DATA_PATH}

    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def get_form_prompt(format: str = "logform") -> str:
    """Получить промпт с базой знаний по тегам и атрибутам формы.

    Возвращает описание всех допустимых тегов, атрибутов и значений
    для XML-форм 1С в указанном формате.
    Используется как контекст для LLM при генерации/валидации форм.

    Args:
        format: формат формы — "logform" (по умолчанию), "managed" или "edt"

    Returns:
        str — текст промпта
    """
    if format == "edt":
        prompt_path = FORM_PROMPT_EDT_MD
    else:
        prompt_path = DATA_PATH / "formprompt.md"

    if not prompt_path.exists():
        return "%s не найден в %s" % (prompt_path.name, prompt_path.parent)

    return prompt_path.read_text(encoding="utf-8")


def get_xcore_model_info() -> dict:
    """Получить информацию о Xcore-модели форм из EDT.

    Парсит Form.xcore и возвращает сводку: классы, enum-ы, свойства.

    Returns:
        dict с полями: classes_count, enums_count, class_names, enum_names
    """
    xcore_path = EDT_REFERENCE_PATH / "Form.xcore"
    if not xcore_path.exists():
        return {"error": "Form.xcore не найден в %s" % EDT_REFERENCE_PATH}

    from mcp_forms.schema.parser import parse_xcore

    schema = parse_xcore(xcore_path)

    return {
        "source": str(xcore_path),
        "package": schema.package,
        "ns_uri": schema.ns_uri,
        "classes_count": schema.class_count,
        "enums_count": schema.enum_count,
        "imports_count": len(schema.imports),
        "class_names": sorted(schema.classes.keys()),
        "enum_names": sorted(schema.enums.keys()),
    }
