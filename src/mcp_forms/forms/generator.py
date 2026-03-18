"""Генератор Form.xml для управляемых форм 1С.

Поддерживает форматы logform (конфигуратор) и managed (EDT).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from lxml import etree

from mcp_forms.forms.loader import LOGFORM_NAMESPACES, MANAGED_NAMESPACES, NS_LOGFORM, NS_MANAGED

# Версия формата
LOGFORM_VERSION = "2.16"


@dataclass
class FormFieldSpec:
    """Спецификация поля формы."""

    name: str
    data_path: str = ""  # Объект.Поле или ИмяРеквизита
    field_type: str = "InputField"  # InputField, CheckBoxField, LabelField...
    title: str = ""  # Заголовок (если отличается от name)
    read_only: bool = False
    visible: bool = True


@dataclass
class FormGroupSpec:
    """Спецификация группы элементов."""

    name: str
    title: str = ""
    group_type: str = "UsualGroup"  # UsualGroup, Pages, Page, ColumnGroup
    direction: str = "Vertical"  # Vertical, Horizontal
    children: list[FormFieldSpec | FormGroupSpec | FormTableSpec] = field(default_factory=list)


@dataclass
class FormTableColumnSpec:
    """Спецификация колонки таблицы."""

    name: str
    data_path: str = ""
    title: str = ""


@dataclass
class FormTableSpec:
    """Спецификация таблицы формы."""

    name: str
    data_path: str = ""  # ИмяТЧ
    columns: list[FormTableColumnSpec] = field(default_factory=list)


@dataclass
class FormAttributeSpec:
    """Спецификация реквизита формы."""

    name: str
    type_name: str  # cfg:CatalogObject.Номенклатура, xs:string, xs:decimal...
    is_main: bool = False
    save_data: bool = False
    title: str = ""


@dataclass
class FormSpec:
    """Полная спецификация формы для генерации."""

    object_type: str = ""  # Catalog, Document, DataProcessor...
    object_name: str = ""  # Номенклатура, ПоступлениеТоваров...
    form_type: str = "ФормаЭлемента"  # ФормаЭлемента, ФормаСписка, ФормаДокумента...
    title: str = ""
    attributes: list[FormAttributeSpec] = field(default_factory=list)
    elements: list[FormFieldSpec | FormGroupSpec | FormTableSpec] = field(default_factory=list)
    format: str = "logform"  # logform | managed


class FormGenerator:
    """Генератор Form.xml."""

    def __init__(self) -> None:
        self._next_element_id = 1
        self._next_attribute_id = 0

    def _alloc_id(self) -> int:
        """Выделяет следующий id для элемента формы."""
        val = self._next_element_id
        self._next_element_id += 1
        return val

    def _alloc_attr_id(self) -> int:
        val = self._next_attribute_id
        self._next_attribute_id += 1
        return val

    def generate(self, spec: FormSpec) -> str:
        """Генерирует Form.xml по спецификации."""
        self._next_element_id = 1
        self._next_attribute_id = 0

        # "edt" — алиас для "logform" (EDT использует logform-формат)
        fmt = "logform" if spec.format == "edt" else spec.format

        if fmt == "managed":
            return self._generate_managed(spec)
        return self._generate_logform(spec)

    # =================== Logform ===================

    def _generate_logform(self, spec: FormSpec) -> str:
        nsmap = {k or None: v for k, v in LOGFORM_NAMESPACES.items()}
        root = etree.Element("{%s}Form" % NS_LOGFORM, nsmap=nsmap)
        root.set("version", LOGFORM_VERSION)

        # AutoCommandBar
        acb = etree.SubElement(root, "AutoCommandBar")
        acb.set("name", "")
        acb.set("id", "-1")

        # ChildItems
        child_items = etree.SubElement(root, "ChildItems")
        for elem_spec in spec.elements:
            self._add_logform_element(child_items, elem_spec)

        # Attributes
        if spec.attributes:
            attrs_section = etree.SubElement(root, "Attributes")
            for attr_spec in spec.attributes:
                self._add_logform_attribute(attrs_section, attr_spec)

        return _serialize_xml(root)

    def _add_logform_element(
        self, parent: etree._Element, spec: FormFieldSpec | FormGroupSpec | FormTableSpec
    ) -> None:
        if isinstance(spec, FormGroupSpec):
            self._add_logform_group(parent, spec)
        elif isinstance(spec, FormTableSpec):
            self._add_logform_table(parent, spec)
        else:
            self._add_logform_field(parent, spec)

    def _add_logform_field(self, parent: etree._Element, spec: FormFieldSpec) -> None:
        elem_id = self._alloc_id()
        field_el = etree.SubElement(parent, spec.field_type)
        field_el.set("name", spec.name)
        field_el.set("id", str(elem_id))

        if spec.data_path:
            dp = etree.SubElement(field_el, "DataPath")
            dp.text = spec.data_path

        if spec.title:
            _add_v8_title(field_el, spec.title)

        if spec.read_only:
            ro = etree.SubElement(field_el, "ReadOnly")
            ro.text = "true"

        # ContextMenu и ExtendedTooltip — обязательные
        cm = etree.SubElement(field_el, "ContextMenu")
        cm.set("name", spec.name + "КонтекстноеМеню")
        cm.set("id", str(self._alloc_id()))

        et = etree.SubElement(field_el, "ExtendedTooltip")
        et.set("name", spec.name + "РасширеннаяПодсказка")
        et.set("id", str(self._alloc_id()))

    def _add_logform_group(self, parent: etree._Element, spec: FormGroupSpec) -> None:
        elem_id = self._alloc_id()
        group_el = etree.SubElement(parent, spec.group_type)
        group_el.set("name", spec.name)
        group_el.set("id", str(elem_id))

        if spec.title:
            _add_v8_title(group_el, spec.title)

        if spec.direction:
            grp = etree.SubElement(group_el, "Group")
            grp.text = spec.direction

        # ExtendedTooltip для группы
        et = etree.SubElement(group_el, "ExtendedTooltip")
        et.set("name", spec.name + "РасширеннаяПодсказка")
        et.set("id", str(self._alloc_id()))

        if spec.children:
            child_items = etree.SubElement(group_el, "ChildItems")
            for child_spec in spec.children:
                self._add_logform_element(child_items, child_spec)

    def _add_logform_table(self, parent: etree._Element, spec: FormTableSpec) -> None:
        elem_id = self._alloc_id()
        table_el = etree.SubElement(parent, "Table")
        table_el.set("name", spec.name)
        table_el.set("id", str(elem_id))

        if spec.data_path:
            dp = etree.SubElement(table_el, "DataPath")
            dp.text = spec.data_path

        # ContextMenu и ExtendedTooltip
        cm = etree.SubElement(table_el, "ContextMenu")
        cm.set("name", spec.name + "КонтекстноеМеню")
        cm.set("id", str(self._alloc_id()))

        et = etree.SubElement(table_el, "ExtendedTooltip")
        et.set("name", spec.name + "РасширеннаяПодсказка")
        et.set("id", str(self._alloc_id()))

        # Колонки
        if spec.columns:
            child_items = etree.SubElement(table_el, "ChildItems")
            for col in spec.columns:
                self._add_logform_field(
                    child_items,
                    FormFieldSpec(
                        name=col.name,
                        data_path=col.data_path or ("%s.%s" % (spec.data_path, col.name) if spec.data_path else ""),
                        title=col.title,
                    ),
                )

    def _add_logform_attribute(self, parent: etree._Element, spec: FormAttributeSpec) -> None:
        attr_el = etree.SubElement(parent, "Attribute")
        attr_el.set("name", spec.name)
        attr_el.set("id", str(self._alloc_attr_id()))

        if spec.title:
            _add_v8_title(attr_el, spec.title)

        # Type
        type_el = etree.SubElement(attr_el, "Type")
        v8_type = etree.SubElement(type_el, "{http://v8.1c.ru/8.1/data/core}Type")
        v8_type.text = spec.type_name

        if spec.is_main:
            main = etree.SubElement(attr_el, "MainAttribute")
            main.text = "true"

        if spec.save_data:
            save = etree.SubElement(attr_el, "SavedData")
            save.text = "true"

    # =================== Managed ===================

    def _generate_managed(self, spec: FormSpec) -> str:
        nsmap = {k or None: v for k, v in MANAGED_NAMESPACES.items()}
        root = etree.Element("{%s}ManagedForm" % NS_MANAGED, nsmap=nsmap)

        if spec.title:
            title_el = etree.SubElement(root, "Title")
            title_el.text = spec.title

        auto_title = etree.SubElement(root, "AutoTitle")
        auto_title.text = "true"

        # Attributes
        if spec.attributes:
            attrs_section = etree.SubElement(root, "Attributes")
            for attr_spec in spec.attributes:
                attr_el = etree.SubElement(attrs_section, "Attribute")
                name_el = etree.SubElement(attr_el, "Name")
                name_el.text = attr_spec.name
                id_el = etree.SubElement(attr_el, "Id")
                id_el.text = str(self._alloc_attr_id())
                vt = etree.SubElement(attr_el, "ValueType")
                t = etree.SubElement(vt, "Type")
                t.text = attr_spec.type_name

        # Elements
        if spec.elements:
            elements = etree.SubElement(root, "Elements")
            for elem_spec in spec.elements:
                self._add_managed_element(elements, elem_spec)

        return _serialize_xml(root)

    def _add_managed_element(
        self, parent: etree._Element, spec: FormFieldSpec | FormGroupSpec | FormTableSpec
    ) -> None:
        if isinstance(spec, FormGroupSpec):
            group_el = etree.SubElement(parent, spec.group_type)
            name_el = etree.SubElement(group_el, "Name")
            name_el.text = spec.name
            id_el = etree.SubElement(group_el, "Id")
            id_el.text = str(self._alloc_id())
            if spec.title:
                t = etree.SubElement(group_el, "Title")
                t.text = spec.title
            if spec.children:
                elems = etree.SubElement(group_el, "Elements")
                for child in spec.children:
                    self._add_managed_element(elems, child)
        elif isinstance(spec, FormTableSpec):
            table_el = etree.SubElement(parent, "Table")
            name_el = etree.SubElement(table_el, "Name")
            name_el.text = spec.name
            id_el = etree.SubElement(table_el, "Id")
            id_el.text = str(self._alloc_id())
            if spec.data_path:
                dp = etree.SubElement(table_el, "DataPath")
                dp.text = spec.data_path
        else:
            field_el = etree.SubElement(parent, spec.field_type)
            name_el = etree.SubElement(field_el, "Name")
            name_el.text = spec.name
            id_el = etree.SubElement(field_el, "Id")
            id_el.text = str(self._alloc_id())
            if spec.data_path:
                dp = etree.SubElement(field_el, "DataPath")
                dp.text = spec.data_path


# =================== Утилиты ===================


def _add_v8_title(parent: etree._Element, text: str) -> None:
    """Добавляет заголовок в формате v8:item/v8:lang/v8:content."""
    ns_v8 = "http://v8.1c.ru/8.1/data/core"
    title = etree.SubElement(parent, "Title")
    item = etree.SubElement(title, "{%s}item" % ns_v8)
    lang = etree.SubElement(item, "{%s}lang" % ns_v8)
    lang.text = "ru"
    content = etree.SubElement(item, "{%s}content" % ns_v8)
    content.text = text


def _serialize_xml(root: etree._Element) -> str:
    """Сериализует XML-дерево в строку с отступами."""
    etree.indent(root, space="\t")
    xml_bytes = etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )
    return xml_bytes.decode("utf-8")


def generate_form(spec: FormSpec) -> str:
    """Главная функция генерации. Обёртка над FormGenerator."""
    gen = FormGenerator()
    return gen.generate(spec)
