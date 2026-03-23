"""MCP-инструменты интеграции с EDT."""

from __future__ import annotations

from mcp_forms.edt_client import get_edt_client, EDTClient, MetadataInfo


def _client(edt_url: str = "") -> EDTClient:
    """Получить EDT-клиент: с указанным URL или глобальный."""
    if edt_url:
        return EDTClient(url=edt_url, enabled=True)
    return get_edt_client()


def get_edt_status(edt_url: str = "") -> dict:
    """Проверить статус EDT MCP сервера.

    Returns:
        dict с ключами: available, enabled, url
    """
    client = _client(edt_url)
    return {
        "enabled": client.enabled,
        "url": client.url,
        "available": client.is_available() if client.enabled else False,
    }


def get_object_metadata(object_type: str, object_name: str, edt_url: str = "") -> dict:
    """Получить метаданные объекта 1С из EDT для генерации формы.

    Возвращает реквизиты, табличные части, стандартные реквизиты — всё,
    что нужно для автозаполнения формы.

    Args:
        object_type: тип объекта (Catalog, Document, DataProcessor, Справочник, Документ...)
        object_name: имя объекта (Номенклатура, ПоступлениеТоваров...)
        edt_url: URL EDT MCP сервера (если не указан — берётся из настроек)

    Returns:
        dict с ключами: success, fqn, attributes, table_parts, datapaths
    """
    client = _client(edt_url)

    if not client.enabled:
        return {
            "success": False,
            "error": "EDT MCP не включён. Установите EDT_ENABLED=true",
        }

    info = client.get_metadata_details(object_type, object_name)
    if info is None:
        return {
            "success": False,
            "error": f"Не удалось получить метаданные {object_type}.{object_name} из EDT",
        }

    return _metadata_to_dict(info)


def validate_form_with_edt(xml_content: str, form_fqn: str = "", edt_url: str = "") -> dict:
    """Валидировать форму через EDT (дополнительно к встроенной валидации).

    Вызывает get_project_errors для формы. Если form_fqn не указан,
    выполняет только встроенную валидацию.

    Args:
        xml_content: содержимое Form.xml
        form_fqn: FQN формы в проекте (напр. Catalog.Номенклатура.Form.ФормаЭлемента)

    Returns:
        dict с ключами: success, builtin_result, edt_errors
    """
    # Встроенная валидация
    from mcp_forms.tools.validate import validate_form as _builtin_validate
    builtin = _builtin_validate(xml_content)

    result = {
        "success": True,
        "builtin_result": builtin,
        "edt_errors": [],
        "edt_available": False,
    }

    client = _client(edt_url)
    if not client.enabled or not form_fqn:
        return result

    # EDT валидация
    errors = client.get_project_errors(objects=[form_fqn])
    if errors is not None:
        result["edt_available"] = True
        result["edt_errors"] = [
            {
                "message": e.message,
                "severity": e.severity,
                "line": e.line,
                "check_id": e.check_id,
            }
            for e in errors
        ]

    return result


def get_form_screenshot(form_fqn: str, edt_url: str = "") -> dict:
    """Получить скриншот формы из EDT WYSIWYG-редактора.

    Args:
        form_fqn: FQN формы (напр. Catalog.Номенклатура.Form.ФормаЭлемента)
        edt_url: URL EDT MCP сервера (если не указан — берётся из настроек)

    Returns:
        dict с ключами: success, screenshot_base64
    """
    client = _client(edt_url)

    if not client.enabled:
        return {
            "success": False,
            "error": "EDT MCP не включён. Установите EDT_ENABLED=true",
        }

    screenshot = client.get_form_screenshot(form_fqn)
    if screenshot is None:
        return {
            "success": False,
            "error": f"Не удалось получить скриншот формы {form_fqn}",
        }

    return {
        "success": True,
        "screenshot_base64": screenshot,
        "form_fqn": form_fqn,
    }


def generate_form_spec_from_metadata(
    object_type: str,
    object_name: str,
    form_type: str = "ФормаЭлемента",
    format: str = "logform",
    include_table_parts: bool = True,
    edt_url: str = "",
) -> dict:
    """Сгенерировать спецификацию формы на основе метаданных из EDT.

    Автоматически заполняет реквизиты, табличные части и DataPath.

    Args:
        object_type: тип объекта (Catalog, Document...)
        object_name: имя объекта
        form_type: тип формы (ФормаЭлемента, ФормаДокумента...)
        format: формат XML (logform, managed)
        include_table_parts: включать табличные части

    Returns:
        dict со спецификацией для generate_form или ошибкой
    """
    client = _client(edt_url)

    if not client.enabled:
        return {
            "success": False,
            "error": "EDT MCP не включён. Установите EDT_ENABLED=true",
        }

    info = client.get_metadata_details(object_type, object_name)
    if info is None:
        return {
            "success": False,
            "error": f"Не удалось получить метаданные {object_type}.{object_name}",
        }

    spec = _build_form_spec(info, form_type, format, include_table_parts)
    return {
        "success": True,
        "spec": spec,
        "metadata": _metadata_to_dict(info),
    }


def _metadata_to_dict(info: MetadataInfo) -> dict:
    """Конвертировать MetadataInfo в dict."""
    return {
        "success": True,
        "fqn": info.fqn,
        "object_type": info.object_type,
        "object_name": info.object_name,
        "synonym": info.synonym,
        "attributes": [
            {"name": a.name, "type": a.type_name, "synonym": a.synonym}
            for a in info.attributes
        ],
        "table_parts": [
            {
                "name": tp.name,
                "synonym": tp.synonym,
                "attributes": [
                    {"name": a.name, "type": a.type_name, "synonym": a.synonym}
                    for a in tp.attributes
                ],
            }
            for tp in info.table_parts
        ],
        "standard_attributes": info.standard_attributes,
        "datapaths": info.get_all_datapaths(),
    }


def _build_form_spec(
    info: MetadataInfo,
    form_type: str,
    format: str,
    include_table_parts: bool,
) -> dict:
    """Построить спецификацию формы из метаданных."""
    # Определяем тип для реквизита формы
    type_prefix = "cfg:" if format == "logform" else ""
    obj_type_name = f"{type_prefix}{info.object_type}Object.{info.object_name}"

    spec: dict = {
        "format": format,
        "object_type": info.object_type,
        "object_name": info.object_name,
        "form_type": form_type,
        "title": info.synonym or info.object_name,
        "attributes": [
            {
                "name": "Объект",
                "type_name": obj_type_name,
                "is_main": True,
                "save_data": True,
            }
        ],
        "elements": [],
    }

    # Стандартные реквизиты как поля
    for std_attr in info.standard_attributes:
        if std_attr in ("Ref", "Ссылка", "DeletionMark", "ПометкаУдаления", "Predefined", "Предопределенный"):
            continue
        spec["elements"].append({
            "name": std_attr,
            "data_path": f"Объект.{std_attr}",
            "field_type": "InputField",
        })

    # Реквизиты
    for attr in info.attributes:
        spec["elements"].append({
            "name": attr.name,
            "data_path": f"Объект.{attr.name}",
            "field_type": "InputField",
        })

    # Табличные части
    if include_table_parts:
        for tp in info.table_parts:
            table_spec: dict = {
                "name": tp.name,
                "data_path": f"Объект.{tp.name}",
                "columns": [],
            }
            for attr in tp.attributes:
                table_spec["columns"].append({
                    "name": attr.name,
                    "data_path": f"Объект.{tp.name}.{attr.name}",
                })
            spec["elements"].append(table_spec)

    return spec
