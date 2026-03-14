"""Шаблоны типовых форм 1С."""

from __future__ import annotations

from mcp_forms.forms.generator import (
    FormAttributeSpec,
    FormFieldSpec,
    FormGroupSpec,
    FormSpec,
    FormTableColumnSpec,
    FormTableSpec,
)


def catalog_element_form(
    catalog_name: str,
    fields: list[str] | None = None,
    format: str = "logform",
) -> FormSpec:
    """Шаблон ФормаЭлемента справочника."""
    if fields is None:
        fields = ["Наименование"]

    elements = [
        FormFieldSpec(name=f, data_path="Объект.%s" % f) for f in fields
    ]

    return FormSpec(
        object_type="Catalog",
        object_name=catalog_name,
        form_type="ФормаЭлемента",
        format=format,
        attributes=[
            FormAttributeSpec(
                name="Объект",
                type_name="cfg:CatalogObject.%s" % catalog_name,
                is_main=True,
                save_data=True,
            ),
        ],
        elements=elements,
    )


def document_form(
    document_name: str,
    header_fields: list[str] | None = None,
    table_name: str = "",
    table_columns: list[str] | None = None,
    format: str = "logform",
) -> FormSpec:
    """Шаблон ФормаДокумента."""
    if header_fields is None:
        header_fields = ["Дата", "Номер"]

    elements: list[FormFieldSpec | FormGroupSpec | FormTableSpec] = []

    # Шапка
    header = FormGroupSpec(
        name="ГруппаШапка",
        title="Шапка",
        direction="Vertical",
        children=[
            FormFieldSpec(name=f, data_path="Объект.%s" % f) for f in header_fields
        ],
    )
    elements.append(header)

    # Табличная часть
    if table_name and table_columns:
        table = FormTableSpec(
            name=table_name,
            data_path="Объект.%s" % table_name,
            columns=[
                FormTableColumnSpec(name=c, data_path="Объект.%s.%s" % (table_name, c))
                for c in table_columns
            ],
        )
        elements.append(table)

    return FormSpec(
        object_type="Document",
        object_name=document_name,
        form_type="ФормаДокумента",
        format=format,
        attributes=[
            FormAttributeSpec(
                name="Объект",
                type_name="cfg:DocumentObject.%s" % document_name,
                is_main=True,
                save_data=True,
            ),
        ],
        elements=elements,
    )


def data_processor_form(
    processor_name: str,
    fields: list[str] | None = None,
    format: str = "logform",
) -> FormSpec:
    """Шаблон формы обработки."""
    if fields is None:
        fields = []

    elements = [
        FormFieldSpec(name=f, data_path="Объект.%s" % f) for f in fields
    ]

    return FormSpec(
        object_type="DataProcessor",
        object_name=processor_name,
        form_type="Форма",
        format=format,
        attributes=[
            FormAttributeSpec(
                name="Объект",
                type_name="cfg:DataProcessorObject.%s" % processor_name,
                is_main=True,
                save_data=True,
            ),
        ],
        elements=elements,
    )


TEMPLATE_REGISTRY: dict[str, callable] = {
    "catalog_element": catalog_element_form,
    "document": document_form,
    "data_processor": data_processor_form,
}
