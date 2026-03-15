"""Тесты интеграции с EDT MCP."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mcp_forms.edt_client import (
    EDTClient,
    MetadataInfo,
    MetadataAttribute,
    MetadataTablePart,
    OBJECT_TYPE_MAP,
)
from mcp_forms.tools.edt import (
    get_edt_status,
    get_object_metadata,
    validate_form_with_edt,
    generate_form_spec_from_metadata,
    _metadata_to_dict,
    _build_form_spec,
)

FIXTURES = Path(__file__).parent / "fixtures"


# =================== EDTClient ===================


class TestEDTClient:
    """Тесты EDT клиента."""

    def test_disabled_by_default(self):
        """Клиент отключён по умолчанию."""
        client = EDTClient(enabled=False)
        assert not client.is_available()

    def test_disabled_returns_none(self):
        """Отключённый клиент возвращает None."""
        client = EDTClient(enabled=False)
        assert client.get_metadata_details("Catalog", "Test") is None
        assert client.get_project_errors() is None
        assert client.get_form_screenshot("Catalog.Test.Form.F") is None
        assert client.validate_query("ВЫБРАТЬ 1") is None
        assert client.get_metadata_objects() is None

    def test_object_type_map(self):
        """Маппинг типов объектов."""
        assert OBJECT_TYPE_MAP["Catalog"] == "Catalog"
        assert OBJECT_TYPE_MAP["Справочник"] == "Catalog"
        assert OBJECT_TYPE_MAP["Документ"] == "Document"
        assert OBJECT_TYPE_MAP["Обработка"] == "DataProcessor"

    def test_parse_metadata(self):
        """Парсинг ответа get_metadata_details."""
        client = EDTClient(enabled=False)
        raw = {
            "synonym": "Товары",
            "attributes": [
                {"name": "Артикул", "type": "String", "synonym": "Артикул"},
                {"name": "Цена", "type": "Number", "synonym": "Цена"},
            ],
            "tableParts": [
                {
                    "name": "Штрихкоды",
                    "synonym": "Штрихкоды",
                    "attributes": [
                        {"name": "Штрихкод", "type": "String"},
                    ],
                }
            ],
            "standardAttributes": ["Code", "Description"],
        }
        info = client._parse_metadata(raw, "Catalog.Товары", "Catalog", "Товары")

        assert info.fqn == "Catalog.Товары"
        assert info.synonym == "Товары"
        assert len(info.attributes) == 2
        assert info.attributes[0].name == "Артикул"
        assert len(info.table_parts) == 1
        assert info.table_parts[0].name == "Штрихкоды"
        assert len(info.table_parts[0].attributes) == 1
        assert info.standard_attributes == ["Code", "Description"]

    def test_parse_metadata_minimal(self):
        """Парсинг минимального ответа."""
        client = EDTClient(enabled=False)
        info = client._parse_metadata({}, "Catalog.X", "Catalog", "X")
        assert info.fqn == "Catalog.X"
        assert len(info.attributes) == 0

    def test_parse_metadata_string_attrs(self):
        """Парсинг атрибутов как строк."""
        client = EDTClient(enabled=False)
        info = client._parse_metadata(
            {"attributes": ["Поле1", "Поле2"]},
            "Catalog.X", "Catalog", "X",
        )
        assert len(info.attributes) == 2
        assert info.attributes[0].name == "Поле1"


# =================== MetadataInfo ===================


class TestMetadataInfo:
    """Тесты MetadataInfo."""

    def test_get_all_datapaths(self):
        """Генерация всех DataPath."""
        info = MetadataInfo(
            fqn="Catalog.Товары",
            object_type="Catalog",
            object_name="Товары",
            attributes=[
                MetadataAttribute(name="Артикул"),
                MetadataAttribute(name="Цена"),
            ],
            table_parts=[
                MetadataTablePart(
                    name="Штрихкоды",
                    attributes=[MetadataAttribute(name="Штрихкод")],
                ),
            ],
            standard_attributes=["Code", "Description"],
        )
        paths = info.get_all_datapaths()

        assert "Объект.Code" in paths
        assert "Объект.Description" in paths
        assert "Объект.Артикул" in paths
        assert "Объект.Цена" in paths
        assert "Объект.Штрихкоды" in paths
        assert "Объект.Штрихкоды.Штрихкод" in paths

    def test_get_datapaths_custom_main_attr(self):
        """DataPath с кастомным именем основного реквизита."""
        info = MetadataInfo(
            fqn="Catalog.X",
            object_type="Catalog",
            object_name="X",
            attributes=[MetadataAttribute(name="Поле")],
        )
        paths = info.get_all_datapaths(main_attr_name="Данные")
        assert "Данные.Поле" in paths

    def test_get_datapaths_empty(self):
        """DataPath для пустых метаданных."""
        info = MetadataInfo(fqn="Catalog.X", object_type="Catalog", object_name="X")
        assert info.get_all_datapaths() == []


# =================== Tools ===================


class TestEdtTools:
    """Тесты MCP-инструментов EDT."""

    def test_get_edt_status_disabled(self):
        """Статус EDT при отключённом клиенте."""
        with patch("mcp_forms.tools.edt.get_edt_client") as mock:
            client = MagicMock()
            client.enabled = False
            client.url = "http://localhost:9999/sse"
            mock.return_value = client

            result = get_edt_status()
            assert result["enabled"] is False
            assert "url" in result

    def test_get_object_metadata_disabled(self):
        """Получение метаданных при отключённом EDT."""
        with patch("mcp_forms.tools.edt.get_edt_client") as mock:
            client = MagicMock()
            client.enabled = False
            mock.return_value = client

            result = get_object_metadata("Catalog", "Товары")
            assert result["success"] is False
            assert "EDT_ENABLED" in result["error"]

    def test_validate_form_edt_disabled(self):
        """Валидация с EDT при отключённом клиенте — работает встроенная."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")

        with patch("mcp_forms.tools.edt.get_edt_client") as mock:
            client = MagicMock()
            client.enabled = False
            mock.return_value = client

            result = validate_form_with_edt(xml)
            assert result["success"] is True
            assert "builtin_result" in result
            assert result["edt_errors"] == []
            assert result["edt_available"] is False

    def test_generate_spec_disabled(self):
        """Генерация спецификации при отключённом EDT."""
        with patch("mcp_forms.tools.edt.get_edt_client") as mock:
            client = MagicMock()
            client.enabled = False
            mock.return_value = client

            result = generate_form_spec_from_metadata("Catalog", "Товары")
            assert result["success"] is False


# =================== Build Form Spec ===================


class TestBuildFormSpec:
    """Тесты генерации спецификации формы из метаданных."""

    def test_build_catalog_spec_logform(self):
        """Спецификация для справочника в logform."""
        info = MetadataInfo(
            fqn="Catalog.Товары",
            object_type="Catalog",
            object_name="Товары",
            synonym="Товары",
            attributes=[
                MetadataAttribute(name="Артикул", type_name="String"),
                MetadataAttribute(name="Цена", type_name="Number"),
            ],
            table_parts=[
                MetadataTablePart(
                    name="Штрихкоды",
                    attributes=[MetadataAttribute(name="Штрихкод", type_name="String")],
                ),
            ],
            standard_attributes=["Code", "Description"],
        )
        spec = _build_form_spec(info, "ФормаЭлемента", "logform", True)

        assert spec["format"] == "logform"
        assert spec["object_type"] == "Catalog"
        assert spec["object_name"] == "Товары"

        # Основной реквизит
        assert len(spec["attributes"]) == 1
        assert spec["attributes"][0]["name"] == "Объект"
        assert "cfg:" in spec["attributes"][0]["type_name"]

        # Элементы: стандартные + реквизиты + таблица
        element_names = [e["name"] for e in spec["elements"]]
        assert "Code" in element_names
        assert "Description" in element_names
        assert "Артикул" in element_names
        assert "Цена" in element_names
        assert "Штрихкоды" in element_names

    def test_build_spec_managed_no_cfg_prefix(self):
        """В managed формате нет cfg: префикса."""
        info = MetadataInfo(
            fqn="Document.Приход",
            object_type="Document",
            object_name="Приход",
            attributes=[MetadataAttribute(name="Склад")],
        )
        spec = _build_form_spec(info, "ФормаДокумента", "managed", False)

        assert "cfg:" not in spec["attributes"][0]["type_name"]
        assert "DocumentObject.Приход" in spec["attributes"][0]["type_name"]

    def test_build_spec_without_table_parts(self):
        """Спецификация без табличных частей."""
        info = MetadataInfo(
            fqn="Catalog.X",
            object_type="Catalog",
            object_name="X",
            table_parts=[MetadataTablePart(name="ТЧ")],
        )
        spec = _build_form_spec(info, "ФормаЭлемента", "logform", False)

        element_names = [e.get("name") for e in spec["elements"]]
        assert "ТЧ" not in element_names

    def test_build_spec_skips_service_attributes(self):
        """Стандартные служебные реквизиты пропускаются."""
        info = MetadataInfo(
            fqn="Catalog.X",
            object_type="Catalog",
            object_name="X",
            standard_attributes=["Ref", "DeletionMark", "Code", "Description", "Predefined"],
        )
        spec = _build_form_spec(info, "ФормаЭлемента", "logform", True)

        element_names = [e["name"] for e in spec["elements"]]
        assert "Ref" not in element_names
        assert "DeletionMark" not in element_names
        assert "Predefined" not in element_names
        assert "Code" in element_names
        assert "Description" in element_names


# =================== Metadata to Dict ===================


class TestMetadataToDict:
    """Тесты конвертации MetadataInfo → dict."""

    def test_full_metadata(self):
        """Полная конвертация с реквизитами и ТЧ."""
        info = MetadataInfo(
            fqn="Catalog.Товары",
            object_type="Catalog",
            object_name="Товары",
            synonym="Товары и услуги",
            attributes=[MetadataAttribute(name="Артикул", type_name="String", synonym="Артикул")],
            table_parts=[
                MetadataTablePart(
                    name="ТЧ",
                    synonym="Табличная часть",
                    attributes=[MetadataAttribute(name="Поле", type_name="Number")],
                )
            ],
            standard_attributes=["Code"],
        )
        d = _metadata_to_dict(info)

        assert d["success"] is True
        assert d["fqn"] == "Catalog.Товары"
        assert d["synonym"] == "Товары и услуги"
        assert len(d["attributes"]) == 1
        assert d["attributes"][0]["name"] == "Артикул"
        assert len(d["table_parts"]) == 1
        assert d["table_parts"][0]["name"] == "ТЧ"
        assert len(d["datapaths"]) >= 3  # Code, Артикул, ТЧ, ТЧ.Поле
