"""Конвертер Form.xml между форматами EDT (managed) и Конфигуратор (logform)."""

from __future__ import annotations

from copy import deepcopy
from lxml import etree

from mcp_forms.forms.loader import (
    EDT_NAMESPACES,
    FormDocument,
    load_form,
    NS_CORE,
    NS_EDT,
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
        if target_format not in ("logform", "managed", "edt"):
            raise ValueError(f"Неизвестный целевой формат: {target_format}")

        doc = load_form(xml_content)

        if doc.format == target_format:
            raise ValueError(
                f"Форма уже в формате {target_format}, конвертация не требуется"
            )

        # Direct routes
        if doc.format == "logform" and target_format == "managed":
            return self._logform_to_managed(doc)
        if doc.format == "managed" and target_format == "logform":
            return self._managed_to_logform(doc)
        if doc.format == "logform" and target_format == "edt":
            return self._logform_to_edt(doc)
        if doc.format == "edt" and target_format == "logform":
            return self._edt_to_logform(doc)

        # Chain routes via logform
        if doc.format == "managed" and target_format == "edt":
            logform_xml = self._managed_to_logform(doc)
            return self.convert(logform_xml, "edt")
        if doc.format == "edt" and target_format == "managed":
            logform_xml = self._edt_to_logform(doc)
            return self.convert(logform_xml, "managed")

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


    # =================== Logform → EDT ===================

    def _logform_to_edt(self, doc: FormDocument) -> str:
        """Конвертировать logform → EDT (form:Form)."""
        ns = doc.namespace
        ns_xsi = "http://www.w3.org/2001/XMLSchema-instance"
        xsi_type = "{%s}type" % ns_xsi

        nsmap = {k: v for k, v in EDT_NAMESPACES.items()}
        root = etree.Element("{%s}Form" % NS_EDT, nsmap=nsmap)

        # Convert ChildItems → items (direct children of root)
        child_items = doc.root.find("{%s}ChildItems" % ns)
        if child_items is None:
            child_items = doc.root.find("ChildItems")
        if child_items is not None:
            self._convert_elements_logform_to_edt(child_items, root, ns, xsi_type)

        # AutoCommandBar
        acb = doc.root.find("{%s}AutoCommandBar" % ns)
        if acb is None:
            acb = doc.root.find("AutoCommandBar")
        edt_acb = etree.SubElement(root, "{%s}autoCommandBar" % NS_EDT)
        if acb is not None:
            acb_name = acb.get("name", "ФормаКоманднаяПанель")
            acb_id = acb.get("id", "-1")
        else:
            acb_name = "ФормаКоманднаяПанель"
            acb_id = "-1"
        n = etree.SubElement(edt_acb, "{%s}name" % NS_EDT)
        n.text = acb_name
        i = etree.SubElement(edt_acb, "{%s}id" % NS_EDT)
        i.text = acb_id
        af = etree.SubElement(edt_acb, "{%s}autoFill" % NS_EDT)
        af.text = "true"

        # AutoTitle
        auto_title = doc.root.find("{%s}AutoTitle" % ns)
        if auto_title is None:
            auto_title = doc.root.find("AutoTitle")
        at = etree.SubElement(root, "{%s}autoTitle" % NS_EDT)
        at.text = auto_title.text if auto_title is not None else "true"

        # Form properties
        grp = etree.SubElement(root, "{%s}group" % NS_EDT)
        grp.text = "Vertical"
        en = etree.SubElement(root, "{%s}enabled" % NS_EDT)
        en.text = "true"

        # Attributes
        attrs_section = doc.root.find("{%s}Attributes" % ns)
        if attrs_section is None:
            attrs_section = doc.root.find("Attributes")
        if attrs_section is not None:
            for lf_attr in attrs_section:
                self._convert_attribute_logform_to_edt(lf_attr, root, ns)

        return _serialize_xml(root)

    def _convert_elements_logform_to_edt(
        self,
        source: etree._Element,
        target: etree._Element,
        ns: str,
        xsi_type_attr: str,
    ) -> None:
        """Рекурсивно конвертировать элементы logform → EDT."""
        for child in source:
            local = _local_tag(child)
            if local in COMPANION_TAGS or local in ADDITION_TAGS:
                continue
            if local in FIELD_TAGS:
                self._convert_field_logform_to_edt(child, target, ns, xsi_type_attr)
            elif local == "Table":
                self._convert_table_logform_to_edt(child, target, ns, xsi_type_attr)
            elif local in GROUP_TAGS:
                self._convert_group_logform_to_edt(child, target, ns, xsi_type_attr)

    def _convert_field_logform_to_edt(
        self,
        lf_field: etree._Element,
        target: etree._Element,
        ns: str,
        xsi_type_attr: str,
    ) -> None:
        """Конвертировать поле logform → EDT items."""
        field_type = _local_tag(lf_field)
        name = lf_field.get("name", "")
        el_id = lf_field.get("id", str(self._alloc_id()))

        item = etree.SubElement(
            target, "{%s}items" % NS_EDT,
            {xsi_type_attr: "form:FormField"},
        )
        n = etree.SubElement(item, "{%s}name" % NS_EDT)
        n.text = name
        i = etree.SubElement(item, "{%s}id" % NS_EDT)
        i.text = el_id

        # DataPath
        dp = lf_field.find("{%s}DataPath" % ns)
        if dp is None:
            dp = lf_field.find("DataPath")
        if dp is not None and dp.text:
            edt_dp = etree.SubElement(
                item, "{%s}dataPath" % NS_EDT,
                {xsi_type_attr: "form:DataPath"},
            )
            seg = etree.SubElement(edt_dp, "{%s}segments" % NS_EDT)
            seg.text = dp.text

        # extendedTooltip (companion)
        _add_edt_companion_tooltip(item, name, self._alloc_id(), xsi_type_attr)

        # contextMenu (companion)
        _add_edt_companion_menu(item, name, self._alloc_id())

        # type
        t = etree.SubElement(item, "{%s}type" % NS_EDT)
        t.text = field_type

        # extInfo
        from mcp_forms.forms.generator import _edt_field_ext_info_type
        ext_type = _edt_field_ext_info_type(field_type)
        ei = etree.SubElement(
            item, "{%s}extInfo" % NS_EDT,
            {xsi_type_attr: ext_type},
        )
        amw = etree.SubElement(ei, "{%s}autoMaxWidth" % NS_EDT)
        amw.text = "true"
        amh = etree.SubElement(ei, "{%s}autoMaxHeight" % NS_EDT)
        amh.text = "true"

    def _convert_table_logform_to_edt(
        self,
        lf_table: etree._Element,
        target: etree._Element,
        ns: str,
        xsi_type_attr: str,
    ) -> None:
        """Конвертировать таблицу logform → EDT."""
        name = lf_table.get("name", "")
        el_id = lf_table.get("id", str(self._alloc_id()))

        item = etree.SubElement(
            target, "{%s}items" % NS_EDT,
            {xsi_type_attr: "form:Table"},
        )
        n = etree.SubElement(item, "{%s}name" % NS_EDT)
        n.text = name
        i = etree.SubElement(item, "{%s}id" % NS_EDT)
        i.text = el_id

        # DataPath
        dp = lf_table.find("{%s}DataPath" % ns)
        if dp is None:
            dp = lf_table.find("DataPath")
        if dp is not None and dp.text:
            edt_dp = etree.SubElement(
                item, "{%s}dataPath" % NS_EDT,
                {xsi_type_attr: "form:DataPath"},
            )
            seg = etree.SubElement(edt_dp, "{%s}segments" % NS_EDT)
            seg.text = dp.text

        # Child elements (columns)
        child_items = lf_table.find("{%s}ChildItems" % ns)
        if child_items is None:
            child_items = lf_table.find("ChildItems")
        if child_items is not None:
            self._convert_elements_logform_to_edt(child_items, item, ns, xsi_type_attr)

    def _convert_group_logform_to_edt(
        self,
        lf_group: etree._Element,
        target: etree._Element,
        ns: str,
        xsi_type_attr: str,
    ) -> None:
        """Конвертировать группу logform → EDT."""
        group_type = _local_tag(lf_group)
        name = lf_group.get("name", "")
        el_id = lf_group.get("id", str(self._alloc_id()))

        item = etree.SubElement(
            target, "{%s}items" % NS_EDT,
            {xsi_type_attr: "form:FormGroup"},
        )
        n = etree.SubElement(item, "{%s}name" % NS_EDT)
        n.text = name
        i = etree.SubElement(item, "{%s}id" % NS_EDT)
        i.text = el_id

        # Children
        child_items = lf_group.find("{%s}ChildItems" % ns)
        if child_items is None:
            child_items = lf_group.find("ChildItems")
        if child_items is not None:
            self._convert_elements_logform_to_edt(child_items, item, ns, xsi_type_attr)

        # Title
        title_el = lf_group.find("{%s}Title" % ns)
        if title_el is None:
            title_el = lf_group.find("Title")
        title_text = self._extract_v8_title(title_el) if title_el is not None else ""
        if title_text:
            _add_edt_title_el(item, title_text)

        # extendedTooltip
        _add_edt_companion_tooltip(item, name, self._alloc_id(), xsi_type_attr)

        # type
        t = etree.SubElement(item, "{%s}type" % NS_EDT)
        t.text = group_type

        # extInfo
        from mcp_forms.forms.generator import _edt_group_ext_info_type
        ext_type = _edt_group_ext_info_type(group_type)
        ei = etree.SubElement(
            item, "{%s}extInfo" % NS_EDT,
            {xsi_type_attr: ext_type},
        )

    def _convert_attribute_logform_to_edt(
        self,
        lf_attr: etree._Element,
        target: etree._Element,
        ns: str,
    ) -> None:
        """Конвертировать атрибут logform → EDT."""
        name = lf_attr.get("name", "")
        attr_id = lf_attr.get("id", "0")

        attr = etree.SubElement(target, "{%s}attributes" % NS_EDT)
        n = etree.SubElement(attr, "{%s}name" % NS_EDT)
        n.text = name
        i = etree.SubElement(attr, "{%s}id" % NS_EDT)
        i.text = attr_id

        # Type → valueType
        type_section = lf_attr.find("{%s}Type" % ns)
        if type_section is None:
            type_section = lf_attr.find("Type")
        if type_section is not None:
            ns_v8 = "http://v8.1c.ru/8.1/data/core"
            v8_type = type_section.find("{%s}Type" % ns_v8)
            if v8_type is not None and v8_type.text:
                vt = etree.SubElement(attr, "{%s}valueType" % NS_EDT)
                types_el = etree.SubElement(vt, "{%s}types" % NS_EDT)
                types_el.text = self._convert_type_to_managed(v8_type.text)

        # view, edit
        view = etree.SubElement(attr, "{%s}view" % NS_EDT)
        vc = etree.SubElement(view, "{%s}common" % NS_EDT)
        vc.text = "true"
        edit = etree.SubElement(attr, "{%s}edit" % NS_EDT)
        ec = etree.SubElement(edit, "{%s}common" % NS_EDT)
        ec.text = "true"

        # MainAttribute → main
        main = lf_attr.find("{%s}MainAttribute" % ns)
        if main is None:
            main = lf_attr.find("MainAttribute")
        if main is not None and main.text == "true":
            m = etree.SubElement(attr, "{%s}main" % NS_EDT)
            m.text = "true"

        # SavedData → savedData
        sd = lf_attr.find("{%s}SavedData" % ns)
        if sd is None:
            sd = lf_attr.find("SavedData")
        if sd is not None and sd.text == "true":
            s = etree.SubElement(attr, "{%s}savedData" % NS_EDT)
            s.text = "true"

    # =================== EDT → Logform ===================

    def _edt_to_logform(self, doc: FormDocument) -> str:
        """Конвертировать EDT (form:Form) → logform."""
        ns = NS_EDT
        ns_xsi = "http://www.w3.org/2001/XMLSchema-instance"
        xsi_type_attr = "{%s}type" % ns_xsi

        nsmap = {k or None: v for k, v in LOGFORM_NAMESPACES.items()}
        root = etree.Element("{%s}Form" % NS_LOGFORM, nsmap=nsmap)
        root.set("version", LOGFORM_VERSION)

        # AutoCommandBar
        acb_el = _edt_find(doc.root, "autoCommandBar", ns)
        acb = etree.SubElement(root, "{%s}AutoCommandBar" % NS_LOGFORM)
        if acb_el is not None:
            acb.set("name", _edt_text(acb_el, "name", ns, "ФормаКоманднаяПанель"))
            acb.set("id", _edt_text(acb_el, "id", ns, "-1"))
        else:
            acb.set("name", "ФормаКоманднаяПанель")
            acb.set("id", "-1")

        # ChildItems
        child_items = etree.SubElement(root, "{%s}ChildItems" % NS_LOGFORM)
        self._convert_elements_edt_to_logform(doc.root, child_items, ns, xsi_type_attr)

        # AutoTitle
        at = etree.SubElement(root, "{%s}AutoTitle" % NS_LOGFORM)
        at.text = _edt_text(doc.root, "autoTitle", ns, "true")

        # Attributes
        attrs_section = etree.SubElement(root, "{%s}Attributes" % NS_LOGFORM)
        for edt_attr in _edt_findall(doc.root, "attributes", ns):
            self._convert_attribute_edt_to_logform(edt_attr, attrs_section, ns)

        return _serialize_xml(root)

    def _convert_elements_edt_to_logform(
        self,
        source: etree._Element,
        target: etree._Element,
        ns: str,
        xsi_type_attr: str,
    ) -> None:
        """Рекурсивно конвертировать EDT items → logform."""
        for child in _edt_findall(source, "items", ns):
            xsi_type = child.get(xsi_type_attr, "")
            if xsi_type == "form:FormField":
                self._convert_field_edt_to_logform(child, target, ns, xsi_type_attr)
            elif xsi_type == "form:Table":
                self._convert_table_edt_to_logform(child, target, ns, xsi_type_attr)
            elif xsi_type == "form:FormGroup":
                self._convert_group_edt_to_logform(child, target, ns, xsi_type_attr)

    def _convert_field_edt_to_logform(
        self,
        edt_field: etree._Element,
        target: etree._Element,
        ns: str,
        xsi_type_attr: str,
    ) -> None:
        """Конвертировать EDT FormField → logform поле."""
        name = _edt_text(edt_field, "name", ns)
        el_id = _edt_text(edt_field, "id", ns, str(self._alloc_id()))
        field_type = _edt_text(edt_field, "type", ns, "InputField")

        field = etree.SubElement(target, "{%s}%s" % (NS_LOGFORM, field_type))
        field.set("name", name)
        field.set("id", el_id)

        # DataPath
        dp = _edt_find(edt_field, "dataPath", ns)
        if dp is not None:
            seg = _edt_find(dp, "segments", ns)
            if seg is not None and seg.text:
                dp_el = etree.SubElement(field, "{%s}DataPath" % NS_LOGFORM)
                dp_el.text = seg.text

        # Title
        title_text = _extract_edt_title(edt_field, ns)
        if title_text:
            _add_v8_title(field, title_text)

        # Companion elements
        _add_logform_companion(field, name, NS_LOGFORM, self._alloc_id)

    def _convert_table_edt_to_logform(
        self,
        edt_table: etree._Element,
        target: etree._Element,
        ns: str,
        xsi_type_attr: str,
    ) -> None:
        """Конвертировать EDT Table → logform Table."""
        name = _edt_text(edt_table, "name", ns)
        el_id = _edt_text(edt_table, "id", ns, str(self._alloc_id()))

        table = etree.SubElement(target, "{%s}Table" % NS_LOGFORM)
        table.set("name", name)
        table.set("id", el_id)

        # DataPath
        dp = _edt_find(edt_table, "dataPath", ns)
        if dp is not None:
            seg = _edt_find(dp, "segments", ns)
            if seg is not None and seg.text:
                dp_el = etree.SubElement(table, "{%s}DataPath" % NS_LOGFORM)
                dp_el.text = seg.text

        # Companion
        _add_logform_companion(table, name, NS_LOGFORM, self._alloc_id)

        # Children
        child_items = etree.SubElement(table, "{%s}ChildItems" % NS_LOGFORM)
        self._convert_elements_edt_to_logform(edt_table, child_items, ns, xsi_type_attr)

    def _convert_group_edt_to_logform(
        self,
        edt_group: etree._Element,
        target: etree._Element,
        ns: str,
        xsi_type_attr: str,
    ) -> None:
        """Конвертировать EDT FormGroup → logform группу."""
        name = _edt_text(edt_group, "name", ns)
        el_id = _edt_text(edt_group, "id", ns, str(self._alloc_id()))
        group_type = _edt_text(edt_group, "type", ns, "UsualGroup")

        group = etree.SubElement(target, "{%s}%s" % (NS_LOGFORM, group_type))
        group.set("name", name)
        group.set("id", el_id)

        # Title
        title_text = _extract_edt_title(edt_group, ns)
        if title_text:
            _add_v8_title(group, title_text)

        # ExtendedTooltip companion
        tt = etree.SubElement(group, "{%s}ExtendedTooltip" % NS_LOGFORM)
        tt.set("name", name + "РасширеннаяПодсказка")
        tt.set("id", str(self._alloc_id()))

        # Children
        child_items = etree.SubElement(group, "{%s}ChildItems" % NS_LOGFORM)
        self._convert_elements_edt_to_logform(edt_group, child_items, ns, xsi_type_attr)

    def _convert_attribute_edt_to_logform(
        self,
        edt_attr: etree._Element,
        target: etree._Element,
        ns: str,
    ) -> None:
        """Конвертировать EDT атрибут → logform Attribute."""
        name = _edt_text(edt_attr, "name", ns)
        attr_id = _edt_text(edt_attr, "id", ns, "0")

        attr = etree.SubElement(target, "{%s}Attribute" % NS_LOGFORM)
        attr.set("name", name)
        attr.set("id", attr_id)

        # valueType → Type with v8:Type
        vt = _edt_find(edt_attr, "valueType", ns)
        if vt is not None:
            type_text = _edt_text(vt, "types", ns)
            if type_text:
                ns_v8 = "http://v8.1c.ru/8.1/data/core"
                type_section = etree.SubElement(attr, "{%s}Type" % NS_LOGFORM)
                v8_type = etree.SubElement(type_section, "{%s}Type" % ns_v8)
                v8_type.text = self._convert_type_to_logform(type_text)

        # main → MainAttribute
        if _edt_text(edt_attr, "main", ns) == "true":
            m = etree.SubElement(attr, "{%s}MainAttribute" % NS_LOGFORM)
            m.text = "true"

        # savedData → SavedData
        if _edt_text(edt_attr, "savedData", ns) == "true":
            s = etree.SubElement(attr, "{%s}SavedData" % NS_LOGFORM)
            s.text = "true"


# =================== EDT helpers ===================


def _edt_find(element: etree._Element, local_name: str, ns: str) -> etree._Element | None:
    """Найти дочерний элемент по имени (с namespace EDT или без)."""
    el = element.find("{%s}%s" % (ns, local_name))
    if el is None:
        el = element.find(local_name)
    return el


def _edt_findall(element: etree._Element, local_name: str, ns: str) -> list[etree._Element]:
    """Найти все дочерние элементы по имени."""
    result = element.findall("{%s}%s" % (ns, local_name))
    result.extend(element.findall(local_name))
    return result


def _edt_text(element: etree._Element, local_name: str, ns: str, default: str = "") -> str:
    """Получить текст дочернего элемента."""
    el = _edt_find(element, local_name, ns)
    if el is not None and el.text:
        return el.text
    return default


# =================== Утилиты ===================


def _add_edt_companion_tooltip(
    parent: etree._Element, name: str, tooltip_id: int, xsi_type_attr: str
) -> None:
    """Добавить extendedTooltip в EDT-формате."""
    tt = etree.SubElement(parent, "{%s}extendedTooltip" % NS_EDT)
    n = etree.SubElement(tt, "{%s}name" % NS_EDT)
    n.text = name + "РасширеннаяПодсказка"
    i = etree.SubElement(tt, "{%s}id" % NS_EDT)
    i.text = str(tooltip_id)
    t = etree.SubElement(tt, "{%s}type" % NS_EDT)
    t.text = "Label"
    amw = etree.SubElement(tt, "{%s}autoMaxWidth" % NS_EDT)
    amw.text = "true"
    amh = etree.SubElement(tt, "{%s}autoMaxHeight" % NS_EDT)
    amh.text = "true"
    ei = etree.SubElement(
        tt, "{%s}extInfo" % NS_EDT,
        {xsi_type_attr: "form:LabelDecorationExtInfo"},
    )
    ha = etree.SubElement(ei, "{%s}horizontalAlign" % NS_EDT)
    ha.text = "Left"


def _add_edt_companion_menu(
    parent: etree._Element, name: str, menu_id: int
) -> None:
    """Добавить contextMenu в EDT-формате."""
    cm = etree.SubElement(parent, "{%s}contextMenu" % NS_EDT)
    n = etree.SubElement(cm, "{%s}name" % NS_EDT)
    n.text = name + "КонтекстноеМеню"
    i = etree.SubElement(cm, "{%s}id" % NS_EDT)
    i.text = str(menu_id)
    af = etree.SubElement(cm, "{%s}autoFill" % NS_EDT)
    af.text = "true"


def _add_edt_title_el(parent: etree._Element, text: str) -> None:
    """Добавить title в EDT-формате: <title><key>ru</key><value>текст</value></title>."""
    title = etree.SubElement(parent, "{%s}title" % NS_EDT)
    key = etree.SubElement(title, "{%s}key" % NS_EDT)
    key.text = "ru"
    val = etree.SubElement(title, "{%s}value" % NS_EDT)
    val.text = text


def _extract_edt_title(element: etree._Element, ns: str) -> str:
    """Извлечь текст заголовка из EDT title (key/value)."""
    title = _edt_find(element, "title", ns)
    if title is not None:
        return _edt_text(title, "value", ns)
    return ""


def _add_logform_companion(
    parent: etree._Element, name: str, ns: str, alloc_id=None
) -> None:
    """Добавить ContextMenu и ExtendedTooltip в logform-формате."""
    cm = etree.SubElement(parent, "{%s}ContextMenu" % ns)
    cm.set("name", name + "КонтекстноеМеню")
    cm.set("id", str(alloc_id()) if alloc_id else "-1")
    tt = etree.SubElement(parent, "{%s}ExtendedTooltip" % ns)
    tt.set("name", name + "РасширеннаяПодсказка")
    tt.set("id", str(alloc_id()) if alloc_id else "-1")


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
