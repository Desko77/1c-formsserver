"""FastMCP сервер для работы с формами 1С."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_forms.tools.validate import validate_form as _validate_form, get_form_info as _get_form_info
from mcp_forms.tools.schema import get_form_schema as _get_form_schema, get_form_prompt as _get_form_prompt, get_xcore_model_info as _get_xcore_model_info
from mcp_forms.tools.generate import generate_form_from_spec as _generate_form, generate_form_template as _generate_template, list_templates as _list_templates
from mcp_forms.tools.convert import convert_form as _convert_form
from mcp_forms.tools.search import search_form_examples as _search_forms, index_forms_from_directory as _index_forms, get_form_example as _get_form_example
from mcp_forms.tools.edt import (
    get_edt_status as _get_edt_status,
    get_object_metadata as _get_object_metadata,
    validate_form_with_edt as _validate_form_edt,
    get_form_screenshot as _get_form_screenshot,
    generate_form_spec_from_metadata as _gen_spec_from_metadata,
)

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


# =================== Конвертация ===================


@mcp.tool()
def convert_form(xml_content: str, target_format: str) -> dict:
    """Конвертировать Form.xml между форматами logform и managed.

    Logform (конфигуратор) ↔ Managed (EDT).
    Формат исходного XML определяется автоматически.

    Ключевые отличия форматов:
    - Logform: name/id как XML-атрибуты, ContextMenu/ExtendedTooltip обязательны, 17 namespace-ов
    - Managed: Name/Id как дочерние элементы, без companion-элементов, 4 namespace-а

    Args:
        xml_content: содержимое Form.xml
        target_format: целевой формат ("logform" или "managed")
    """
    return _convert_form(xml_content, target_format)


# =================== Поиск ===================


@mcp.tool()
def search_form_examples(
    query: str,
    mode: str = "fts",
    limit: int = 5,
    include_code: bool = False,
) -> dict:
    """Поиск примеров форм по текстовому запросу.

    Ищет в базе проиндексированных Form.xml по описанию, типу объекта, имени формы.
    Режимы: fts (полнотекстовый), vector (по эмбеддингам), auto (vector если доступен).

    Args:
        query: поисковый запрос (напр. "форма документа с табличной частью")
        mode: режим поиска ("fts", "vector", "auto")
        limit: максимум результатов
        include_code: включить XML-код формы в результат
    """
    return _search_forms(query, mode, limit, include_code)


@mcp.tool()
def index_forms(directory: str, pattern: str = "**/Form.xml") -> dict:
    """Индексировать Form.xml файлы из директории конфигурации 1С.

    Сканирует директорию, находит Form.xml файлы и добавляет их в базу поиска.
    Автоматически определяет тип объекта (Catalog, Document...) по пути.

    Args:
        directory: путь к директории с конфигурацией
        pattern: glob-паттерн для поиска файлов
    """
    return _index_forms(directory, pattern)


@mcp.tool()
def get_form_example(form_id: int) -> dict:
    """Получить XML-код примера формы по его id.

    Используется после search_form_examples для получения полного XML
    конкретного примера.

    Args:
        form_id: id записи из результатов поиска
    """
    return _get_form_example(form_id)


# =================== EDT интеграция ===================


@mcp.tool()
def edt_status() -> dict:
    """Проверить статус подключения к EDT MCP серверу.

    Возвращает: включён ли EDT, URL сервера, доступен ли.
    Настройка: переменные окружения EDT_ENABLED, EDT_MCP_URL.
    """
    return _get_edt_status()


@mcp.tool()
def get_object_metadata(object_type: str, object_name: str) -> dict:
    """Получить метаданные объекта 1С из EDT для генерации формы.

    Возвращает реквизиты, табличные части, стандартные реквизиты
    и все допустимые DataPath для формы.

    Требует: EDT MCP (EDT_ENABLED=true).

    Args:
        object_type: тип (Catalog, Document, DataProcessor, Справочник, Документ...)
        object_name: имя (Номенклатура, ПоступлениеТоваров...)
    """
    return _get_object_metadata(object_type, object_name)


@mcp.tool()
def validate_form_edt(xml_content: str, form_fqn: str = "") -> dict:
    """Валидировать форму встроенной + EDT валидацией.

    Выполняет структурную валидацию (всегда) и дополнительную проверку
    через EDT get_project_errors (если form_fqn указан и EDT доступен).

    Args:
        xml_content: содержимое Form.xml
        form_fqn: FQN формы в проекте (напр. Catalog.Номенклатура.Form.ФормаЭлемента)
    """
    return _validate_form_edt(xml_content, form_fqn)


@mcp.tool()
def form_screenshot(form_fqn: str) -> dict:
    """Получить скриншот формы из EDT WYSIWYG-редактора.

    Требует: EDT MCP (EDT_ENABLED=true) и открытый проект в EDT.

    Args:
        form_fqn: FQN формы (напр. Catalog.Номенклатура.Form.ФормаЭлемента)
    """
    return _get_form_screenshot(form_fqn)


@mcp.tool()
def generate_form_from_metadata(
    object_type: str,
    object_name: str,
    form_type: str = "ФормаЭлемента",
    format: str = "logform",
    include_table_parts: bool = True,
) -> dict:
    """Сгенерировать спецификацию формы автоматически из метаданных EDT.

    Получает реквизиты и табличные части объекта из EDT,
    и строит готовую спецификацию для generate_form.

    Требует: EDT MCP (EDT_ENABLED=true).

    Args:
        object_type: тип объекта (Catalog, Document...)
        object_name: имя объекта
        form_type: тип формы (ФормаЭлемента, ФормаДокумента...)
        format: формат XML (logform, managed)
        include_table_parts: включать табличные части
    """
    return _gen_spec_from_metadata(object_type, object_name, form_type, format, include_table_parts)


# =================== Info ===================


@mcp.tool()
def get_server_info() -> dict:
    """Информация о сервере и доступных инструментах."""
    from mcp_forms import __version__

    tools = []
    try:
        tools = [t.name for t in mcp._tool_manager._tools.values()]
    except AttributeError:
        try:
            tools = [t.name for t in mcp.get_tools()]
        except Exception:
            tools = ["(unable to list)"]

    return {
        "name": "mcp-forms-server",
        "version": __version__,
        "supported_formats": ["logform", "managed"],
        "tools": tools,
        "tools_count": len(tools),
    }
