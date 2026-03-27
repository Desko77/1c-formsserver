"""Тесты формата EDT (form:Form) — загрузка, генерация, валидация, конвертация."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_forms.forms.loader import detect_format, load_form
from mcp_forms.forms.generator import (
    FormAttributeSpec,
    FormButtonSpec,
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
        # Баг 1: visible/enabled/userVisible
        assert "<form:visible>true</form:visible>" in xml
        assert "<form:enabled>true</form:enabled>" in xml
        assert "<form:userVisible>" in xml and "<form:common>true</form:common>" in xml
        # Баг 5: InputField extended properties
        assert "chooseType" in xml
        assert "typeDomainEnabled" in xml
        assert "textEdit" in xml

    def test_generate_field_invisible(self) -> None:
        spec = FormSpec(
            format="edt",
            elements=[
                FormFieldSpec(name="Скрытое", data_path="Объект.Скрытое", visible=False),
            ],
        )
        xml = generate_form(spec)
        assert "<form:visible>false</form:visible>" in xml

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

    def test_generate_group_horizontal(self) -> None:
        spec = FormSpec(
            format="edt",
            elements=[
                FormGroupSpec(name="Горизонтальная", group_type="UsualGroup", direction="Horizontal"),
            ],
        )
        xml = generate_form(spec)
        # direction should be inside UsualGroupExtInfo, not at items level
        assert "UsualGroupExtInfo" in xml
        # HorizontalIfPossible inside extInfo
        ext_info_pos = xml.index("UsualGroupExtInfo")
        group_pos = xml.index("HorizontalIfPossible")
        assert group_pos > ext_info_pos

    def test_generate_group_vertical_no_group_in_extinfo(self) -> None:
        spec = FormSpec(
            format="edt",
            elements=[
                FormGroupSpec(name="Вертикальная", group_type="UsualGroup", direction="Vertical"),
            ],
        )
        xml = generate_form(spec)
        # Vertical is default — no <group> inside extInfo
        ext_start = xml.index("UsualGroupExtInfo")
        ext_end = xml.index("</form:extInfo>", ext_start)
        ext_info_block = xml[ext_start:ext_end]
        assert "<form:group>" not in ext_info_block

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
        # Баг 4: autoCommandBar таблицы
        assert "ТоварыКоманднаяПанель" in xml
        # Баг 7: visible/enabled/userVisible, extendedTooltip, contextMenu
        assert "ТоварыРасширеннаяПодсказка" in xml
        assert "ТоварыКонтекстноеМеню" in xml

    def test_generate_table_column_properties(self) -> None:
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
        # Баг 6: колонки имеют editMode, showInHeader, showInFooter
        assert "<form:editMode>Enter</form:editMode>" in xml
        assert "<form:showInHeader>true</form:showInHeader>" in xml
        assert "<form:showInFooter>true</form:showInFooter>" in xml
        assert "<form:headerHorizontalAlign>Left</form:headerHorizontalAlign>" in xml

    def test_generate_table_companions(self) -> None:
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
        # Баг 9: searchStringAddition, viewStatusAddition
        assert "ТоварыСтрокаПоиска" in xml
        assert "SearchStringAdditionExtInfo" in xml
        assert "ТоварыСостояниеПросмотра" in xml
        assert "ViewStatusAdditionExtInfo" in xml

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

    def test_generate_button(self) -> None:
        spec = FormSpec(
            format="edt",
            elements=[
                FormButtonSpec(name="Выполнить", command_name="Выполнить", representation="Text"),
            ],
        )
        xml = generate_form(spec)
        assert "form:Button" in xml
        assert "<form:commandName>Выполнить</form:commandName>" in xml
        assert "<form:visible>true</form:visible>" in xml
        assert "<form:representation>Text</form:representation>" in xml
        assert "extendedTooltip" in xml

    def test_generate_attribute_xs_types(self) -> None:
        spec = FormSpec(
            format="edt",
            attributes=[
                FormAttributeSpec(name="Флаг", type_name="xs:boolean"),
                FormAttributeSpec(name="Сумма", type_name="xs:decimal"),
                FormAttributeSpec(name="Текст", type_name="xs:string"),
                FormAttributeSpec(name="Дата", type_name="xs:dateTime"),
            ],
        )
        xml = generate_form(spec)
        assert ">Boolean<" in xml
        assert ">Number<" in xml
        assert ">String<" in xml
        assert ">Date<" in xml
        assert "xs:" not in xml

    def test_generate_auto_command_bar(self) -> None:
        spec = FormSpec(format="edt")
        xml = generate_form(spec)
        assert "autoCommandBar" in xml
        assert ">-1<" in xml
        assert "autoTitle" in xml

    def test_generate_form_root_properties(self) -> None:
        spec = FormSpec(format="edt")
        xml = generate_form(spec)
        assert "<form:autoUrl>true</form:autoUrl>" in xml
        assert "<form:autoFillCheck>true</form:autoFillCheck>" in xml
        assert "<form:showTitle>true</form:showTitle>" in xml
        assert "<form:showCloseButton>true</form:showCloseButton>" in xml


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


# =================== Button type (UsualButton) ===================


class TestEdtButtonType:
    """Тесты генерации type для Button: UsualButton вне CommandBar."""

    def test_button_outside_commandbar_has_usual_type(self) -> None:
        """Кнопка на верхнем уровне -> type=UsualButton."""
        spec = FormSpec(
            format="edt",
            elements=[
                FormButtonSpec(name="Выполнить", command_name="Выполнить"),
            ],
        )
        xml = generate_form(spec)
        assert "<form:type>UsualButton</form:type>" in xml

    def test_button_in_commandbar_no_usual_type(self) -> None:
        """Кнопка в CommandBar -> без UsualButton (дефолт CommandBarButton)."""
        spec = FormSpec(
            format="edt",
            elements=[
                FormGroupSpec(
                    name="КоманднаяПанель",
                    group_type="CommandBar",
                    children=[
                        FormButtonSpec(name="Выполнить", command_name="Выполнить"),
                    ],
                ),
            ],
        )
        xml = generate_form(spec)
        assert "form:Button" in xml
        assert "UsualButton" not in xml

    def test_button_in_nested_group_inside_commandbar(self) -> None:
        """Кнопка в подгруппе внутри CommandBar -> тоже без UsualButton."""
        spec = FormSpec(
            format="edt",
            elements=[
                FormGroupSpec(
                    name="КоманднаяПанель",
                    group_type="CommandBar",
                    children=[
                        FormGroupSpec(
                            name="Подгруппа",
                            group_type="UsualGroup",
                            children=[
                                FormButtonSpec(name="Выполнить", command_name="Выполнить"),
                            ],
                        ),
                    ],
                ),
            ],
        )
        xml = generate_form(spec)
        assert "form:Button" in xml
        assert "UsualButton" not in xml

    def test_button_in_usual_group_outside_commandbar(self) -> None:
        """Кнопка в обычной группе (не CommandBar) -> type=UsualButton."""
        spec = FormSpec(
            format="edt",
            elements=[
                FormGroupSpec(
                    name="Группа",
                    group_type="UsualGroup",
                    children=[
                        FormButtonSpec(name="Выполнить", command_name="Выполнить"),
                    ],
                ),
            ],
        )
        xml = generate_form(spec)
        assert "<form:type>UsualButton</form:type>" in xml


# =================== EDT Defaults Validation Warnings ===================


class TestEdtDefaultsWarnings:
    """Тесты warnings для пропущенных EDT-дефолтов."""

    def test_inputfield_missing_extinfo_props(self) -> None:
        """InputField без chooseType/typeDomainEnabled/textEdit -> warning."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<form:Form xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:form="http://g5.1c.ru/v8/dt/form">
  <items xsi:type="form:FormField">
    <name>Поле</name>
    <id>1</id>
    <type>InputField</type>
    <extInfo xsi:type="form:InputFieldExtInfo">
      <autoMaxWidth>true</autoMaxWidth>
    </extInfo>
  </items>
</form:Form>"""
        doc = load_form(xml)
        result = validate_form(doc)
        warnings = [e for e in result.errors if e.severity == "warning"]
        assert any("chooseType" in w.message and "Поле" in w.message for w in warnings)

    def test_inputfield_with_all_props_no_warning(self) -> None:
        """InputField со всеми свойствами -> без warning."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<form:Form xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:form="http://g5.1c.ru/v8/dt/form">
  <items xsi:type="form:FormField">
    <name>Поле</name>
    <id>1</id>
    <type>InputField</type>
    <extInfo xsi:type="form:InputFieldExtInfo">
      <chooseType>true</chooseType>
      <typeDomainEnabled>true</typeDomainEnabled>
      <textEdit>true</textEdit>
    </extInfo>
  </items>
</form:Form>"""
        doc = load_form(xml)
        result = validate_form(doc)
        warnings = [e for e in result.errors if e.severity == "warning" and "extInfo без" in e.message]
        assert len(warnings) == 0

    def test_button_outside_commandbar_without_type(self) -> None:
        """Button без type вне CommandBar -> warning."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<form:Form xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:form="http://g5.1c.ru/v8/dt/form">
  <items xsi:type="form:Button">
    <name>Кнопка</name>
    <id>1</id>
  </items>
</form:Form>"""
        doc = load_form(xml)
        result = validate_form(doc)
        warnings = [e for e in result.errors if e.severity == "warning"]
        assert any("Button" in w.message and "CommandBar" in w.message for w in warnings)

    def test_button_in_commandbar_without_type_no_warning(self) -> None:
        """Button без type в CommandBar -> без warning."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<form:Form xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:form="http://g5.1c.ru/v8/dt/form">
  <items xsi:type="form:FormGroup">
    <name>Панель</name>
    <id>1</id>
    <type>CommandBar</type>
    <items xsi:type="form:Button">
      <name>Кнопка</name>
      <id>2</id>
    </items>
  </items>
</form:Form>"""
        doc = load_form(xml)
        result = validate_form(doc)
        warnings = [e for e in result.errors if e.severity == "warning" and "CommandBar" in e.message]
        assert len(warnings) == 0

    def test_contained_objects_warning(self) -> None:
        """containedObjects -> warning."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<form:Form xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:form="http://g5.1c.ru/v8/dt/form">
  <items xsi:type="form:FormField">
    <name>Поле</name>
    <id>1</id>
    <containedObjects classId="some-uuid"/>
  </items>
</form:Form>"""
        doc = load_form(xml)
        result = validate_form(doc)
        warnings = [e for e in result.errors if e.severity == "warning"]
        assert any("containedObjects" in w.message for w in warnings)

    def test_table_column_missing_props(self) -> None:
        """Колонка таблицы без editMode/showInHeader/showInFooter -> warning."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<form:Form xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:form="http://g5.1c.ru/v8/dt/form">
  <items xsi:type="form:Table">
    <name>Таблица</name>
    <id>1</id>
    <items xsi:type="form:FormField">
      <name>Колонка</name>
      <id>2</id>
      <type>InputField</type>
    </items>
  </items>
</form:Form>"""
        doc = load_form(xml)
        result = validate_form(doc)
        warnings = [e for e in result.errors if e.severity == "warning"]
        assert any("editMode" in w.message and "Колонка" in w.message for w in warnings)

    def test_handler_in_wrong_place(self) -> None:
        """StartChoice handler на уровне элемента вместо extInfo -> warning."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<form:Form xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:form="http://g5.1c.ru/v8/dt/form">
  <items xsi:type="form:FormField">
    <name>Поле</name>
    <id>1</id>
    <type>InputField</type>
    <handlers>
      <event>StartChoice</event>
      <name>ПолеНачалоВыбора</name>
    </handlers>
    <extInfo xsi:type="form:InputFieldExtInfo">
      <chooseType>true</chooseType>
      <typeDomainEnabled>true</typeDomainEnabled>
      <textEdit>true</textEdit>
    </extInfo>
  </items>
</form:Form>"""
        doc = load_form(xml)
        result = validate_form(doc)
        warnings = [e for e in result.errors if e.severity == "warning"]
        assert any("StartChoice" in w.message and "extInfo" in w.message for w in warnings)

    def test_fixture_edt_catalog_warnings(self) -> None:
        """Фикстура edt_catalog_element.form: Артикул без extInfo-свойств."""
        fixture = FIXTURES / "edt_catalog_element.form"
        xml = fixture.read_text(encoding="utf-8")
        doc = load_form(xml)
        result = validate_form(doc)
        # Артикул имеет InputField extInfo без chooseType/typeDomainEnabled/textEdit
        warnings = [e for e in result.errors if e.severity == "warning" and "extInfo без" in e.message]
        assert len(warnings) > 0
