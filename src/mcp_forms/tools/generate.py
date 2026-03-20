"""MCP-инструменты генерации форм."""

from __future__ import annotations

from mcp_forms.forms.generator import (
    FormAttributeSpec,
    FormFieldSpec,
    FormGroupSpec,
    FormSpec,
    FormTableColumnSpec,
    FormTableSpec,
    generate_form,
)
from mcp_forms.forms.templates import TEMPLATE_REGISTRY


def generate_form_from_spec(spec: dict) -> dict:
    """Сгенерировать Form.xml по JSON-спецификации.

    Спецификация — словарь с полями:
    - format: "logform" (по умолчанию) или "managed"
    - object_type: "Catalog", "Document", "DataProcessor"
    - object_name: имя объекта метаданных
    - form_type: "ФормаЭлемента", "ФормаДокумента" и т.д.
    - title: заголовок формы (опционально)
    - attributes: список атрибутов [{name, type_name, is_main, save_data}]
    - elements: список элементов [{name, data_path, field_type, title}]
      - field_type: "InputField" (по умолчанию), "CheckBoxField", "LabelField"...
      - Для групп: {name, group_type, direction, children: [...]}
      - Для таблиц: {name, data_path, columns: [{name, data_path}]}

    Returns:
        dict с полями: xml (строка Form.xml), format, elements_count
    """
    try:
        form_spec = _dict_to_spec(spec)
        xml = generate_form(form_spec)
        return {
            "xml": xml,
            "format": form_spec.format,
            "elements_count": _count_elements(form_spec),
        }
    except Exception as exc:
        return {"error": str(exc)}


def generate_form_template(
    template: str,
    object_name: str,
    fields: list[str] | None = None,
    format: str = "logform",
    table_name: str = "",
    table_columns: list[str] | None = None,
) -> dict:
    """Сгенерировать Form.xml из типового шаблона.

    Доступные шаблоны:
    - "catalog_element" — форма элемента справочника
    - "document" — форма документа (с табличной частью)
    - "data_processor" — форма обработки

    Args:
        template: имя шаблона
        object_name: имя объекта метаданных (Номенклатура, ПоступлениеТоваров...)
        fields: список полей шапки
        format: "logform" или "managed"
        table_name: имя ТЧ (для document)
        table_columns: колонки ТЧ (для document)

    Returns:
        dict с полями: xml, format, template
    """
    factory = TEMPLATE_REGISTRY.get(template)
    if not factory:
        return {
            "error": "Неизвестный шаблон: '%s'. Доступные: %s"
            % (template, ", ".join(TEMPLATE_REGISTRY.keys()))
        }

    kwargs: dict = {"format": format}
    if fields is not None:
        # document_form uses header_fields, others use fields
        param_name = "header_fields" if template == "document" else "fields"
        kwargs[param_name] = fields
    if template == "document":
        if table_name:
            kwargs["table_name"] = table_name
        if table_columns:
            kwargs["table_columns"] = table_columns

    try:
        spec = factory(object_name, **kwargs)
        xml = generate_form(spec)
        return {"xml": xml, "format": format, "template": template}
    except Exception as exc:
        return {"error": str(exc)}


def list_templates() -> dict:
    """Список доступных шаблонов форм.

    Returns:
        dict с описанием каждого шаблона
    """
    return {
        "templates": {
            "catalog_element": {
                "description": "Форма элемента справочника",
                "params": ["object_name", "fields", "format"],
            },
            "document": {
                "description": "Форма документа с табличной частью",
                "params": ["object_name", "fields", "format", "table_name", "table_columns"],
            },
            "data_processor": {
                "description": "Форма обработки",
                "params": ["object_name", "fields", "format"],
            },
        }
    }


# =================== Helpers ===================


def _dict_to_spec(d: dict) -> FormSpec:
    """Конвертирует словарь в FormSpec."""
    _attr_fields = {f.name for f in FormAttributeSpec.__dataclass_fields__.values()}
    attributes = [
        FormAttributeSpec(**{k: v for k, v in a.items() if k in _attr_fields})
        for a in d.get("attributes", [])
    ]
    elements = [_dict_to_element(e) for e in d.get("elements", [])]

    return FormSpec(
        object_type=d.get("object_type", ""),
        object_name=d.get("object_name", ""),
        form_type=d.get("form_type", ""),
        title=d.get("title", ""),
        attributes=attributes,
        elements=elements,
        format=d.get("format", "logform"),
    )


def _dict_to_element(d: dict) -> FormFieldSpec | FormGroupSpec | FormTableSpec:
    """Конвертирует словарь в спецификацию элемента."""
    _col_fields = {f.name for f in FormTableColumnSpec.__dataclass_fields__.values()}
    if "columns" in d:
        return FormTableSpec(
            name=d["name"],
            data_path=d.get("data_path", ""),
            columns=[
                FormTableColumnSpec(**{k: v for k, v in c.items() if k in _col_fields})
                for c in d["columns"]
            ],
        )
    if "children" in d:
        return FormGroupSpec(
            name=d["name"],
            title=d.get("title", ""),
            group_type=d.get("group_type", "UsualGroup"),
            direction=d.get("direction", "Vertical"),
            children=[_dict_to_element(c) for c in d["children"]],
        )
    return FormFieldSpec(
        name=d["name"],
        data_path=d.get("data_path", ""),
        field_type=d.get("field_type", "InputField"),
        title=d.get("title", ""),
        read_only=d.get("read_only", False),
    )


def _count_elements(spec: FormSpec) -> int:
    count = 0
    for e in spec.elements:
        count += _count_element(e)
    return count


def _count_element(e: FormFieldSpec | FormGroupSpec | FormTableSpec) -> int:
    if isinstance(e, FormGroupSpec):
        return 1 + sum(_count_element(c) for c in e.children)
    if isinstance(e, FormTableSpec):
        return 1 + len(e.columns)
    return 1
