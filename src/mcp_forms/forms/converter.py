"""Конвертер Form.xml между форматами EDT (managed) и Конфигуратор (logform)."""

from __future__ import annotations

from copy import deepcopy
from lxml import etree

from mcp_forms.forms.loader import (
    FormDocument,
    load_form,
    NS_LOGFORM,
    NS_MANAGED,
    LOGFORM_NAMESPACES,
    MANAGED_NAMESPACES,
)
from mcp_forms.forms.generator import LOGFORM_VERSION

# Теги, которые являются companion-элементами (logform-specific)
COMPANION_TAGS = {"ContextMenu", "ExtendedTooltip", "AutoCommandBar"}

# Теги, которые являются Addition-элементами таблицы (logform-specific)
ADDITION_TAGS = {"SearchStringAddition", "ViewStatusAddition", "SearchControlAddition"}

# Logform-specific свойства элементов, которые не переносятся в managed
LOGFORM_ONLY_PROPS = {
    "EditMode",
    "ExtendedEditMultipleValues",
    "RowFilter",
    "Representation",
    "AutoInsertNewRow",
    "EnableStartDrag",
    "EnableDrag",
}

# Контейнерные теги (элементы, содержащие дочерние)
CONTAINER_TAGS = {
    "ChildItems",  # logform
    "Elements",  # managed
}

# Элементы формы (field-like)
FIELD_TAGS = {
    "InputField",
    "CheckBoxField",
    "LabelField",
    "RadioButtonField",
    "NumberField",
    "DateField",
    "TextDocumentField",
    "SpreadSheetDocumentField",
    "PictureField",
    "PlannerField",
    "CalendarField",
    "ChartField",
    "DendrogramField",
    "FormattedDocumentField",
    "HTMLDocumentField",
    "GeographicalSchemaField",
    "GraphicalSchemaField",
    "TrackBarField",
    "ProgressBarField",
    "PeriodField",
}

# Группы
GROUP_TAGS = {"UsualGroup", "Pages", "Page", "ColumnGroup", "CommandBar", "Popup"}


def _local_tag(element: etree._Element) -> str:
    """Получить локальное имя тега без namespace."""
    tag = element.tag
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _strip_ns(tag: str) -> str:
    """Убрать namespace из тега."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


class FormConverter:
    """Конвертер Form.xml между форматами logform и managed."""

    def __init__(self) -> None:
        self._next_id = 1

    def _alloc_id(self) -> int:
        val = self._next_id
        self._next_id += 1
        return val

    def convert(self, xml_content: str, target_format: str) -> str:
        """Конвертировать Form.xml в целевой формат.

        Args:
            xml_content: содержимое Form.xml
            target_format: "logform" или "managed"

        Returns:
            сконвертированный XML

        Raises:
            ValueError: если формат не поддерживается или совпадает с исходным
        """
        # "edt" — алиас для "logform" (EDT использует logform-формат)
        if target_format == "edt":
            target_format = "logform"

        if target_format not in ("logform", "managed"):
            raise ValueError(f"Неизвестный целевой формат: {target_format}")

        doc = load_form(xml_content)

        if doc.format == target_format:
            raise ValueError(
                f"Форма уже в формате {target_format}, конвертация не требуется"
            )

        if doc.format == "logform" and target_format == "managed":
            return self._logform_to_managed(doc)
        elif doc.format == "managed" and target_format == "logform":
            return self._managed_to_logform(doc)
        else:
            raise ValueError(
                f"Конвертация {doc.format} → {target_format} не поддерживается"
            )

    # =================== Logform → Managed ===================

    def _logform_to_managed(self, doc: FormDocument) -> str:
        """Конвертировать logform → managed."""
        nsmap = {k or None: v for k, v in MANAGED_NAMESPACES.items()}
        managed_root = etree.Element("{%s}ManagedForm" % NS_MANAGED, nsmap=nsmap)

        root = doc.root
        ns = doc.namespace

        # Собираем все используемые element ID для перенумерации attribute ID
        self._used_element_ids = self._collect_element_ids(root, ns)

        # Title — ищем в Title (v8:item), WindowOpeningMode пропускаем
        title_el = root.find("{%s}Title" % ns)
        if title_el is not None:
            title_text = self._extract_v8_title(title_el)
            if title_text:
                new_title = etree.SubElement(managed_root, "Title")
                new_title.text = title_text

        auto_title = etree.SubElement(managed_root, "AutoTitle")
        auto_title.text = "true"

        # Attributes — перенумеровываем ID чтобы не конфликтовать с element ID
        lf_attrs = root.find("{%s}Attributes" % ns)
        if lf_attrs is not None:
            attrs_section = etree.SubElement(managed_root, "Attributes")
            for lf_attr in lf_attrs:
                if _local_tag(lf_attr) != "Attribute":
                    continue
                self._convert_attribute_to_managed(lf_attr, attrs_section, ns)

        # Elements — из ChildItems
        child_items = root.find("{%s}ChildItems" % ns)
        if child_items is not None and len(child_items):
            elements = etree.SubElement(managed_root, "Elements")
            self._convert_elements_to_managed(child_items, elements, ns)

        return _serialize_xml(managed_root)

    def _collect_element_ids(self, root: etree._Element, ns: str) -> set[str]:
        """Собрать все id из элементов формы (ChildItems)."""
        ids = set()
        for el in root.iter():
            el_id = el.get("id")
            if el_id is not None and el_id != "-1":
                ids.add(el_id)
        return ids

    def _convert_attribute_to_managed(
        self,
        lf_attr: etree._Element,
        parent: etree._Element,
        ns: str,
    ) -> None:
        """Конвертировать один Attribute из logform в managed формат."""
        attr_el = etree.SubElement(parent, "Attribute")

        # name → Name элемент
        name = lf_attr.get("name", "")
        name_el = etree.SubElement(attr_el, "Name")
        name_el.text = name

        # id → Id элемент (перенумеровать если конфликтует с element ID)
        attr_id = lf_attr.get("id", "0")
        if attr_id in self._used_element_ids:
            # Найти свободный ID
            max_id = max(int(x) for x in self._used_element_ids if x.lstrip("-").isdigit())
            attr_id = str(max_id + 1)
            self._used_element_ids.add(attr_id)
        else:
            self._used_element_ids.add(attr_id)
        id_el = etree.SubElement(attr_el, "Id")
        id_el.text = attr_id

        # Type/v8:Type → ValueType/Type
        type_el = lf_attr.find("{%s}Type" % ns)
        if type_el is None:
            type_el = lf_attr.find("Type")
        if type_el is not None:
            ns_v8 = "http://v8.1c.ru/8.1/data/core"
            v8_type = type_el.find("{%s}Type" % ns_v8)
            if v8_type is not None and v8_type.text:
                vt = etree.SubElement(attr_el, "ValueType")
                t = etree.SubElement(vt, "Type")
                t.text = self._convert_type_to_managed(v8_type.text)

        # MainAttribute, SavedData — сохраняем как есть
        for child_tag in ("MainAttribute", "SavedData"):
            child = lf_attr.find("{%s}%s" % (ns, child_tag))
            if child is None:
                child = lf_attr.find(child_tag)
            if child is not None:
                new_child = etree.SubElement(attr_el, child_tag)
                new_child.text = child.text

    def _convert_type_to_managed(self, type_text: str) -> str:
        """Конвертировать тип из logform в managed формат.

        cfg:CatalogObject.Номенклатура → CatalogObject.Номенклатура
        cfg:DocumentObject.РТУ → DocumentObject.РТУ
        xs:string → xs:string (без изменений)
        """
        if type_text.startswith("cfg:"):
            return type_text[4:]
        return type_text

    def _convert_type_to_logform(self, type_text: str) -> str:
        """Конвертировать тип из managed в logform формат.

        CatalogObject.Номенклатура → cfg:CatalogObject.Номенклатура
        xs:string → xs:string (без изменений)
        """
        # Типы, которые должны иметь префикс cfg:
        cfg_prefixes = (
            "CatalogObject.",
            "CatalogRef.",
            "DocumentObject.",
            "DocumentRef.",
            "DataProcessorObject.",
            "ExternalDataProcessorObject.",
            "ReportObject.",
            "ExternalReportObject.",
            "ChartOfAccountsObject.",
            "ChartOfCharacteristicTypesObject.",
            "ChartOfCalculationTypesObject.",
            "ExchangePlanObject.",
            "BusinessProcessObject.",
            "TaskObject.",
            "InformationRegisterRecord.",
            "AccumulationRegisterRecord.",
            "AccountingRegisterRecord.",
            "CalculationRegisterRecord.",
        )
        for prefix in cfg_prefixes:
            if type_text.startswith(prefix):
                return "cfg:" + type_text
        return type_text

    def _convert_elements_to_managed(
        self,
        source: etree._Element,
        target: etree._Element,
        ns: str,
    ) -> None:
        """Рекурсивно конвертировать элементы из logform в managed."""
        for child in source:
            local = _local_tag(child)

            # Пропускаем companion и addition элементы
            if local in COMPANION_TAGS or local in ADDITION_TAGS:
                continue

            if local in FIELD_TAGS:
                self._convert_field_to_managed(child, target, ns)
            elif local == "Table":
                self._convert_table_to_managed(child, target, ns)
            elif local in GROUP_TAGS:
                self._convert_group_to_managed(child, target, ns)
            elif local == "Button":
                self._convert_field_to_managed(child, target, ns)
            elif local == "Decoration":
                self._convert_field_to_managed(child, target, ns)

    def _convert_field_to_managed(
        self,
        lf_field: etree._Element,
        parent: etree._Element,
        ns: str,
    ) -> None:
        """Конвертировать поле из logform в managed."""
        local = _local_tag(lf_field)
        field_el = etree.SubElement(parent, local)

        # name → Name
        name = lf_field.get("name", "")
        name_el = etree.SubElement(field_el, "Name")
        name_el.text = name

        # id → Id
        field_id = lf_field.get("id", "0")
        id_el = etree.SubElement(field_el, "Id")
        id_el.text = field_id

        # Переносим свойства, кроме logform-specific
        for child in lf_field:
            local_child = _local_tag(child)
            if local_child in COMPANION_TAGS:
                continue
            if local_child in LOGFORM_ONLY_PROPS:
                continue
            if local_child == "Title":
                title_text = self._extract_v8_title(child)
                if title_text:
                    t = etree.SubElement(field_el, "Title")
                    t.text = title_text
                continue
            # Простые текстовые свойства (DataPath, ReadOnly, Visible и др.)
            new_child = etree.SubElement(field_el, local_child)
            new_child.text = child.text

    def _convert_table_to_managed(
        self,
        lf_table: etree._Element,
        parent: etree._Element,
        ns: str,
    ) -> None:
        """Конвертировать таблицу из logform в managed."""
        table_el = etree.SubElement(parent, "Table")

        name_el = etree.SubElement(table_el, "Name")
        name_el.text = lf_table.get("name", "")

        id_el = etree.SubElement(table_el, "Id")
        id_el.text = lf_table.get("id", "0")

        # DataPath
        dp = lf_table.find("{%s}DataPath" % ns)
        if dp is None:
            dp = lf_table.find("DataPath")
        if dp is not None:
            new_dp = etree.SubElement(table_el, "DataPath")
            new_dp.text = dp.text

        # ChildItems/columns → Elements (рекурсивно)
        child_items = lf_table.find("{%s}ChildItems" % ns)
        if child_items is None:
            child_items = lf_table.find("ChildItems")
        if child_items is not None and len(child_items):
            columns = etree.SubElement(table_el, "Elements")
            self._convert_elements_to_managed(child_items, columns, ns)

    def _convert_group_to_managed(
        self,
        lf_group: etree._Element,
        parent: etree._Element,
        ns: str,
    ) -> None:
        """Конвертировать группу из logform в managed."""
        local = _local_tag(lf_group)
        group_el = etree.SubElement(parent, local)

        name_el = etree.SubElement(group_el, "Name")
        name_el.text = lf_group.get("name", "")

        id_el = etree.SubElement(group_el, "Id")
        id_el.text = lf_group.get("id", "0")

        # Title
        title_child = lf_group.find("{%s}Title" % ns)
        if title_child is None:
            title_child = lf_group.find("Title")
        if title_child is not None:
            title_text = self._extract_v8_title(title_child)
            if title_text:
                t = etree.SubElement(group_el, "Title")
                t.text = title_text

        # Перенос свойств (Group/Direction и др.)
        for child in lf_group:
            local_child = _local_tag(child)
            if local_child in COMPANION_TAGS or local_child in ADDITION_TAGS:
                continue
            if local_child in ("Title", "ChildItems"):
                continue
            if local_child in LOGFORM_ONLY_PROPS:
                continue
            new_child = etree.SubElement(group_el, local_child)
            new_child.text = child.text

        # ChildItems → Elements
        child_items = lf_group.find("{%s}ChildItems" % ns)
        if child_items is None:
            child_items = lf_group.find("ChildItems")
        if child_items is not None and len(child_items):
            elements = etree.SubElement(group_el, "Elements")
            self._convert_elements_to_managed(child_items, elements, ns)

    def _extract_v8_title(self, title_el: etree._Element) -> str:
        """Извлечь текст заголовка из v8:item/v8:content формата."""
        ns_v8 = "http://v8.1c.ru/8.1/data/core"

        # Прямой текст
        if title_el.text and title_el.text.strip():
            return title_el.text.strip()

        # v8:item/v8:content
        item = title_el.find("{%s}item" % ns_v8)
        if item is not None:
            content = item.find("{%s}content" % ns_v8)
            if content is not None and content.text:
                return content.text

        return ""

    # =================== Managed → Logform ===================

    def _managed_to_logform(self, doc: FormDocument) -> str:
        """Конвертировать managed → logform."""
        self._next_id = 1
        nsmap = {k or None: v for k, v in LOGFORM_NAMESPACES.items()}
        lf_root = etree.Element("{%s}Form" % NS_LOGFORM, nsmap=nsmap)
        lf_root.set("version", LOGFORM_VERSION)

        root = doc.root
        ns = doc.namespace

        # AutoCommandBar
        acb = etree.SubElement(lf_root, "AutoCommandBar")
        acb.set("name", "")
        acb.set("id", "-1")

        # ChildItems
        elements = root.find("{%s}Elements" % ns)
        if elements is None:
            elements = root.find("Elements")
        if elements is not None and len(elements):
            child_items = etree.SubElement(lf_root, "ChildItems")
            self._collect_max_id(elements, ns)
            self._convert_elements_to_logform(elements, child_items, ns)

        # Attributes
        attrs = root.find("{%s}Attributes" % ns)
        if attrs is None:
            attrs = root.find("Attributes")
        if attrs is not None:
            attrs_section = etree.SubElement(lf_root, "Attributes")
            for attr in attrs:
                if _local_tag(attr) != "Attribute":
                    continue
                self._convert_attribute_to_logform(attr, attrs_section, ns)

        return _serialize_xml(lf_root)

    def _collect_max_id(self, elements: etree._Element, ns: str) -> None:
        """Собрать максимальный ID из элементов managed для аллокации новых."""
        max_id = 0
        for el in elements.iter():
            local = _local_tag(el)
            if local == "Id":
                try:
                    val = int(el.text or "0")
                    if val > max_id:
                        max_id = val
                except ValueError:
                    pass
        self._next_id = max_id + 1

    def _convert_elements_to_logform(
        self,
        source: etree._Element,
        target: etree._Element,
        ns: str,
    ) -> None:
        """Рекурсивно конвертировать элементы из managed в logform."""
        for child in source:
            local = _local_tag(child)

            if local in FIELD_TAGS or local == "Button" or local == "Decoration":
                self._convert_field_to_logform(child, target, ns)
            elif local == "Table":
                self._convert_table_to_logform(child, target, ns)
            elif local in GROUP_TAGS:
                self._convert_group_to_logform(child, target, ns)

    def _get_child_text(self, element: etree._Element, tag: str, ns: str) -> str:
        """Получить текст дочернего элемента по локальному имени."""
        child = element.find("{%s}%s" % (ns, tag))
        if child is None:
            child = element.find(tag)
        if child is not None and child.text:
            return child.text
        return ""

    def _convert_field_to_logform(
        self,
        managed_field: etree._Element,
        parent: etree._Element,
        ns: str,
    ) -> None:
        """Конвертировать поле из managed в logform."""
        local = _local_tag(managed_field)
        field_el = etree.SubElement(parent, local)

        name = self._get_child_text(managed_field, "Name", ns)
        field_id = self._get_child_text(managed_field, "Id", ns) or str(self._alloc_id())
        field_el.set("name", name)
        field_el.set("id", field_id)

        # Переносим свойства (DataPath, ReadOnly, Visible и др.)
        for child in managed_field:
            local_child = _local_tag(child)
            if local_child in ("Name", "Id"):
                continue
            if local_child == "Title":
                if child.text and child.text.strip():
                    _add_v8_title(field_el, child.text.strip())
                continue
            if local_child == "Elements":
                continue
            new_child = etree.SubElement(field_el, local_child)
            new_child.text = child.text

        # Добавить companion-элементы
        cm = etree.SubElement(field_el, "ContextMenu")
        cm.set("name", name + "КонтекстноеМеню")
        cm.set("id", str(self._alloc_id()))

        et = etree.SubElement(field_el, "ExtendedTooltip")
        et.set("name", name + "РасширеннаяПодсказка")
        et.set("id", str(self._alloc_id()))

    def _convert_table_to_logform(
        self,
        managed_table: etree._Element,
        parent: etree._Element,
        ns: str,
    ) -> None:
        """Конвертировать таблицу из managed в logform."""
        table_el = etree.SubElement(parent, "Table")

        name = self._get_child_text(managed_table, "Name", ns)
        table_id = self._get_child_text(managed_table, "Id", ns) or str(self._alloc_id())
        table_el.set("name", name)
        table_el.set("id", table_id)

        # DataPath
        dp_text = self._get_child_text(managed_table, "DataPath", ns)
        if dp_text:
            dp = etree.SubElement(table_el, "DataPath")
            dp.text = dp_text

        # Companion-элементы таблицы
        cm = etree.SubElement(table_el, "ContextMenu")
        cm.set("name", name + "КонтекстноеМеню")
        cm.set("id", str(self._alloc_id()))

        acb = etree.SubElement(table_el, "AutoCommandBar")
        acb.set("name", name + "КоманднаяПанель")
        acb.set("id", str(self._alloc_id()))

        et = etree.SubElement(table_el, "ExtendedTooltip")
        et.set("name", name + "РасширеннаяПодсказка")
        et.set("id", str(self._alloc_id()))

        # Columns (Elements → ChildItems)
        elements = managed_table.find("{%s}Elements" % ns)
        if elements is None:
            elements = managed_table.find("Elements")
        if elements is not None and len(elements):
            child_items = etree.SubElement(table_el, "ChildItems")
            self._convert_elements_to_logform(elements, child_items, ns)

    def _convert_group_to_logform(
        self,
        managed_group: etree._Element,
        parent: etree._Element,
        ns: str,
    ) -> None:
        """Конвертировать группу из managed в logform."""
        local = _local_tag(managed_group)
        group_el = etree.SubElement(parent, local)

        name = self._get_child_text(managed_group, "Name", ns)
        group_id = self._get_child_text(managed_group, "Id", ns) or str(self._alloc_id())
        group_el.set("name", name)
        group_el.set("id", group_id)

        # Перенос свойств
        for child in managed_group:
            local_child = _local_tag(child)
            if local_child in ("Name", "Id", "Elements"):
                continue
            if local_child == "Title":
                if child.text and child.text.strip():
                    _add_v8_title(group_el, child.text.strip())
                continue
            new_child = etree.SubElement(group_el, local_child)
            new_child.text = child.text

        # ExtendedTooltip для группы
        et = etree.SubElement(group_el, "ExtendedTooltip")
        et.set("name", name + "РасширеннаяПодсказка")
        et.set("id", str(self._alloc_id()))

        # Elements → ChildItems
        elements = managed_group.find("{%s}Elements" % ns)
        if elements is None:
            elements = managed_group.find("Elements")
        if elements is not None and len(elements):
            child_items = etree.SubElement(group_el, "ChildItems")
            self._convert_elements_to_logform(elements, child_items, ns)

    def _convert_attribute_to_logform(
        self,
        managed_attr: etree._Element,
        parent: etree._Element,
        ns: str,
    ) -> None:
        """Конвертировать один Attribute из managed в logform."""
        attr_el = etree.SubElement(parent, "Attribute")

        name = self._get_child_text(managed_attr, "Name", ns)
        attr_id = self._get_child_text(managed_attr, "Id", ns) or "0"
        attr_el.set("name", name)
        attr_el.set("id", attr_id)

        # ValueType/Type → Type/v8:Type
        vt = managed_attr.find("{%s}ValueType" % ns)
        if vt is None:
            vt = managed_attr.find("ValueType")
        if vt is not None:
            type_child = vt.find("{%s}Type" % ns)
            if type_child is None:
                type_child = vt.find("Type")
            if type_child is not None and type_child.text:
                type_el = etree.SubElement(attr_el, "Type")
                ns_v8 = "http://v8.1c.ru/8.1/data/core"
                v8_type = etree.SubElement(type_el, "{%s}Type" % ns_v8)
                v8_type.text = self._convert_type_to_logform(type_child.text)

        # MainAttribute, SavedData
        for child_tag in ("MainAttribute", "SavedData"):
            child = managed_attr.find("{%s}%s" % (ns, child_tag))
            if child is None:
                child = managed_attr.find(child_tag)
            if child is not None:
                new_child = etree.SubElement(attr_el, child_tag)
                new_child.text = child.text


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


# =================== Public API ===================


def convert_form(xml_content: str, target_format: str) -> str:
    """Конвертировать Form.xml в целевой формат.

    Args:
        xml_content: содержимое Form.xml
        target_format: "logform" или "managed"

    Returns:
        сконвертированный XML
    """
    converter = FormConverter()
    return converter.convert(xml_content, target_format)
