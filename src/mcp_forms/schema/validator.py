"""Валидатор Form.xml.

Проверяет структурную корректность XML-форм 1С:
- Обязательные элементы (ContextMenu, ExtendedTooltip для полей)
- Уникальность id
- Допустимые дочерние элементы
- Связь DataPath ↔ Attribute.name
"""

from __future__ import annotations

from dataclasses import dataclass, field
from lxml import etree

from mcp_forms.forms.loader import FormDocument, NS_EDT, NS_LOGFORM

# Элементы формы, которые могут содержать ChildItems / Elements
_CONTAINER_TAGS = {
    "Form", "ChildItems", "Elements",
    "UsualGroup", "Pages", "Page", "Table",
    "CommandBar", "ContextMenu", "AutoCommandBar",
    "Popup", "ColumnGroup", "ButtonGroup",
}

# Элементы, требующие обязательные дочерние ContextMenu и ExtendedTooltip (logform)
_ELEMENTS_REQUIRING_COMPANIONS = {
    "InputField", "LabelField", "CheckBoxField", "RadioButtonField",
    "SpreadSheetDocumentField", "TextDocumentField", "FormattedDocumentField",
    "HTMLDocumentField", "PictureField", "CalendarField", "ChartField",
    "ProgressBarField", "TrackBarField", "PDFDocumentField",
    "GraphicalSchemaField", "PictureDecoration", "LabelDecoration",
    "Table",
}

# Элементы, которые должны иметь атрибуты id и name (logform)
_ELEMENTS_WITH_ID_NAME = {
    "InputField", "LabelField", "CheckBoxField", "RadioButtonField",
    "SpreadSheetDocumentField", "TextDocumentField", "FormattedDocumentField",
    "HTMLDocumentField", "PictureField", "CalendarField", "ChartField",
    "ProgressBarField", "TrackBarField", "PDFDocumentField",
    "GraphicalSchemaField", "PictureDecoration", "LabelDecoration",
    "Table", "Button", "UsualGroup", "Pages", "Page", "ColumnGroup",
    "ButtonGroup", "CommandBar", "ContextMenu", "AutoCommandBar",
    "Popup", "ExtendedTooltip", "SearchStringAddition",
    "SearchControlAddition", "ViewStatusAddition",
}

# Допустимые дочерние элементы ChildItems (logform)
_ALLOWED_CHILD_ITEMS = {
    "InputField", "LabelField", "CheckBoxField", "RadioButtonField",
    "SpreadSheetDocumentField", "TextDocumentField", "FormattedDocumentField",
    "HTMLDocumentField", "PictureField", "CalendarField", "ChartField",
    "ProgressBarField", "TrackBarField", "PDFDocumentField",
    "GraphicalSchemaField", "PictureDecoration", "LabelDecoration",
    "Table", "Button", "UsualGroup", "Pages", "Page", "ColumnGroup",
    "ButtonGroup", "CommandBar", "Popup", "SearchStringAddition",
    "SearchControlAddition", "ViewStatusAddition",
}


@dataclass
class ValidationError:
    """Ошибка валидации."""

    severity: str  # "error", "warning", "info"
    message: str
    element: str = ""  # XPath или имя элемента
    line: int = 0


@dataclass
class ValidationResult:
    """Результат валидации формы."""

    errors: list[ValidationError] = field(default_factory=list)
    format: str = ""
    version: str = ""

    @property
    def is_valid(self) -> bool:
        return not any(e.severity == "error" for e in self.errors)

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == "warning")

    def add_error(self, message: str, element: str = "", line: int = 0) -> None:
        self.errors.append(ValidationError("error", message, element, line))

    def add_warning(self, message: str, element: str = "", line: int = 0) -> None:
        self.errors.append(ValidationError("warning", message, element, line))

    def to_dict(self) -> dict:
        return {
            "valid": self.is_valid,
            "format": self.format,
            "version": self.version,
            "errors": self.error_count,
            "warnings": self.warning_count,
            "details": [
                {"severity": e.severity, "message": e.message, "element": e.element}
                for e in self.errors
            ],
        }


def validate_form(doc: FormDocument) -> ValidationResult:
    """Валидирует загруженный FormDocument."""
    result = ValidationResult(format=doc.format, version=doc.version)

    if doc.format == "unknown":
        result.add_error("Неизвестный формат Form.xml — не logform, managed или edt")
        return result

    if doc.format == "logform":
        _validate_logform(doc, result)
    elif doc.format == "edt":
        _validate_edt(doc, result)
    else:
        _validate_managed(doc, result)

    return result


def _validate_logform(doc: FormDocument, result: ValidationResult) -> None:
    """Валидация формата logform (конфигуратор)."""
    root = doc.root
    ns = doc.namespace

    # 1. Проверка root element
    local_tag = _local_name(root.tag)
    if local_tag != "Form":
        result.add_error(
            "Root элемент должен быть <Form>, найден: <%s>" % local_tag,
            element="root",
        )
        return

    # 2. Проверка version
    if not doc.version:
        result.add_warning("Отсутствует атрибут version у <Form>", element="Form")

    # 3. Сбор id → проверка уникальности
    # id элементов формы (ChildItems) и id атрибутов (Attributes) — разные пространства
    element_ids: dict[str, list[str]] = {}
    attribute_ids: dict[str, list[str]] = {}
    _collect_ids_by_scope(root, ns, element_ids, attribute_ids)

    for id_val, names in element_ids.items():
        if id_val == "-1":
            continue  # AutoCommandBar часто имеет id="-1"
        if len(names) > 1:
            result.add_error(
                "Дублирующийся id=%s у элементов формы: %s" % (id_val, ", ".join(names)),
                element="id=" + id_val,
            )

    for id_val, names in attribute_ids.items():
        if len(names) > 1:
            result.add_error(
                "Дублирующийся id=%s у атрибутов: %s" % (id_val, ", ".join(names)),
                element="Attribute id=" + id_val,
            )

    # 4. Проверка обязательных дочерних элементов (ContextMenu, ExtendedTooltip)
    _check_companion_elements(root, ns, result)

    # 5. Проверка Attributes — каждый Attribute должен иметь name и id
    _check_attributes_section(root, ns, result)

    # 6. Проверка DataPath ↔ Attribute
    _check_datapath_bindings(root, ns, result)


def _validate_managed(doc: FormDocument, result: ValidationResult) -> None:
    """Валидация формата managed (EDT)."""
    root = doc.root
    ns = doc.namespace

    local_tag = _local_name(root.tag)
    if local_tag != "ManagedForm":
        result.add_error(
            "Root элемент должен быть <ManagedForm>, найден: <%s>" % local_tag,
            element="root",
        )
        return

    # Базовая проверка: наличие Attributes
    attrs = root.find("{%s}Attributes" % ns) if ns else root.find("Attributes")
    if attrs is None:
        result.add_warning("Секция <Attributes> отсутствует", element="ManagedForm")

    # Проверка: Elements
    elements = root.find("{%s}Elements" % ns) if ns else root.find("Elements")
    if elements is None:
        result.add_warning("Секция <Elements> отсутствует", element="ManagedForm")


_EDT_VALID_ITEM_TYPES = {
    "form:FormField", "form:FormGroup", "form:Table",
    "form:Button", "form:Decoration",
}

# Handlers, которые должны быть в extInfo.handlers, а не в FormField.handlers
_EXTINFO_HANDLER_EVENTS = {
    "StartChoice", "Clearing", "Opening", "ChoiceProcessing",
    "AutoComplete", "TextEditEnd",
}

# Обязательные свойства InputFieldExtInfo
_INPUT_FIELD_REQUIRED_PROPS = {"chooseType", "typeDomainEnabled", "textEdit"}

# Обязательные свойства колонки таблицы
_TABLE_COLUMN_REQUIRED_PROPS = {"editMode", "showInHeader", "showInFooter"}


def _validate_edt(doc: FormDocument, result: ValidationResult) -> None:
    """Валидация формата EDT (form:Form)."""
    root = doc.root
    ns = NS_EDT

    local_tag = _local_name(root.tag)
    if local_tag != "Form":
        result.add_error(
            "Root элемент должен быть <form:Form>, найден: <%s>" % local_tag,
            element="root",
        )
        return

    ns_xsi = "http://www.w3.org/2001/XMLSchema-instance"
    xsi_type_attr = "{%s}type" % ns_xsi

    # Collect ids separately by scope (items, attributes, formCommands)
    item_ids: dict[str, list[str]] = {}
    attr_ids: dict[str, list[str]] = {}
    cmd_ids: dict[str, list[str]] = {}

    # Items (elements) — recursive
    for item in _findall_edt(root, "items", ns):
        _collect_edt_ids(item, ns, xsi_type_attr, item_ids)

    # Attributes — flat
    for attr in _findall_edt(root, "attributes", ns):
        id_el = _find_edt_child(attr, "id", ns)
        name_el = _find_edt_child(attr, "name", ns)
        if id_el is not None and id_el.text:
            name = name_el.text if name_el is not None else "?"
            attr_ids.setdefault(id_el.text, []).append(name)

    # FormCommands — flat
    for cmd in _findall_edt(root, "formCommands", ns):
        id_el = _find_edt_child(cmd, "id", ns)
        name_el = _find_edt_child(cmd, "name", ns)
        if id_el is not None and id_el.text:
            name = name_el.text if name_el is not None else "?"
            cmd_ids.setdefault(id_el.text, []).append(name)

    for scope_name, ids in [("элементов", item_ids), ("атрибутов", attr_ids), ("команд", cmd_ids)]:
        for id_val, names in ids.items():
            if id_val == "-1":
                continue
            if len(names) > 1:
                result.add_error(
                    "Дублирующийся id=%s у %s: %s" % (id_val, scope_name, ", ".join(names)),
                    element="id=" + id_val,
                )

    # Validate items have xsi:type
    for item in _iter_edt(root, "items", ns):
        xsi_type = item.get(xsi_type_attr, "")
        if not xsi_type:
            name_el = _find_edt_child(item, "name", ns)
            name_text = name_el.text if name_el is not None else "?"
            result.add_warning(
                "Элемент <items> без xsi:type: %s" % name_text,
                element=name_text,
            )
        elif xsi_type not in _EDT_VALID_ITEM_TYPES:
            result.add_warning(
                "Неизвестный xsi:type: %s" % xsi_type,
                element=xsi_type,
            )

    # Validate attributes have name, id, valueType
    for attr in _findall_edt(root, "attributes", ns):
        name_el = _find_edt_child(attr, "name", ns)
        id_el = _find_edt_child(attr, "id", ns)
        vt_el = _find_edt_child(attr, "valueType", ns)

        attr_name = name_el.text if name_el is not None else "?"
        if name_el is None:
            result.add_error("Атрибут без <name>", element="attributes")
        if id_el is None:
            result.add_error("Атрибут '%s' без <id>" % attr_name, element=attr_name)
        if vt_el is None:
            result.add_warning(
                "Атрибут '%s' без <valueType>" % attr_name, element=attr_name
            )

    # Validate dataPath has segments
    for dp in _iter_edt(root, "dataPath", ns):
        segments = _findall_edt(dp, "segments", ns)
        if not segments:
            parent = dp.getparent()
            parent_name = "?"
            if parent is not None:
                pn = _find_edt_child(parent, "name", ns)
                if pn is not None:
                    parent_name = pn.text or "?"
            result.add_warning(
                "dataPath без <segments> в элементе '%s'" % parent_name,
                element=parent_name,
            )

    # EDT-дефолты: soft-warnings для пропущенных свойств
    _check_edt_defaults(root, ns, ns_xsi, xsi_type_attr, result)


def _check_edt_defaults(
    root: etree._Element,
    ns: str,
    ns_xsi: str,
    xsi_type_attr: str,
    result: ValidationResult,
) -> None:
    """Проверяет наличие рекомендуемых EDT-свойств (soft-warnings)."""

    for item in _iter_edt(root, "items", ns):
        xsi_type = item.get(xsi_type_attr, "")
        name_el = _find_edt_child(item, "name", ns)
        name_text = name_el.text if name_el is not None else "?"

        # 3.1: InputFieldExtInfo без обязательных свойств
        if xsi_type == "form:FormField":
            type_el = _find_edt_child(item, "type", ns)
            if type_el is not None and type_el.text == "InputField":
                ext_info = _find_edt_child(item, "extInfo", ns)
                if ext_info is None:
                    result.add_warning(
                        "InputField '%s': отсутствует extInfo "
                        "(обязан содержать chooseType, typeDomainEnabled, textEdit)"
                        % name_text,
                        element=name_text,
                    )
                else:
                    missing = []
                    for prop in sorted(_INPUT_FIELD_REQUIRED_PROPS):
                        if _find_edt_child(ext_info, prop, ns) is None:
                            missing.append(prop)
                    if missing:
                        result.add_warning(
                            "InputField '%s': extInfo без %s"
                            % (name_text, ", ".join(missing)),
                            element=name_text,
                        )

            # 3.2: Колонка таблицы без обязательных свойств
            if _is_inside_table_edt(item, xsi_type_attr):
                missing = []
                for prop in sorted(_TABLE_COLUMN_REQUIRED_PROPS):
                    if _find_edt_child(item, prop, ns) is None:
                        missing.append(prop)
                if missing:
                    result.add_warning(
                        "Колонка '%s' в таблице без %s"
                        % (name_text, ", ".join(missing)),
                        element=name_text,
                    )

            # 3.4: Handler в неправильном месте
            for handler in _findall_edt(item, "handlers", ns):
                event_el = _find_edt_child(handler, "event", ns)
                if event_el is not None and event_el.text in _EXTINFO_HANDLER_EVENTS:
                    handler_name_el = _find_edt_child(handler, "name", ns)
                    handler_name = handler_name_el.text if handler_name_el is not None else "?"
                    result.add_warning(
                        "Handler '%s' (%s) должен быть в extInfo, "
                        "а не на уровне элемента '%s'"
                        % (event_el.text, handler_name, name_text),
                        element=name_text,
                    )

        # 3.3: Button без type вне CommandBar
        if xsi_type == "form:Button":
            type_el = _find_edt_child(item, "type", ns)
            if type_el is None and not _is_inside_commandbar_edt(item, ns, xsi_type_attr):
                result.add_warning(
                    "Button '%s' вне CommandBar без <type> "
                    "(ожидается UsualButton)" % name_text,
                    element=name_text,
                )

    # 3.5: containedObjects — EDT добавляет их автоматически
    for co in _iter_edt(root, "containedObjects", ns):
        parent = co.getparent()
        parent_name = "?"
        if parent is not None:
            pn = _find_edt_child(parent, "name", ns)
            if pn is not None:
                parent_name = pn.text or "?"
        result.add_warning(
            "containedObjects в '%s' — EDT обычно добавляет их автоматически"
            % parent_name,
            element=parent_name,
        )


def _is_inside_table_edt(item: etree._Element, xsi_type_attr: str) -> bool:
    """Проверяет, находится ли элемент внутри Table."""
    parent = item.getparent()
    while parent is not None:
        if parent.get(xsi_type_attr, "") == "form:Table":
            return True
        if _local_name(parent.tag) == "Form":
            return False
        parent = parent.getparent()
    return False


def _is_inside_commandbar_edt(
    item: etree._Element, ns: str, xsi_type_attr: str
) -> bool:
    """Проверяет, находится ли элемент внутри CommandBar-группы."""
    parent = item.getparent()
    while parent is not None:
        if parent.get(xsi_type_attr, "") == "form:FormGroup":
            type_el = _find_edt_child(parent, "type", ns)
            if type_el is not None and type_el.text == "CommandBar":
                return True
        if _local_name(parent.tag) == "Form":
            return False
        parent = parent.getparent()
    return False


def _find_edt_child(element: etree._Element, local_name: str, ns: str) -> etree._Element | None:
    """Найти дочерний элемент по локальному имени (с namespace или без)."""
    el = element.find("{%s}%s" % (ns, local_name))
    if el is None:
        el = element.find(local_name)
    return el


def _findall_edt(element: etree._Element, local_name: str, ns: str) -> list[etree._Element]:
    """Найти все дочерние элементы по локальному имени (с namespace или без, без дубликатов)."""
    result = element.findall("{%s}%s" % (ns, local_name))
    seen = set(id(el) for el in result)
    for el in element.findall(local_name):
        if id(el) not in seen:
            result.append(el)
    return result


def _iter_edt(root: etree._Element, local_name: str, ns: str):
    """Итерировать по элементам с данным именем (с namespace или без, без дубликатов)."""
    seen: set[int] = set()
    for el in root.iter("{%s}%s" % (ns, local_name)):
        seen.add(id(el))
        yield el
    for el in root.iter(local_name):
        if id(el) not in seen:
            yield el


def _collect_edt_ids(
    element: etree._Element,
    ns: str,
    xsi_type_attr: str,
    ids: dict[str, list[str]],
) -> None:
    """Рекурсивно собирает id из EDT-формы."""
    id_el = _find_edt_child(element, "id", ns)
    if id_el is not None and id_el.text:
        name_el = _find_edt_child(element, "name", ns)
        name = name_el.text if name_el is not None else _local_name(element.tag)
        ids.setdefault(id_el.text, []).append(name)

    for child in element:
        _collect_edt_ids(child, ns, xsi_type_attr, ids)


# =================== Вспомогательные функции ===================


def _local_name(tag: str) -> str:
    """Извлекает локальное имя тега без namespace."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _collect_ids_by_scope(
    root: etree._Element,
    ns: str,
    element_ids: dict[str, list[str]],
    attribute_ids: dict[str, list[str]],
) -> None:
    """Собирает id раздельно для элементов формы и атрибутов."""
    in_attributes = False
    for elem in root.iter():
        local = _local_name(elem.tag)
        if local == "Attributes":
            in_attributes = True
        elif local in ("ChildItems", "AutoCommandBar", "Commands"):
            in_attributes = False

        id_val = elem.get("id")
        if id_val is None:
            continue

        name = elem.get("name", local)
        if in_attributes and local == "Attribute":
            attribute_ids.setdefault(id_val, []).append(name)
        elif not in_attributes:
            element_ids.setdefault(id_val, []).append(name)


def _check_companion_elements(
    root: etree._Element, ns: str, result: ValidationResult
) -> None:
    """Проверяет наличие ContextMenu и ExtendedTooltip у элементов формы."""
    for elem in root.iter():
        local = _local_name(elem.tag)
        if local not in _ELEMENTS_REQUIRING_COMPANIONS:
            continue

        elem_name = elem.get("name", local)

        # Ищем дочерние ContextMenu и ExtendedTooltip
        has_context_menu = False
        has_extended_tooltip = False
        for child in elem:
            child_local = _local_name(child.tag)
            if child_local == "ContextMenu":
                has_context_menu = True
            elif child_local == "ExtendedTooltip":
                has_extended_tooltip = True

        if not has_context_menu:
            result.add_warning(
                "<%s name=\"%s\">: отсутствует дочерний <ContextMenu>" % (local, elem_name),
                element=elem_name,
            )
        if not has_extended_tooltip:
            result.add_warning(
                "<%s name=\"%s\">: отсутствует дочерний <ExtendedTooltip>" % (local, elem_name),
                element=elem_name,
            )


def _check_attributes_section(
    root: etree._Element, ns: str, result: ValidationResult
) -> None:
    """Проверяет секцию Attributes."""
    attrs_section = None
    for child in root:
        if _local_name(child.tag) == "Attributes":
            attrs_section = child
            break

    if attrs_section is None:
        return

    attr_names = set()
    attr_ids = set()

    for attr in attrs_section:
        if _local_name(attr.tag) != "Attribute":
            continue

        name = attr.get("name", "")
        id_val = attr.get("id", "")

        if not name:
            result.add_error("Атрибут формы без name", element="Attributes/Attribute")

        if not id_val:
            result.add_error(
                "Атрибут формы '%s' без id" % name, element="Attribute[%s]" % name
            )

        if name in attr_names:
            result.add_error(
                "Дублирующееся имя атрибута: '%s'" % name,
                element="Attribute[%s]" % name,
            )
        attr_names.add(name)

        if id_val and id_val in attr_ids:
            result.add_error(
                "Дублирующийся id атрибута: '%s'" % id_val,
                element="Attribute[%s]" % name,
            )
        if id_val:
            attr_ids.add(id_val)

        # Проверка наличия Type
        has_type = any(_local_name(c.tag) == "Type" for c in attr)
        if not has_type:
            result.add_warning(
                "Атрибут '%s': отсутствует <Type>" % name,
                element="Attribute[%s]" % name,
            )


def _check_datapath_bindings(
    root: etree._Element, ns: str, result: ValidationResult
) -> None:
    """Проверяет что DataPath ссылается на существующий Attribute."""
    # Собираем имена атрибутов
    attr_names: set[str] = set()
    for elem in root.iter():
        if _local_name(elem.tag) == "Attribute":
            name = elem.get("name", "")
            if name:
                attr_names.add(name)

    if not attr_names:
        return

    # Проверяем DataPath
    for elem in root.iter():
        if _local_name(elem.tag) != "DataPath":
            continue

        datapath = (elem.text or "").strip()
        if not datapath:
            continue

        # DataPath может быть вида "Объект.Поле" или просто "МойРеквизит"
        top_level = datapath.split(".")[0]

        if top_level not in attr_names:
            # Не ошибка — может быть стандартный путь (Объект.Code и т.д.)
            # Но если точно не Объект* — предупреждение
            if not top_level.startswith("Объект") and top_level not in ("Object",):
                result.add_warning(
                    "DataPath '%s': атрибут '%s' не найден в секции Attributes"
                    % (datapath, top_level),
                    element="DataPath",
                )
