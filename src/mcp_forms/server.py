"""FastMCP сервер для работы с формами 1С."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_forms.tools.validate import validate_form as _validate_form, get_form_info as _get_form_info
from mcp_forms.tools.schema import get_form_schema as _get_form_schema, get_form_prompt as _get_form_prompt, get_xcore_model_info as _get_xcore_model_info
from mcp_forms.tools.generate import generate_form_from_spec as _generate_form, generate_form_template as _generate_template, list_templates as _list_templates

mcp = FastMCP(
    "mcp-forms-server",
    instructions=(
        "MCP-сервер для генерации, валидации и поиска управляемых форм 1С (Form.xml). "
        "Поддерживает форматы EDT (xcf/managed) и Конфигуратор (xcf/logform)."
    ),
)


# =================== Валидация ===================


@mcp.tool()
def validate_form(xml_content: str) -> dict:
    """Валидировать XML-форму 1С.

    Проверяет структурную корректность Form.xml:
    - Формат (logform/managed) определяется автоматически
    - Уникальность id элементов и атрибутов
    - Обязательные дочерние элементы (ContextMenu, ExtendedTooltip)
    - Дубликаты имён атрибутов
    - Привязка DataPath к Attribute

    Args:
        xml_content: Содержимое Form.xml
    """
    return _validate_form(xml_content)


@mcp.tool()
def get_form_info(xml_content: str) -> dict:
    """Получить информацию о структуре Form.xml.

    Возвращает: формат, версию, количество элементов, атрибутов, команд,
    типы элементов и имена атрибутов.

    Args:
        xml_content: Содержимое Form.xml
    """
    return _get_form_info(xml_content)


# =================== Схема ===================


@mcp.tool()
def get_form_schema() -> dict:
    """Получить JSON-схему элементов формы 1С.

    Возвращает описание элементов (InputField, Table, UsualGroup и др.),
    их свойств и типов данных.
    """
    return _get_form_schema()


@mcp.tool()
def get_form_prompt() -> str:
    """Получить промпт с полной базой знаний по тегам и атрибутам Form.xml.

    Содержит все допустимые теги, атрибуты, значения и правила валидации.
    Используется как контекст для LLM при генерации форм.
    """
    return _get_form_prompt()


@mcp.tool()
def get_xcore_model_info() -> dict:
    """Получить информацию о Xcore-модели форм из EDT 2025.2.

    Возвращает: количество классов, enum-ов, список имён.
    Xcore — первоисточник модели данных управляемых форм 1С.
    """
    return _get_xcore_model_info()


# =================== Генерация ===================


@mcp.tool()
def generate_form(spec: dict) -> dict:
    """Сгенерировать Form.xml по JSON-спецификации.

    Спецификация — словарь с полями:
    - format: "logform" (по умолчанию) или "managed"
    - attributes: [{name, type_name, is_main, save_data}]
    - elements: [{name, data_path, field_type}]
      - Для групп: {name, group_type, direction, children: [...]}
      - Для таблиц: {name, data_path, columns: [{name, data_path}]}

    Args:
        spec: JSON-спецификация формы
    """
    return _generate_form(spec)


@mcp.tool()
def generate_form_template(
    template: str,
    object_name: str,
    fields: list[str] | None = None,
    format: str = "logform",
    table_name: str = "",
    table_columns: list[str] | None = None,
) -> dict:
    """Сгенерировать Form.xml из типового шаблона.

    Шаблоны: catalog_element, document, data_processor.

    Args:
        template: имя шаблона
        object_name: имя объекта (Номенклатура, ПоступлениеТоваров...)
        fields: поля шапки
        format: "logform" или "managed"
        table_name: имя ТЧ (для document)
        table_columns: колонки ТЧ (для document)
    """
    return _generate_template(template, object_name, fields, format, table_name, table_columns)


@mcp.tool()
def list_form_templates() -> dict:
    """Список доступных шаблонов форм с описаниями и параметрами."""
    return _list_templates()


# =================== Info ===================


@mcp.tool()
def get_server_info() -> dict:
    """Информация о сервере и доступных инструментах."""
    from mcp_forms import __version__

    return {
        "name": "mcp-forms-server",
        "version": __version__,
        "supported_formats": ["logform", "managed"],
        "tools": [t.name for t in mcp._tool_manager._tools.values()],
    }
