"""Генератор Form.xml для управляемых форм 1С.

Поддерживает форматы logform (конфигуратор), managed (упрощённый) и edt (EDT form:Form).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from lxml import etree

from mcp_forms.forms.loader import (
    EDT_NAMESPACES,
    LOGFORM_NAMESPACES,
    MANAGED_NAMESPACES,
    NS_CORE,
    NS_EDT,
    NS_LOGFORM,
    NS_MANAGED,
)

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
    format: str = "logform"  # logform | managed | edt


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

        fmt = spec.format
        if fmt == "managed":
            return self._generate_managed(spec)
        if fmt == "edt":
            return self._generate_edt(spec)
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


    # =================== EDT (form:Form) ===================

    def _generate_edt(self, spec: FormSpec) -> str:
        ns_xsi = "http://www.w3.org/2001/XMLSchema-instance"
        nsmap = {k: v for k, v in EDT_NAMESPACES.items()}
        root = etree.Element("{%s}Form" % NS_EDT, nsmap=nsmap)

        # Elements (items)
        for elem_spec in spec.elements:
            self._add_edt_element(root, elem_spec, ns_xsi)

        # AutoCommandBar
        acb = etree.SubElement(root, "{%s}autoCommandBar" % NS_EDT)
        acb_name = etree.SubElement(acb, "{%s}name" % NS_EDT)
        acb_name.text = "ФормаКоманднаяПанель"
        acb_id = etree.SubElement(acb, "{%s}id" % NS_EDT)
        acb_id.text = "-1"
        acb_fill = etree.SubElement(acb, "{%s}autoFill" % NS_EDT)
        acb_fill.text = "true"

        # autoTitle
        at = etree.SubElement(root, "{%s}autoTitle" % NS_EDT)
        at.text = "true"

        # Form properties
        grp = etree.SubElement(root, "{%s}group" % NS_EDT)
        grp.text = "Vertical"
        en = etree.SubElement(root, "{%s}enabled" % NS_EDT)
        en.text = "true"

        # Attributes
        for attr_spec in spec.attributes:
            self._add_edt_attribute(root, attr_spec, ns_xsi)

        return _serialize_xml(root)

    def _add_edt_element(
        self,
        parent: etree._Element,
        spec: FormFieldSpec | FormGroupSpec | FormTableSpec,
        ns_xsi: str,
    ) -> None:
        if isinstance(spec, FormGroupSpec):
            self._add_edt_group(parent, spec, ns_xsi)
        elif isinstance(spec, FormTableSpec):
            self._add_edt_table(parent, spec, ns_xsi)
        else:
            self._add_edt_field(parent, spec, ns_xsi)

    def _add_edt_field(
        self, parent: etree._Element, spec: FormFieldSpec, ns_xsi: str
    ) -> None:
        item = etree.SubElement(
            parent, "{%s}items" % NS_EDT,
            {"{%s}type" % ns_xsi: "form:FormField"},
        )
        el_id = self._alloc_id()

        name_el = etree.SubElement(item, "{%s}name" % NS_EDT)
        name_el.text = spec.name
        id_el = etree.SubElement(item, "{%s}id" % NS_EDT)
        id_el.text = str(el_id)

        if spec.data_path:
            dp = etree.SubElement(
                item, "{%s}dataPath" % NS_EDT,
                {"{%s}type" % ns_xsi: "form:DataPath"},
            )
            seg = etree.SubElement(dp, "{%s}segments" % NS_EDT)
            seg.text = spec.data_path

        # extendedTooltip
        tt = etree.SubElement(item, "{%s}extendedTooltip" % NS_EDT)
        tt_name = etree.SubElement(tt, "{%s}name" % NS_EDT)
        tt_name.text = spec.name + "РасширеннаяПодсказка"
        tt_id = etree.SubElement(tt, "{%s}id" % NS_EDT)
        tt_id.text = str(self._alloc_id())
        tt_type = etree.SubElement(tt, "{%s}type" % NS_EDT)
        tt_type.text = "Label"
        tt_amw = etree.SubElement(tt, "{%s}autoMaxWidth" % NS_EDT)
        tt_amw.text = "true"
        tt_amh = etree.SubElement(tt, "{%s}autoMaxHeight" % NS_EDT)
        tt_amh.text = "true"
        tt_ei = etree.SubElement(
            tt, "{%s}extInfo" % NS_EDT,
            {"{%s}type" % ns_xsi: "form:LabelDecorationExtInfo"},
        )
        tt_ha = etree.SubElement(tt_ei, "{%s}horizontalAlign" % NS_EDT)
        tt_ha.text = "Left"

        # contextMenu
        cm = etree.SubElement(item, "{%s}contextMenu" % NS_EDT)
        cm_name = etree.SubElement(cm, "{%s}name" % NS_EDT)
        cm_name.text = spec.name + "КонтекстноеМеню"
        cm_id = etree.SubElement(cm, "{%s}id" % NS_EDT)
        cm_id.text = str(self._alloc_id())
        cm_fill = etree.SubElement(cm, "{%s}autoFill" % NS_EDT)
        cm_fill.text = "true"

        # type
        type_el = etree.SubElement(item, "{%s}type" % NS_EDT)
        type_el.text = spec.field_type

        # extInfo
        ext_type = _edt_field_ext_info_type(spec.field_type)
        ei = etree.SubElement(
            item, "{%s}extInfo" % NS_EDT,
            {"{%s}type" % ns_xsi: ext_type},
        )
        amw = etree.SubElement(ei, "{%s}autoMaxWidth" % NS_EDT)
        amw.text = "true"
        amh = etree.SubElement(ei, "{%s}autoMaxHeight" % NS_EDT)
        amh.text = "true"

    def _add_edt_group(
        self, parent: etree._Element, spec: FormGroupSpec, ns_xsi: str
    ) -> None:
        item = etree.SubElement(
            parent, "{%s}items" % NS_EDT,
            {"{%s}type" % ns_xsi: "form:FormGroup"},
        )
        name_el = etree.SubElement(item, "{%s}name" % NS_EDT)
        name_el.text = spec.name
        id_el = etree.SubElement(item, "{%s}id" % NS_EDT)
        id_el.text = str(self._alloc_id())

        # Children
        for child in spec.children:
            self._add_edt_element(item, child, ns_xsi)

        if spec.title:
            _add_edt_title(item, spec.title)

        # extendedTooltip
        tt = etree.SubElement(item, "{%s}extendedTooltip" % NS_EDT)
        tt_name = etree.SubElement(tt, "{%s}name" % NS_EDT)
        tt_name.text = spec.name + "РасширеннаяПодсказка"
        tt_id = etree.SubElement(tt, "{%s}id" % NS_EDT)
        tt_id.text = str(self._alloc_id())
        tt_type = etree.SubElement(tt, "{%s}type" % NS_EDT)
        tt_type.text = "Label"
        tt_ei = etree.SubElement(
            tt, "{%s}extInfo" % NS_EDT,
            {"{%s}type" % ns_xsi: "form:LabelDecorationExtInfo"},
        )
        tt_ha = etree.SubElement(tt_ei, "{%s}horizontalAlign" % NS_EDT)
        tt_ha.text = "Left"

        # type
        type_el = etree.SubElement(item, "{%s}type" % NS_EDT)
        type_el.text = spec.group_type

        # extInfo
        ext_type = _edt_group_ext_info_type(spec.group_type)
        ei = etree.SubElement(
            item, "{%s}extInfo" % NS_EDT,
            {"{%s}type" % ns_xsi: ext_type},
        )
        if spec.group_type == "UsualGroup":
            rep = etree.SubElement(ei, "{%s}representation" % NS_EDT)
            rep.text = "None"
            show = etree.SubElement(ei, "{%s}showLeftMargin" % NS_EDT)
            show.text = "true"
            united = etree.SubElement(ei, "{%s}united" % NS_EDT)
            united.text = "true"
            ta = etree.SubElement(ei, "{%s}throughAlign" % NS_EDT)
            ta.text = "Auto"
            cru = etree.SubElement(ei, "{%s}currentRowUse" % NS_EDT)
            cru.text = "Auto"

    def _add_edt_table(
        self, parent: etree._Element, spec: FormTableSpec, ns_xsi: str
    ) -> None:
        item = etree.SubElement(
            parent, "{%s}items" % NS_EDT,
            {"{%s}type" % ns_xsi: "form:Table"},
        )
        name_el = etree.SubElement(item, "{%s}name" % NS_EDT)
        name_el.text = spec.name
        id_el = etree.SubElement(item, "{%s}id" % NS_EDT)
        id_el.text = str(self._alloc_id())

        if spec.data_path:
            dp = etree.SubElement(
                item, "{%s}dataPath" % NS_EDT,
                {"{%s}type" % ns_xsi: "form:DataPath"},
            )
            seg = etree.SubElement(dp, "{%s}segments" % NS_EDT)
            seg.text = spec.data_path

        # Column items
        for col in spec.columns:
            col_spec = FormFieldSpec(
                name=col.name, data_path=col.data_path, title=col.title,
            )
            self._add_edt_field(item, col_spec, ns_xsi)

    def _add_edt_attribute(
        self, parent: etree._Element, spec: FormAttributeSpec, ns_xsi: str
    ) -> None:
        attr = etree.SubElement(parent, "{%s}attributes" % NS_EDT)
        name_el = etree.SubElement(attr, "{%s}name" % NS_EDT)
        name_el.text = spec.name
        if spec.title:
            _add_edt_title(attr, spec.title)
        id_el = etree.SubElement(attr, "{%s}id" % NS_EDT)
        id_el.text = str(self._alloc_attr_id())
        vt = etree.SubElement(attr, "{%s}valueType" % NS_EDT)
        types_el = etree.SubElement(vt, "{%s}types" % NS_EDT)
        # Strip cfg: prefix if present
        type_name = spec.type_name
        if type_name.startswith("cfg:"):
            type_name = type_name[4:]
        types_el.text = type_name

        view = etree.SubElement(attr, "{%s}view" % NS_EDT)
        vc = etree.SubElement(view, "{%s}common" % NS_EDT)
        vc.text = "true"
        edit = etree.SubElement(attr, "{%s}edit" % NS_EDT)
        ec = etree.SubElement(edit, "{%s}common" % NS_EDT)
        ec.text = "true"

        if spec.is_main:
            main = etree.SubElement(attr, "{%s}main" % NS_EDT)
            main.text = "true"
        if spec.save_data:
            sd = etree.SubElement(attr, "{%s}savedData" % NS_EDT)
            sd.text = "true"


def _edt_field_ext_info_type(field_type: str) -> str:
    """Возвращает xsi:type для extInfo поля."""
    mapping = {
        "InputField": "form:InputFieldExtInfo",
        "LabelField": "form:LabelFieldExtInfo",
        "CheckBoxField": "form:CheckBoxFieldExtInfo",
        "RadioButtonField": "form:RadioButtonsFieldExtInfo",
        "ImageField": "form:ImageFieldExtInfo",
        "SpreadSheetDocumentField": "form:SpreadSheetDocFieldExtInfo",
        "CalendarField": "form:CalendarFieldExtInfo",
        "TrackBarField": "form:TrackBarFieldExtInfo",
        "ProgressBarField": "form:ProgressBarFieldExtInfo",
    }
    return mapping.get(field_type, "form:InputFieldExtInfo")


def _edt_group_ext_info_type(group_type: str) -> str:
    """Возвращает xsi:type для extInfo группы."""
    mapping = {
        "UsualGroup": "form:UsualGroupExtInfo",
        "Pages": "form:PagesGroupExtInfo",
        "Page": "form:PageGroupExtInfo",
        "ColumnGroup": "form:ColumnGroupExtInfo",
        "CommandBar": "form:CommandBarExtInfo",
        "Popup": "form:PopupGroupExtInfo",
    }
    return mapping.get(group_type, "form:UsualGroupExtInfo")


def _add_edt_title(parent: etree._Element, text: str) -> None:
    """Добавляет заголовок в EDT-формате: <title><key>ru</key><value>текст</value></title>."""
    title = etree.SubElement(parent, "{%s}title" % NS_EDT)
    key = etree.SubElement(title, "{%s}key" % NS_EDT)
    key.text = "ru"
    val = etree.SubElement(title, "{%s}value" % NS_EDT)
    val.text = text


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
