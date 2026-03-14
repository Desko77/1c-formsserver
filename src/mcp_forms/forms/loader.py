"""Загрузчик Form.xml с автоопределением формата."""

from __future__ import annotations

from dataclasses import dataclass, field
from lxml import etree

# Namespace URI для двух форматов
NS_LOGFORM = "http://v8.1c.ru/8.3/xcf/logform"
NS_MANAGED = "http://v8.1c.ru/8.3/xcf/managed"

# Все namespace'ы формата logform (конфигуратор)
LOGFORM_NAMESPACES = {
    "": NS_LOGFORM,
    "app": "http://v8.1c.ru/8.2/managed-application/core",
    "cfg": "http://v8.1c.ru/8.1/data/enterprise/current-config",
    "dcscor": "http://v8.1c.ru/8.1/data-composition-system/core",
    "dcssch": "http://v8.1c.ru/8.1/data-composition-system/schema",
    "dcsset": "http://v8.1c.ru/8.1/data-composition-system/settings",
    "ent": "http://v8.1c.ru/8.1/data/enterprise",
    "lf": "http://v8.1c.ru/8.2/managed-application/logform",
    "style": "http://v8.1c.ru/8.1/data/ui/style",
    "sys": "http://v8.1c.ru/8.1/data/ui/fonts/system",
    "v8": "http://v8.1c.ru/8.1/data/core",
    "v8ui": "http://v8.1c.ru/8.1/data/ui",
    "web": "http://v8.1c.ru/8.1/data/ui/colors/web",
    "win": "http://v8.1c.ru/8.1/data/ui/colors/windows",
    "xr": "http://v8.1c.ru/8.3/xcf/readable",
    "xs": "http://www.w3.org/2001/XMLSchema",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

MANAGED_NAMESPACES = {
    "": NS_MANAGED,
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xs": "http://www.w3.org/2001/XMLSchema",
    "xr": "http://v8.1c.ru/8.3/xcf/readable",
}


@dataclass
class FormDocument:
    """Загруженный Form.xml."""

    tree: etree._ElementTree
    root: etree._Element
    format: str  # "logform" или "managed"
    version: str = ""  # атрибут version из root
    encoding: str = "UTF-8"

    @property
    def namespace(self) -> str:
        return NS_LOGFORM if self.format == "logform" else NS_MANAGED

    def ns_tag(self, local_name: str) -> str:
        """Возвращает полное имя тега с namespace: {ns}localname."""
        return "{%s}%s" % (self.namespace, local_name)

    def find(self, xpath: str) -> etree._Element | None:
        """Поиск элемента по XPath с учётом namespace."""
        ns = {"f": self.namespace, "v8": "http://v8.1c.ru/8.1/data/core"}
        return self.root.find(xpath, ns)

    def findall(self, xpath: str) -> list[etree._Element]:
        ns = {"f": self.namespace, "v8": "http://v8.1c.ru/8.1/data/core"}
        return self.root.findall(xpath, ns)


def detect_format(xml_content: str | bytes) -> str:
    """Определяет формат Form.xml по root element и namespace.

    Returns: "logform", "managed" или "unknown"
    """
    if isinstance(xml_content, str):
        xml_content = xml_content.encode("utf-8")

    # Убираем BOM если есть
    if xml_content.startswith(b"\xef\xbb\xbf"):
        xml_content = xml_content[3:]

    try:
        root = etree.fromstring(xml_content)
    except etree.XMLSyntaxError:
        return "unknown"

    tag = root.tag
    if tag == "{%s}Form" % NS_LOGFORM or tag == "Form":
        return "logform"
    if tag == "{%s}ManagedForm" % NS_MANAGED or tag == "ManagedForm":
        return "managed"

    # Fallback: проверяем namespace
    ns = root.nsmap.get(None, "")
    if NS_LOGFORM in ns:
        return "logform"
    if NS_MANAGED in ns:
        return "managed"

    return "unknown"


def load_form(xml_content: str | bytes) -> FormDocument:
    """Загружает Form.xml и возвращает FormDocument."""
    if isinstance(xml_content, str):
        raw = xml_content.encode("utf-8")
    else:
        raw = xml_content

    # Убираем BOM
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]

    fmt = detect_format(raw)

    parser = etree.XMLParser(remove_blank_text=False, encoding="utf-8")
    tree = etree.ElementTree(etree.fromstring(raw, parser))
    root = tree.getroot()

    version = root.get("version", "")

    return FormDocument(
        tree=tree,
        root=root,
        format=fmt,
        version=version,
    )
