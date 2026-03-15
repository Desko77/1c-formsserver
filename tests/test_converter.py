"""Тесты конвертера Form.xml между форматами logform и managed."""

from pathlib import Path

import pytest
from lxml import etree

from mcp_forms.forms.converter import convert_form, FormConverter
from mcp_forms.forms.loader import detect_format, NS_LOGFORM, NS_MANAGED

FIXTURES = Path(__file__).parent / "fixtures"


# =================== Logform → Managed ===================


class TestLogformToManaged:
    """Тесты конвертации logform → managed."""

    def test_catalog_element(self):
        """Конвертация формы элемента справочника."""
        xml = (FIXTURES / "logform_catalog_element.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "managed")

        assert detect_format(result) == "managed"
        root = etree.fromstring(result.encode("utf-8"))
        assert root.tag == "{%s}ManagedForm" % NS_MANAGED

    def test_document_with_table(self):
        """Конвертация формы документа с табличной частью."""
        xml = (FIXTURES / "logform_document.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "managed")

        assert detect_format(result) == "managed"
        root = etree.fromstring(result.encode("utf-8"))

        # Проверяем что таблица Товары сконвертирована
        ns = {"f": NS_MANAGED}
        tables = root.findall(".//f:Table", ns)
        assert len(tables) == 1

        table_name = tables[0].find("f:Name", ns)
        assert table_name is not None
        assert table_name.text == "Товары"

    def test_no_companion_elements(self):
        """В managed не должно быть ContextMenu и ExtendedTooltip."""
        xml = (FIXTURES / "logform_catalog_element.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "managed")
        root = etree.fromstring(result.encode("utf-8"))

        # Ни в одном namespace не должно быть companion-элементов
        xml_str = result.lower()
        assert "contextmenu" not in xml_str
        assert "extendedtooltip" not in xml_str
        assert "autocommandbar" not in xml_str

    def test_no_addition_elements(self):
        """В managed не должно быть SearchStringAddition и т.д."""
        xml = (FIXTURES / "logform_document.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "managed")

        xml_lower = result.lower()
        assert "searchstringaddition" not in xml_lower
        assert "viewstatusaddition" not in xml_lower
        assert "searchcontroladdition" not in xml_lower

    def test_attributes_converted(self):
        """Атрибуты конвертируются: name/id attr → Name/Id elements."""
        xml = (FIXTURES / "logform_catalog_element.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "managed")
        root = etree.fromstring(result.encode("utf-8"))

        ns = {"f": NS_MANAGED}
        attrs = root.findall(".//f:Attributes/f:Attribute", ns)
        assert len(attrs) == 1

        name_el = attrs[0].find("f:Name", ns)
        assert name_el is not None
        assert name_el.text == "Объект"

        # ValueType вместо Type/v8:Type
        vt = attrs[0].find("f:ValueType/f:Type", ns)
        assert vt is not None
        assert vt.text == "CatalogObject.Номенклатура"  # без cfg: префикса

    def test_element_identity_format(self):
        """Элементы имеют Name/Id как дочерние элементы, не атрибуты."""
        xml = (FIXTURES / "logform_catalog_element.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "managed")
        root = etree.fromstring(result.encode("utf-8"))

        ns = {"f": NS_MANAGED}
        fields = root.findall(".//f:InputField", ns)
        assert len(fields) > 0

        for field in fields:
            # Не должно быть name/id атрибутов
            assert field.get("name") is None
            assert field.get("id") is None
            # Должны быть Name/Id элементы
            assert field.find("f:Name", ns) is not None
            assert field.find("f:Id", ns) is not None

    def test_managed_namespaces_only(self):
        """В результате должно быть только 4 namespace-а managed."""
        xml = (FIXTURES / "logform_catalog_element.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "managed")
        root = etree.fromstring(result.encode("utf-8"))

        nsmap = {k: v for k, v in root.nsmap.items() if k is not None}
        # Должны быть только xsi, xs, xr
        assert len(nsmap) <= 3
        assert "v8" not in nsmap
        assert "cfg" not in nsmap
        assert "lf" not in nsmap


# =================== Managed → Logform ===================


class TestManagedToLogform:
    """Тесты конвертации managed → logform."""

    def test_simple_form(self):
        """Конвертация простой managed формы."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "logform")

        assert detect_format(result) == "logform"
        root = etree.fromstring(result.encode("utf-8"))
        assert root.tag == "{%s}Form" % NS_LOGFORM
        assert root.get("version") == "2.16"

    def test_auto_command_bar(self):
        """В logform должен быть AutoCommandBar с id=-1."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "logform")
        root = etree.fromstring(result.encode("utf-8"))

        acb = root.find("AutoCommandBar")
        if acb is None:
            acb = root.find("{%s}AutoCommandBar" % NS_LOGFORM)
        assert acb is not None
        assert acb.get("id") == "-1"

    def test_companion_elements_added(self):
        """Каждое поле должно получить ContextMenu и ExtendedTooltip."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "logform")
        root = etree.fromstring(result.encode("utf-8"))

        ns = {"f": NS_LOGFORM}
        fields = root.findall(".//f:InputField", ns)
        assert len(fields) > 0

        for field in fields:
            cm = field.find("f:ContextMenu", ns)
            et = field.find("f:ExtendedTooltip", ns)
            assert cm is not None, f"Поле {field.get('name')} без ContextMenu"
            assert et is not None, f"Поле {field.get('name')} без ExtendedTooltip"
            assert cm.get("name"), "ContextMenu без name"
            assert cm.get("id"), "ContextMenu без id"
            assert et.get("name"), "ExtendedTooltip без name"
            assert et.get("id"), "ExtendedTooltip без id"

    def test_element_identity_as_attributes(self):
        """Элементы имеют name/id как XML-атрибуты, не дочерние элементы."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "logform")
        root = etree.fromstring(result.encode("utf-8"))

        ns = {"f": NS_LOGFORM}
        fields = root.findall(".//f:InputField", ns)
        assert len(fields) > 0

        for field in fields:
            assert field.get("name"), "InputField без атрибута name"
            assert field.get("id"), "InputField без атрибута id"

    def test_attribute_type_format(self):
        """Атрибуты: Type → v8:Type с cfg: префиксом."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "logform")
        root = etree.fromstring(result.encode("utf-8"))

        ns = {"f": NS_LOGFORM, "v8": "http://v8.1c.ru/8.1/data/core"}
        attrs = root.findall(".//f:Attribute", ns)
        assert len(attrs) == 1

        v8_type = attrs[0].find("f:Type/v8:Type", ns)
        assert v8_type is not None
        assert v8_type.text.startswith("cfg:")  # CatalogObject → cfg:CatalogObject

    def test_logform_namespaces(self):
        """В результате должны быть все logform namespace-ы."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "logform")
        root = etree.fromstring(result.encode("utf-8"))

        nsmap = root.nsmap
        # Проверяем ключевые namespace-ы
        assert nsmap.get(None) == NS_LOGFORM
        assert "v8" in nsmap
        assert "cfg" in nsmap
        assert "xr" in nsmap

    def test_child_items_wrapper(self):
        """Элементы обёрнуты в ChildItems."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "logform")
        root = etree.fromstring(result.encode("utf-8"))

        ns = {"f": NS_LOGFORM}
        child_items = root.find("f:ChildItems", ns)
        assert child_items is not None
        assert len(child_items) > 0


# =================== Roundtrip ===================


class TestRoundtrip:
    """Тесты roundtrip конвертации."""

    def test_logform_roundtrip_preserves_elements(self):
        """Logform → Managed → Logform сохраняет набор элементов."""
        xml = (FIXTURES / "logform_catalog_element.xml").read_text(encoding="utf-8")

        # Logform → Managed
        managed = convert_form(xml, "managed")
        assert detect_format(managed) == "managed"

        # Managed → Logform
        back = convert_form(managed, "logform")
        assert detect_format(back) == "logform"

        # Проверяем что элементы сохранились
        root = etree.fromstring(back.encode("utf-8"))
        ns = {"f": NS_LOGFORM}
        fields = root.findall(".//f:InputField", ns)
        # Оригинал имел 4 InputField
        assert len(fields) == 4

    def test_managed_roundtrip_preserves_elements(self):
        """Managed → Logform → Managed сохраняет набор элементов."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")

        # Managed → Logform
        logform = convert_form(xml, "logform")
        assert detect_format(logform) == "logform"

        # Logform → Managed
        back = convert_form(logform, "managed")
        assert detect_format(back) == "managed"

        # Проверяем элементы
        root = etree.fromstring(back.encode("utf-8"))
        ns = {"f": NS_MANAGED}
        fields = root.findall(".//f:InputField", ns)
        assert len(fields) == 1

        name = fields[0].find("f:Name", ns)
        assert name is not None
        assert name.text == "Наименование"

    def test_document_roundtrip(self):
        """Форма документа с таблицей выдерживает roundtrip."""
        xml = (FIXTURES / "logform_document.xml").read_text(encoding="utf-8")

        managed = convert_form(xml, "managed")
        back = convert_form(managed, "logform")

        root = etree.fromstring(back.encode("utf-8"))
        ns = {"f": NS_LOGFORM}

        # Таблица на месте
        tables = root.findall(".//f:Table", ns)
        assert len(tables) == 1
        assert tables[0].get("name") == "Товары"

        # Header fields
        child_items = root.find("f:ChildItems", ns)
        assert child_items is not None
        header_fields = [
            el for el in child_items
            if el.tag == "{%s}InputField" % NS_LOGFORM
        ]
        assert len(header_fields) == 3  # Номер, Дата, Организация


# =================== Ошибки ===================


class TestErrors:
    """Тесты обработки ошибок."""

    def test_same_format_raises(self):
        """Конвертация в тот же формат — ошибка."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        with pytest.raises(ValueError, match="уже в формате"):
            convert_form(xml, "managed")

    def test_unknown_format_raises(self):
        """Неизвестный целевой формат — ошибка."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        with pytest.raises(ValueError, match="Неизвестный"):
            convert_form(xml, "unknown_format")

    def test_invalid_xml_raises(self):
        """Невалидный XML — ошибка."""
        with pytest.raises(Exception):
            convert_form("<not-a-form/>", "managed")


# =================== Unique IDs ===================


class TestUniqueIds:
    """Тесты уникальности ID после конвертации."""

    def test_managed_to_logform_unique_ids(self):
        """После managed → logform все element ID уникальны."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "logform")
        root = etree.fromstring(result.encode("utf-8"))

        ids = set()
        for el in root.iter():
            el_id = el.get("id")
            if el_id is not None and el_id != "-1":
                assert el_id not in ids, f"Дубликат id={el_id} в элементе {el.tag}"
                ids.add(el_id)

    def test_logform_to_managed_unique_ids(self):
        """После logform → managed все Id элементы уникальны."""
        xml = (FIXTURES / "logform_catalog_element.xml").read_text(encoding="utf-8")
        result = convert_form(xml, "managed")
        root = etree.fromstring(result.encode("utf-8"))

        ns = {"f": NS_MANAGED}
        ids = set()
        for id_el in root.iter("{%s}Id" % NS_MANAGED):
            val = id_el.text
            if val:
                assert val not in ids, f"Дубликат Id={val}"
                ids.add(val)
