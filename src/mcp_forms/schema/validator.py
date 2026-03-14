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

from mcp_forms.forms.loader import FormDocument, NS_LOGFORM

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
        result.add_error("Неизвестный формат Form.xml — не logform и не managed")
        return result

    if doc.format == "logform":
        _validate_logform(doc, result)
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
