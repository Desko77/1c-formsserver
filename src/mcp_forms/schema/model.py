"""Pydantic-модели для представления схемы форм 1С из Xcore."""

from __future__ import annotations

from pydantic import BaseModel


class XcoreEnumValue(BaseModel):
    """Значение перечисления."""

    name: str
    value: int
    comment: str = ""


class XcoreEnum(BaseModel):
    """Перечисление (enum) из Xcore."""

    name: str
    values: list[XcoreEnumValue] = []


class XcoreProperty(BaseModel):
    """Свойство класса/интерфейса."""

    name: str
    type: str  # имя типа (String, int, boolean, FormChildrenGroup, Color...)
    is_list: bool = False  # [] — коллекция
    is_containment: bool = False  # contains — владение (composition)
    is_reference: bool = False  # refers — ссылка
    is_unsettable: bool = False  # unsettable — может быть не задано
    is_transient: bool = False  # transient — не сериализуется
    default: str = ""  # значение по умолчанию
    comment: str = ""  # комментарий (// since 8.5.1, deprecated и т.д.)
    multiplicity: str = ""  # [1], [0..1] и т.д.


class XcoreClass(BaseModel):
    """Класс или интерфейс из Xcore."""

    name: str
    kind: str = "class"  # class, abstract class, interface
    extends: list[str] = []  # базовые классы/интерфейсы
    properties: list[XcoreProperty] = []
    comment: str = ""


class XcoreType(BaseModel):
    """Обёртка Java-типа (type X wraps java.Class)."""

    name: str
    wraps: str


class FormSchema(BaseModel):
    """Полная схема форм, извлечённая из Form.xcore."""

    package: str = ""
    ns_uri: str = ""
    ns_prefix: str = ""
    imports: list[str] = []
    classes: dict[str, XcoreClass] = {}
    enums: dict[str, XcoreEnum] = {}
    types: dict[str, XcoreType] = {}

    @property
    def class_count(self) -> int:
        return len(self.classes)

    @property
    def enum_count(self) -> int:
        return len(self.enums)

    def get_class(self, name: str) -> XcoreClass | None:
        return self.classes.get(name)

    def get_enum(self, name: str) -> XcoreEnum | None:
        return self.enums.get(name)

    def get_all_properties(self, class_name: str) -> list[XcoreProperty]:
        """Все свойства класса, включая унаследованные."""
        cls = self.classes.get(class_name)
        if not cls:
            return []
        props = list(cls.properties)
        for base_name in cls.extends:
            base = self.classes.get(base_name)
            if base:
                props.extend(self.get_all_properties(base_name))
        return props
