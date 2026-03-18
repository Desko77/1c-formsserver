"""MCP-инструмент конвертации Form.xml между форматами."""

from __future__ import annotations

from mcp_forms.forms.converter import convert_form as _convert
from mcp_forms.forms.loader import detect_format


def convert_form(xml_content: str, target_format: str) -> dict:
    """Конвертировать Form.xml между форматами logform и managed.

    Args:
        xml_content: содержимое Form.xml
        target_format: целевой формат ("logform", "edt" или "managed")
            - "logform" / "edt" — формат EDT и Конфигуратора (<Form>)
            - "managed" — упрощённый формат (<ManagedForm>)

    Returns:
        dict с ключами: xml, source_format, target_format, success, errors
    """
    # "edt" — алиас для "logform" (EDT использует logform-формат для Form.xml)
    effective_format = "logform" if target_format == "edt" else target_format

    source_format = detect_format(xml_content)

    if source_format == "unknown":
        return {
            "success": False,
            "errors": ["Не удалось определить формат исходного XML"],
            "xml": "",
            "source_format": "unknown",
            "target_format": target_format,
        }

    if source_format == effective_format:
        return {
            "success": False,
            "errors": [f"Форма уже в формате {target_format} ({effective_format})"],
            "xml": "",
            "source_format": source_format,
            "target_format": target_format,
        }

    try:
        result_xml = _convert(xml_content, effective_format)
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
