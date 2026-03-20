"""MCP-инструмент конвертации Form.xml между форматами."""

from __future__ import annotations

from mcp_forms.forms.converter import convert_form as _convert
from mcp_forms.forms.loader import detect_format


def convert_form(xml_content: str, target_format: str) -> dict:
    """Конвертировать Form.xml между форматами.

    Args:
        xml_content: содержимое Form.xml / Form.form
        target_format: целевой формат:
            - "logform" — формат Конфигуратора (<Form xmlns="...xcf/logform">)
            - "managed" — упрощённый формат (<ManagedForm>)
            - "edt" — формат EDT (<form:Form xmlns:form="...dt/form">)

    Returns:
        dict с ключами: xml, source_format, target_format, success, errors
    """
    source_format = detect_format(xml_content)

    if source_format == "unknown":
        return {
            "success": False,
            "errors": ["Не удалось определить формат исходного XML"],
            "xml": "",
            "source_format": "unknown",
            "target_format": target_format,
        }

    if source_format == target_format:
        return {
            "success": False,
            "errors": [f"Форма уже в формате {target_format}"],
            "xml": "",
            "source_format": source_format,
            "target_format": target_format,
        }

    try:
        result_xml = _convert(xml_content, target_format)
        return {
            "success": True,
            "errors": [],
            "xml": result_xml,
            "source_format": source_format,
            "target_format": target_format,
        }
    except Exception as e:
        return {
            "success": False,
            "errors": [str(e)],
            "xml": "",
            "source_format": source_format,
            "target_format": target_format,
        }
