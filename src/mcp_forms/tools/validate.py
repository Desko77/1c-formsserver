"""MCP-инструменты валидации форм."""

from __future__ import annotations

from mcp_forms.forms.loader import load_form, detect_format, FormDocument
from mcp_forms.schema.validator import validate_form as _validate, ValidationResult


def validate_form(xml_content: str) -> dict:
    """Валидировать XML-форму 1С.

    Проверяет структурную корректность Form.xml:
    - Формат (logform / managed) определяется автоматически
    - Уникальность id элементов и атрибутов
    - Обязательные дочерние элементы (ContextMenu, ExtendedTooltip)
    - Дубликаты имён атрибутов
    - Привязка DataPath к Attribute
    - Наличие version

    Args:
        xml_content: Содержимое Form.xml (строка)

    Returns:
        dict с полями: valid, format, version, errors, warnings, details
    """
    try:
        doc = load_form(xml_content)
    except Exception as exc:
        return {
            "valid": False,
            "format": "unknown",
            "version": "",
            "errors": 1,
            "warnings": 0,
            "details": [
                {"severity": "error", "message": "Ошибка парсинга XML: %s" % exc, "element": ""}
            ],
        }

    result = _validate(doc)
    return result.to_dict()


def get_form_info(xml_content: str) -> dict:
    """Получить информацию о структуре Form.xml.

    Args:
        xml_content: Содержимое Form.xml (строка)

    Returns:
        dict с полями: format, version, elements_count, attributes_count,
        commands_count, element_types, attribute_names
    """
    try:
        doc = load_form(xml_content)
    except Exception as exc:
        return {"error": "Ошибка парсинга XML: %s" % exc}

    ns = doc.namespace

    def local(tag: str) -> str:
        return tag.split("}", 1)[1] if "}" in tag else tag

    # Подсчёт элементов формы
    element_types: dict[str, int] = {}
    form_element_tags = {
        "InputField", "LabelField", "CheckBoxField", "RadioButtonField",
        "SpreadSheetDocumentField", "TextDocumentField", "FormattedDocumentField",
        "HTMLDocumentField", "PictureField", "CalendarField", "ChartField",
        "ProgressBarField", "TrackBarField", "PDFDocumentField",
        "GraphicalSchemaField", "PictureDecoration", "LabelDecoration",
        "Table", "Button", "UsualGroup", "Pages", "Page", "ColumnGroup",
        "ButtonGroup", "CommandBar", "Popup",
    }
    for elem in doc.root.iter():
        tag = local(elem.tag)
        if tag in form_element_tags:
            element_types[tag] = element_types.get(tag, 0) + 1

    # Атрибуты
    attribute_names: list[str] = []
    for elem in doc.root.iter():
        if local(elem.tag) == "Attribute":
            name = elem.get("name", "")
            if name:
                attribute_names.append(name)

    # Команды
    commands_count = sum(1 for e in doc.root.iter() if local(e.tag) == "Command")

    total_elements = sum(element_types.values())

    return {
        "format": doc.format,
        "version": doc.version,
        "elements_count": total_elements,
        "attributes_count": len(attribute_names),
        "commands_count": commands_count,
        "element_types": element_types,
        "attribute_names": attribute_names,
    }
