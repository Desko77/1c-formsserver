"""Тесты формата EDT (form:Form) — загрузка, генерация, валидация, конвертация."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_forms.forms.loader import detect_format, load_form
from mcp_forms.forms.generator import (
    FormAttributeSpec,
    FormFieldSpec,
    FormGroupSpec,
    FormSpec,
    FormTableColumnSpec,
    FormTableSpec,
    generate_form,
)
from mcp_forms.forms.converter import convert_form
from mcp_forms.forms.templates import catalog_element_form, document_form, data_processor_form
from mcp_forms.schema.validator import validate_form

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def edt_xml() -> str:
    return (FIXTURES / "edt_catalog_element.form").read_text(encoding="utf-8")


@pytest.fixture
def logform_xml() -> str:
    return (FIXTURES / "logform_catalog_element.xml").read_text(encoding="utf-8")


# =================== Detection ===================


class TestEdtDetection:
    def test_detect_edt_format(self, edt_xml: str) -> None:
        assert detect_format(edt_xml) == "edt"

    def test_detect_logform_not_confused(self, logform_xml: str) -> None:
        assert detect_format(logform_xml) == "logform"

    def test_load_form_edt(self, edt_xml: str) -> None:
        doc = load_form(edt_xml)
        assert doc.format == "edt"
        assert "g5.1c.ru/v8/dt/form" in doc.namespace


# =================== Generation ===================


class TestEdtGeneration:
    def test_generate_field(self) -> None:
        spec = FormSpec(
            format="edt",
            attributes=[
                FormAttributeSpec(name="Объект", type_name="CatalogObject.Тест", is_main=True, save_data=True),
            ],
            elements=[
                FormFieldSpec(name="Наименование", data_path="Объект.Наименование"),
            ],
        )
        xml = generate_form(spec)
        assert detect_format(xml) == "edt"
        assert "form:FormField" in xml
        assert "segments>" in xml and "Объект.Наименование" in xml
        assert "extendedTooltip" in xml or "ExtendedTooltip" in xml
        assert "contextMenu" in xml or "ContextMenu" in xml
        assert "InputFieldExtInfo" in xml

    def test_generate_group(self) -> None:
        spec = FormSpec(
            format="edt",
            elements=[
                FormGroupSpec(
                    name="Группа",
                    title="Тест",
                    group_type="UsualGroup",
                    children=[
                        FormFieldSpec(name="Поле", data_path="Объект.Поле"),
                    ],
                ),
            ],
        )
        xml = generate_form(spec)
        assert "form:FormGroup" in xml
        assert "UsualGroupExtInfo" in xml
        assert "key>" in xml and "ru" in xml

    def test_generate_table(self) -> None:
        spec = FormSpec(
            format="edt",
            elements=[
                FormTableSpec(
                    name="Товары",
                    data_path="Объект.Товары",
                    columns=[
                        FormTableColumnSpec(name="Номенклатура", data_path="Объект.Товары.Номенклатура"),
                    ],
                ),
            ],
        )
        xml = generate_form(spec)
        assert "form:Table" in xml
        assert "form:FormField" in xml
        assert "Номенклатура" in xml

    def test_generate_attribute_strips_cfg(self) -> None:
        spec = FormSpec(
            format="edt",
            attributes=[
                FormAttributeSpec(name="Объект", type_name="cfg:CatalogObject.Тест", is_main=True, save_data=True),
            ],
        )
        xml = generate_form(spec)
        assert "CatalogObject.Тест" in xml
        assert "cfg:" not in xml
        assert "main>" in xml and "true" in xml
        assert "savedData>" in xml

    def test_generate_auto_command_bar(self) -> None:
        spec = FormSpec(format="edt")
        xml = generate_form(spec)
        assert "autoCommandBar" in xml
        assert ">-1<" in xml
        assert "autoTitle" in xml


# =================== Validation ===================


class TestEdtValidation:
    def test_valid_edt(self, edt_xml: str) -> None:
        doc = load_form(edt_xml)
        result = validate_form(doc)
        assert result.is_valid
        assert result.format == "edt"

    def test_duplicate_ids(self) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<form:Form xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:core="http://g5.1c.ru/v8/dt/mcore"
           xmlns:form="http://g5.1c.ru/v8/dt/form">
  <items xsi:type="form:FormField">
    <name>Поле1</name>
    <id>1</id>
    <type>InputField</type>
  </items>
  <items xsi:type="form:FormField">
    <name>Поле2</name>
    <id>1</id>
    <type>InputField</type>
  </items>
</form:Form>"""
        doc = load_form(xml)
        result = validate_form(doc)
        assert result.error_count > 0
        assert any("Дублирующийся id=1" in e.message for e in result.errors)

    def test_missing_xsi_type(self) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<form:Form xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:form="http://g5.1c.ru/v8/dt/form">
  <items>
    <name>Поле</name>
    <id>1</id>
  </items>
</form:Form>"""
        doc = load_form(xml)
        result = validate_form(doc)
        assert result.warning_count > 0


# =================== Conversion ===================


class TestEdtConversion:
    def test_logform_to_edt(self, logform_xml: str) -> None:
        edt_xml = convert_form(logform_xml, "edt")
        assert detect_format(edt_xml) == "edt"
        assert "form:FormField" in edt_xml
        assert "segments>" in edt_xml

    def test_edt_to_logform(self, edt_xml: str) -> None:
        lf_xml = convert_form(edt_xml, "logform")
        assert detect_format(lf_xml) == "logform"
        assert "InputField" in lf_xml or "LabelField" in lf_xml
        assert "ChildItems" in lf_xml

    def test_roundtrip_logform_edt_logform(self, logform_xml: str) -> None:
        edt_xml = convert_form(logform_xml, "edt")
        lf_xml = convert_form(edt_xml, "logform")
        assert detect_format(lf_xml) == "logform"
        doc = load_form(lf_xml)
        result = validate_form(doc)
        assert result.error_count == 0

    def test_roundtrip_edt_logform_edt(self, edt_xml: str) -> None:
        lf_xml = convert_form(edt_xml, "logform")
        edt_xml2 = convert_form(lf_xml, "edt")
        assert detect_format(edt_xml2) == "edt"
        doc = load_form(edt_xml2)
        result = validate_form(doc)
        assert result.error_count == 0

    def test_managed_to_edt_chain(self) -> None:
        managed_xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        edt_xml = convert_form(managed_xml, "edt")
        assert detect_format(edt_xml) == "edt"

    def test_edt_to_managed_chain(self, edt_xml: str) -> None:
        managed_xml = convert_form(edt_xml, "managed")
        assert detect_format(managed_xml) == "managed"

    def test_edt_preserves_attribute_names(self, logform_xml: str) -> None:
        edt_xml = convert_form(logform_xml, "edt")
        assert "Объект" in edt_xml


# =================== Templates ===================


class TestEdtTemplates:
    def test_catalog_template(self) -> None:
        spec = catalog_element_form("Номенклатура", ["Наименование", "Артикул"], format="edt")
        xml = generate_form(spec)
        assert detect_format(xml) == "edt"
        assert "CatalogObject.Номенклатура" in xml
        assert "cfg:" not in xml

    def test_document_template(self) -> None:
        spec = document_form(
            "ПоступлениеТоваров",
            header_fields=["Дата"],
            table_name="Товары",
            table_columns=["Номенклатура"],
            format="edt",
        )
        xml = generate_form(spec)
        assert detect_format(xml) == "edt"
        assert "form:Table" in xml
        assert "DocumentObject.ПоступлениеТоваров" in xml

    def test_data_processor_template(self) -> None:
        spec = data_processor_form("МояОбработка", ["Параметр"], format="edt")
        xml = generate_form(spec)
        assert detect_format(xml) == "edt"
        assert "DataProcessorObject.МояОбработка" in xml
