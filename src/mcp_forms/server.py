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
        "Сервер для работы с управляемыми формами 1С (Form.xml). "
        "Три формата: logform (Конфигуратор), managed (упрощённый), edt (EDT form:Form).\n\n"
        "Типовой workflow генерации формы:\n"
        "1. get_form_prompt(format) — загрузить базу знаний (обязательно перед генерацией).\n"
        "   Для EDT-проектов: format='edt', для Конфигуратора: format='logform' (по умолчанию)\n"
        "2. search_form_examples — найти похожий пример как образец\n"
        "3. generate_form_template (типовая форма) или generate_form (произвольная спецификация)\n"
        "4. validate_form — проверить результат\n\n"
        "Если подключён EDT (edt_status), доступен расширенный workflow:\n"
        "1. get_form_prompt(format='edt') — загрузить EDT-базу знаний\n"
        "2. get_object_metadata — получить реквизиты объекта из проекта\n"
        "3. generate_form_from_metadata — автогенерация спецификации\n"
        "4. validate_form_edt — валидация с проверками EDT\n\n"
        "Конвертация между форматами: convert_form."
    ),
)


# =================== Валидация ===================


@mcp.tool()
def validate_form(xml_content: str) -> dict:
    """Проверить Form.xml на ошибки. Вызывай ПОСЛЕ каждой генерации или ручной правки формы.

    Формат (logform/managed) определяется автоматически.
    Проверки: уникальность id, обязательные дочерние элементы (ContextMenu, ExtendedTooltip
    в logform), дубликаты имён атрибутов, привязка DataPath к Attribute.

    Возвращает {valid: bool, errors: [...], warnings: [...]}.

    Args:
        xml_content: содержимое Form.xml целиком
    """
    return _validate_form(xml_content)


@mcp.tool()
def get_form_info(xml_content: str) -> dict:
    """Быстрый обзор существующей Form.xml — формат, структура, статистика.

    Вызывай когда нужно понять что внутри формы перед её модификацией или конвертацией.
    Возвращает: формат (logform/managed), количество элементов/атрибутов/команд,
    типы элементов и имена атрибутов.

    Args:
        xml_content: содержимое Form.xml целиком
    """
    return _get_form_info(xml_content)


# =================== Схема ===================


@mcp.tool()
def get_form_schema() -> dict:
    """Справочник элементов формы — какие теги, свойства и типы данных допустимы в Form.xml.

    Вызывай когда нужно узнать допустимые свойства конкретного элемента (InputField,
    Table, UsualGroup и др.) или проверить, какие значения принимает атрибут.
    Для полной базы знаний по генерации используй get_form_prompt.
    """
    return _get_form_schema()


@mcp.tool()
def get_form_prompt(format: str = "logform") -> str:
    """Полная база знаний по Form.xml — теги, атрибуты, допустимые значения, правила.

    ОБЯЗАТЕЛЬНО вызывай перед первой генерацией формы в сессии. Загружает контекст,
    необходимый для корректного построения Form.xml. Без этого контекста генерация
    будет содержать ошибки в именах тегов и значениях атрибутов.
    Достаточно вызвать один раз за сессию.

    Формат выбирай в зависимости от целевого формата генерации:
    - "logform" — формат Конфигуратора (<Form xmlns="...xcf/logform">), по умолчанию
    - "managed" — упрощённый формат (использует ту же базу знаний что logform)
    - "edt" — формат EDT (<form:Form xmlns:form="...dt/form">), для EDT-проектов

    Args:
        format: "logform" (по умолчанию), "managed" или "edt"
    """
    return _get_form_prompt(format=format)


@mcp.tool()
def get_xcore_model_info() -> dict:
    """Метамодель форм EDT — список всех классов и перечислений из Xcore.

    Вызывай для получения полного перечня типов элементов формы и enum-значений,
    определённых в EDT 2025.2. Полезно при отладке ошибок валидации
    или когда нужно уточнить допустимые типы.
    """
    return _get_xcore_model_info()


# =================== Генерация ===================


@mcp.tool()
def generate_form(spec: dict) -> dict:
    """Сгенерировать Form.xml по произвольной JSON-спецификации.

    Используй для нестандартных форм, когда шаблоны (generate_form_template) не подходят.
    Перед вызовом загрузи базу знаний через get_form_prompt.

    Структура spec:
    - format: "logform" (по умолчанию), "managed" или "edt"
    - attributes: [{name, type_name, is_main, save_data}] — реквизиты формы
    - elements: [{name, data_path, field_type}] — поля ввода
      - Группа: {name, group_type, direction, children: [...]}
      - Таблица: {name, data_path, columns: [{name, data_path}]}

    После генерации обязательно вызови validate_form для проверки результата.

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
    """Быстрая генерация типовой Form.xml по шаблону. Начинай с этого инструмента.

    Подходит для стандартных форм справочников, документов, обработок.
    Для нестандартных форм используй generate_form.
    Список шаблонов: list_form_templates.

    Основные шаблоны:
    - catalog_element — форма элемента справочника
    - document — форма документа (с табличной частью)
    - data_processor — форма обработки

    После генерации обязательно вызови validate_form.

    Args:
        template: имя шаблона (catalog_element, document, data_processor)
        object_name: имя объекта 1С (Номенклатура, ПоступлениеТоваров...)
        fields: реквизиты шапки (["Организация", "Контрагент", "Сумма"])
        format: "logform" (по умолчанию), "managed" или "edt". 
        table_name: имя табличной части (для шаблона document)
        table_columns: колонки табличной части (["Номенклатура", "Количество", "Цена"])
    """
    return _generate_template(template, object_name, fields, format, table_name, table_columns)


@mcp.tool()
def list_form_templates() -> dict:
    """Список доступных шаблонов для generate_form_template — имена, описания, параметры."""
    return _list_templates()


# =================== Конвертация ===================


@mcp.tool()
def convert_form(xml_content: str, target_format: str) -> dict:
    """Конвертировать Form.xml между форматами.

    Формат исходного XML определяется автоматически.
    Вызывай когда форма в одном формате, а нужна в другом.

    Args:
        xml_content: содержимое Form.xml целиком
        target_format: целевой формат:
            - "logform" — формат Конфигуратора (<Form xmlns="...xcf/logform">)
            - "edt" — формат EDT (<form:Form xmlns:form="...dt/form">)
            - "managed" — упрощённый формат (<ManagedForm>), НЕ для EDT
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
    """Найти примеры Form.xml в базе знаний как образец для генерации.

    Вызывай перед генерацией, чтобы найти похожую форму и использовать как референс.
    Сначала получи список (include_code=false), затем загрузи XML нужного примера
    через get_form_example.

    Args:
        query: что ищем ("форма документа с табличной частью", "справочник с иерархией")
        mode: "fts" (по умолчанию, полнотекстовый поиск по ключевым словам)
        limit: максимум результатов (по умолчанию 5)
        include_code: true — вернуть XML-код сразу (может быть большим)
    """
    return _search_forms(query, mode, limit, include_code)


@mcp.tool()
def index_forms(directory: str, pattern: str = "**/Form.xml") -> dict:
    """Добавить Form.xml из директории конфигурации в базу поиска (search_form_examples).

    Сканирует директорию, находит Form.xml и индексирует для последующего поиска.
    Тип объекта (Catalog, Document...) определяется автоматически по пути к файлу.

    Args:
        directory: путь к директории с конфигурацией 1С (исходники EDT)
        pattern: glob-паттерн (по умолчанию "**/Form.xml")
    """
    return _index_forms(directory, pattern)


@mcp.tool()
def get_form_example(form_id: int) -> dict:
    """Загрузить полный XML-код примера формы. Вызывай после search_form_examples.

    Args:
        form_id: id из результатов search_form_examples
    """
    return _get_form_example(form_id)


# =================== EDT интеграция ===================


@mcp.tool()
def edt_status(edt_url: str = "") -> dict:
    """Проверить доступность EDT. Вызывай перед использованием EDT-инструментов.

    Возвращает: включён ли EDT, URL, доступен ли сервер.
    Если EDT недоступен — инструменты get_object_metadata, validate_form_edt,
    form_screenshot, generate_form_from_metadata не будут работать.

    Args:
        edt_url: URL EDT MCP сервера (напр. "http://localhost:9999/sse"). Если не указан — из настроек.
    """
    return _get_edt_status(edt_url)


@mcp.tool()
def get_object_metadata(object_type: str, object_name: str, edt_url: str = "") -> dict:
    """Получить реквизиты и табличные части объекта 1С из EDT — для построения спецификации формы.

    Возвращает все допустимые DataPath для формы: реквизиты, ТЧ, стандартные реквизиты.
    Требует подключения к EDT (проверь через edt_status).

    Args:
        object_type: тип объекта (Catalog, Document, DataProcessor)
        object_name: имя объекта (Номенклатура, ПоступлениеТоваров...)
        edt_url: URL EDT MCP сервера (напр. "http://localhost:9999/sse"). Если не указан — из настроек.
    """
    return _get_object_metadata(object_type, object_name, edt_url)


@mcp.tool()
def validate_form_edt(xml_content: str, form_fqn: str = "", edt_url: str = "") -> dict:
    """Расширенная валидация формы: встроенные проверки + проверки EDT.

    Всегда выполняет структурную валидацию (как validate_form).
    Дополнительно, если указан form_fqn и EDT доступен — проверяет через EDT
    (типы данных, ссылки на метаданные, совместимость).
    Требует подключения к EDT (проверь через edt_status).

    Args:
        xml_content: содержимое Form.xml целиком
        form_fqn: FQN формы в проекте (напр. "Catalog.Номенклатура.Form.ФормаЭлемента")
        edt_url: URL EDT MCP сервера. Если не указан — из настроек.
    """
    return _validate_form_edt(xml_content, form_fqn, edt_url)


@mcp.tool()
def form_screenshot(form_fqn: str, edt_url: str = "") -> dict:
    """Скриншот формы из WYSIWYG-редактора EDT — для визуальной проверки результата.

    Требует подключения к EDT (проверь через edt_status) и открытый проект.

    Args:
        form_fqn: FQN формы (напр. "Catalog.Номенклатура.Form.ФормаЭлемента")
        edt_url: URL EDT MCP сервера. Если не указан — из настроек.
    """
    return _get_form_screenshot(form_fqn, edt_url)


@mcp.tool()
def generate_form_from_metadata(
    object_type: str,
    object_name: str,
    form_type: str = "ФормаЭлемента",
    format: str = "logform",
    include_table_parts: bool = True,
    edt_url: str = "",
) -> dict:
    """Автогенерация формы из метаданных EDT — самый быстрый способ при наличии EDT.

    Читает реквизиты и ТЧ объекта из EDT и строит готовый Form.xml за один вызов.
    Эквивалент цепочки: get_object_metadata -> generate_form, но автоматически.
    Требует подключения к EDT (проверь через edt_status).

    Args:
        object_type: тип объекта (Catalog, Document, DataProcessor)
        object_name: имя объекта (Номенклатура, ПоступлениеТоваров...)
        form_type: тип формы ("ФормаЭлемента", "ФормаДокумента", "ФормаСписка")
        format: "logform" (по умолчанию), "managed" или "edt".
        include_table_parts: включать табличные части в форму (по умолчанию true)
        edt_url: URL EDT MCP сервера (напр. "http://localhost:9999/sse"). Если не указан — из настроек.
    """
    return _gen_spec_from_metadata(object_type, object_name, form_type, format, include_table_parts, edt_url)


# =================== Info ===================


@mcp.tool()
def get_server_info() -> dict:
    """Версия сервера и список инструментов. Не нужно вызывать для начала работы."""
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
        "supported_formats": ["logform", "managed", "edt"],
        "tools": tools,
        "tools_count": len(tools),
    }
