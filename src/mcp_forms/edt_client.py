"""Клиент для взаимодействия с EDT MCP сервером.

Обёртка над HTTP-вызовами к 1c-edt MCP серверу.
Graceful degradation: если EDT недоступен, методы возвращают None.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from mcp_forms.config import EDT_MCP_URL, EDT_ENABLED, EDT_TIMEOUT

logger = logging.getLogger(__name__)

# Маппинг типов объектов для формирования FQN
OBJECT_TYPE_MAP = {
    "Catalog": "Catalog",
    "Document": "Document",
    "DataProcessor": "DataProcessor",
    "Report": "Report",
    "ChartOfAccounts": "ChartOfAccounts",
    "ChartOfCharacteristicTypes": "ChartOfCharacteristicTypes",
    "ChartOfCalculationTypes": "ChartOfCalculationTypes",
    "ExchangePlan": "ExchangePlan",
    "BusinessProcess": "BusinessProcess",
    "Task": "Task",
    "InformationRegister": "InformationRegister",
    "AccumulationRegister": "AccumulationRegister",
    "AccountingRegister": "AccountingRegister",
    "CalculationRegister": "CalculationRegister",
    # Русские синонимы
    "Справочник": "Catalog",
    "Документ": "Document",
    "Обработка": "DataProcessor",
    "Отчет": "Report",
    "Отчёт": "Report",
    "ПланСчетов": "ChartOfAccounts",
    "ПланВидовХарактеристик": "ChartOfCharacteristicTypes",
    "ПланВидовРасчета": "ChartOfCalculationTypes",
    "ПланОбмена": "ExchangePlan",
    "БизнесПроцесс": "BusinessProcess",
    "Задача": "Task",
    "РегистрСведений": "InformationRegister",
    "РегистрНакопления": "AccumulationRegister",
    "РегистрБухгалтерии": "AccountingRegister",
    "РегистрРасчета": "CalculationRegister",
}


@dataclass
class MetadataAttribute:
    """Реквизит объекта метаданных."""

    name: str
    type_name: str = ""
    synonym: str = ""


@dataclass
class MetadataTablePart:
    """Табличная часть объекта метаданных."""

    name: str
    synonym: str = ""
    attributes: list[MetadataAttribute] = field(default_factory=list)


@dataclass
class MetadataInfo:
    """Метаданные объекта 1С."""

    fqn: str  # Catalog.Номенклатура
    object_type: str  # Catalog
    object_name: str  # Номенклатура
    synonym: str = ""
    attributes: list[MetadataAttribute] = field(default_factory=list)
    table_parts: list[MetadataTablePart] = field(default_factory=list)
    standard_attributes: list[str] = field(default_factory=list)

    def get_all_datapaths(self, main_attr_name: str = "Объект") -> list[str]:
        """Получить все допустимые DataPath для формы.

        Args:
            main_attr_name: имя основного реквизита формы (обычно "Объект")

        Returns:
            Список DataPath (напр. ["Объект.Код", "Объект.Наименование", "Объект.Товары.Сумма"])
        """
        paths = []

        # Стандартные реквизиты
        for std in self.standard_attributes:
            paths.append(f"{main_attr_name}.{std}")

        # Реквизиты
        for attr in self.attributes:
            paths.append(f"{main_attr_name}.{attr.name}")

        # Табличные части и их реквизиты
        for tp in self.table_parts:
            paths.append(f"{main_attr_name}.{tp.name}")
            for attr in tp.attributes:
                paths.append(f"{main_attr_name}.{tp.name}.{attr.name}")

        return paths


@dataclass
class EDTError:
    """Ошибка из EDT."""

    message: str
    severity: str = "error"  # error, warning, info
    line: int = 0
    check_id: str = ""


class EDTClient:
    """Клиент для EDT MCP сервера."""

    def __init__(
        self,
        url: str | None = None,
        enabled: bool | None = None,
        timeout: int | None = None,
    ) -> None:
        self.url = url or EDT_MCP_URL
        self.enabled = enabled if enabled is not None else EDT_ENABLED
        self.timeout = timeout or EDT_TIMEOUT
        self._session = None

    def is_available(self) -> bool:
        """Проверить доступность EDT MCP сервера."""
        if not self.enabled:
            return False
        try:
            result = self._call_tool("get_edt_version", {})
            return result is not None
        except Exception:
            return False

    def get_metadata_details(
        self,
        object_type: str,
        object_name: str,
    ) -> MetadataInfo | None:
        """Получить метаданные объекта из EDT.

        Args:
            object_type: тип (Catalog, Document, DataProcessor...)
            object_name: имя (Номенклатура, ПоступлениеТоваров...)

        Returns:
            MetadataInfo или None если недоступно
        """
        eng_type = OBJECT_TYPE_MAP.get(object_type, object_type)
        fqn = f"{eng_type}.{object_name}"

        result = self._call_tool("get_metadata_details", {"fqn": fqn})
        if result is None:
            return None

        return self._parse_metadata(result, fqn, eng_type, object_name)

    def get_project_errors(
        self,
        objects: list[str] | None = None,
        severity: str = "ERROR",
    ) -> list[EDTError] | None:
        """Получить ошибки проекта из EDT.

        Args:
            objects: список FQN объектов для проверки (None = все)
            severity: минимальная серьёзность (ERROR, WARNING)

        Returns:
            список ошибок или None если недоступно
        """
        params: dict[str, Any] = {"severity": severity}
        if objects:
            params["objects"] = objects

        result = self._call_tool("get_project_errors", params)
        if result is None:
            return None

        errors = []
        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    errors.append(EDTError(
                        message=item.get("message", ""),
                        severity=item.get("severity", "error"),
                        line=item.get("line", 0),
                        check_id=item.get("checkId", ""),
                    ))
        return errors

    def get_form_screenshot(self, form_fqn: str) -> str | None:
        """Получить скриншот формы из EDT WYSIWYG-редактора.

        Args:
            form_fqn: FQN формы (напр. Catalog.Номенклатура.Form.ФормаЭлемента)

        Returns:
            base64-encoded PNG или None
        """
        result = self._call_tool("get_form_screenshot", {"fqn": form_fqn})
        if result is None:
            return None

        if isinstance(result, dict):
            return result.get("screenshot") or result.get("base64") or result.get("image")
        if isinstance(result, str):
            return result
        return None

    def validate_query(self, query_text: str, dcs_mode: bool = False) -> list[EDTError] | None:
        """Проверить запрос через EDT.

        Args:
            query_text: текст запроса 1С
            dcs_mode: режим СКД

        Returns:
            список ошибок или None
        """
        result = self._call_tool("validate_query", {
            "text": query_text,
            "dcsMode": dcs_mode,
        })
        if result is None:
            return None

        errors = []
        if isinstance(result, dict):
            for err in result.get("errors", []):
                if isinstance(err, dict):
                    errors.append(EDTError(
                        message=err.get("message", ""),
                        severity="error",
                        line=err.get("line", 0),
                    ))
                elif isinstance(err, str):
                    errors.append(EDTError(message=err))
        return errors

    def get_metadata_objects(self, type_filter: str = "") -> list[dict] | None:
        """Получить список объектов метаданных.

        Args:
            type_filter: фильтр по типу (Catalog, Document, ...)

        Returns:
            список объектов или None
        """
        params: dict[str, Any] = {}
        if type_filter:
            params["typeFilter"] = type_filter
        return self._call_tool("get_metadata_objects", params)

    def _call_tool(self, tool_name: str, params: dict) -> Any | None:
        """Вызвать инструмент EDT MCP сервера через HTTP.

        Returns:
            результат вызова или None если недоступен/ошибка
        """
        if not self.enabled:
            return None

        try:
            import urllib.request

            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": params,
                },
                "id": 1,
            }

            # Определяем URL для JSON-RPC
            base_url = self.url.rstrip("/")
            if base_url.endswith("/sse"):
                # SSE endpoint → переключаемся на JSON-RPC endpoint
                rpc_url = base_url.rsplit("/sse", 1)[0] + "/message"
            else:
                rpc_url = base_url

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                rpc_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                response = json.loads(resp.read().decode("utf-8"))

            if "result" in response:
                result = response["result"]
                # MCP tools/call возвращает {content: [{type: "text", text: "..."}]}
                if isinstance(result, dict) and "content" in result:
                    for item in result["content"]:
                        if isinstance(item, dict) and item.get("type") == "text":
                            try:
                                return json.loads(item["text"])
                            except (json.JSONDecodeError, TypeError):
                                return item["text"]
                return result

            if "error" in response:
                logger.warning("EDT MCP error: %s", response["error"])
                return None

        except Exception as e:
            logger.debug("EDT MCP call failed (%s): %s", tool_name, e)
            return None

        return None

    def _parse_metadata(
        self,
        raw: Any,
        fqn: str,
        object_type: str,
        object_name: str,
    ) -> MetadataInfo:
        """Разобрать ответ get_metadata_details в MetadataInfo."""
        info = MetadataInfo(
            fqn=fqn,
            object_type=object_type,
            object_name=object_name,
        )

        if not isinstance(raw, dict):
            return info

        info.synonym = raw.get("synonym", "")

        # Реквизиты
        for attr in raw.get("attributes", []):
            if isinstance(attr, dict):
                info.attributes.append(MetadataAttribute(
                    name=attr.get("name", ""),
                    type_name=attr.get("type", ""),
                    synonym=attr.get("synonym", ""),
                ))
            elif isinstance(attr, str):
                info.attributes.append(MetadataAttribute(name=attr))

        # Табличные части
        for tp in raw.get("tableParts", raw.get("table_parts", [])):
            if isinstance(tp, dict):
                tp_obj = MetadataTablePart(
                    name=tp.get("name", ""),
                    synonym=tp.get("synonym", ""),
                )
                for attr in tp.get("attributes", []):
                    if isinstance(attr, dict):
                        tp_obj.attributes.append(MetadataAttribute(
                            name=attr.get("name", ""),
                            type_name=attr.get("type", ""),
                            synonym=attr.get("synonym", ""),
                        ))
                    elif isinstance(attr, str):
                        tp_obj.attributes.append(MetadataAttribute(name=attr))
                info.table_parts.append(tp_obj)
            elif isinstance(tp, str):
                info.table_parts.append(MetadataTablePart(name=tp))

        # Стандартные реквизиты
        info.standard_attributes = raw.get("standardAttributes", raw.get("standard_attributes", []))

        return info


# Глобальный экземпляр
_client: EDTClient | None = None


def get_edt_client() -> EDTClient:
    """Получить глобальный EDT клиент (singleton)."""
    global _client
    if _client is None:
        _client = EDTClient()
    return _client
