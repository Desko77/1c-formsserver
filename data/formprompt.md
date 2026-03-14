## Дополнение контекста
**Ты эксперт по программированию XML форм 1С 8.3.25.*.**  
**Ниже ОПИСАНИЕ БАЗЫ ЗНАНИЙ в формате JSON по созданию и валидации XMLформ 1С:**  
```
{
    "tags": { - вся информация по тэгам
        "Имя тэга": { - Имя тэга (уникальный)
            "description": "", - краткое описание тэга
            "mandatory_children_tags": [], - обязательные дочерние тэги, использовать для валидации
            "allowed_children_tags": [], - доступные дочерние тэги, использовать для валидации
            "mandatory_attributes": [], - обязательные атрибуты тэга, использовать для валидации
            "allowed_attributes": [], - доступные атрибуты тэга, использовать для валидации
            "allowed_values": [
                {
                    "item": "", - представление значения
                    "is_common": - true/false, булево, является ли значение обобщенным типом, если истина тогда смотрим описание обобщенного типа в "tags_common_types"
                }
            ], - доступные значения тэга
            "allowed_parents_tags": [] - разрешенные родители тэга
        },
    ...
    },
    "attributes": { - вся информация по атрибутам тэгов
        "Имя атрибута тэга": { - имя атрибута (уникальный)
            "description": "", - краткое описание атрибута, использовать для валидации
            "allowed_parents_tags": [] - разрешенные родители (родители - только тэги), использовать для валидации
            "allowed_values": [
                {
                    "item": "", - значение
                    "is_common": - true/false, булево, является ли значение обобщенным типом, если истина тогда смотрим описание обобщенного типа в "attributes_common_types"
                }
            ]
        },
    ...
    },
    "tags_common_types": { - вся информация по обобщенным типам тэгов
        "Представление значения": { - представление значения (уникальный)
            "description": "", - краткое описание
            "examples": [] - список примеров
        },
    ...
    },
    "attributes_common_types": { - вся информация по обобщенным типам атрибутов тэгов
        "Представление значения": { - представление значения (уникальный)
            "description": "", - краткое описание
            "examples": [] - список примеров
        },
    ...
    }
}
```
  
**В базе знаний используются обобщенные типы значений тэгов и атрибутов, когда видишь доступное значение в "allowed_values", которое начинается с @**
**, - обращаешься к "tags_common_types" или "attributes_common_types" за подробностями.**  
  
**БАЗА ЗНАНИЙ:**  
```
{
    "tags": {
        "Form": {
            "allowed_parents_tags": [],
            "allowed_attributes": [
                "version",
                "xmlns",
                "xmlns:app",
                "xmlns:cfg",
                "xmlns:dcscor",
                "xmlns:dcssch",
                "xmlns:dcsset",
                "xmlns:ent",
                "xmlns:lf",
                "xmlns:style",
                "xmlns:sys",
                "xmlns:v8",
                "xmlns:v8ui",
                "xmlns:web",
                "xmlns:win",
                "xmlns:xr",
                "xmlns:xs",
                "xmlns:xsi"
            ],
            "mandatory_attributes": [
                "version",
                "xmlns",
                "xmlns:app",
                "xmlns:cfg",
                "xmlns:dcscor",
                "xmlns:dcssch",
                "xmlns:dcsset",
                "xmlns:ent",
                "xmlns:lf",
                "xmlns:style",
                "xmlns:sys",
                "xmlns:v8",
                "xmlns:v8ui",
                "xmlns:web",
                "xmlns:win",
                "xmlns:xr",
                "xmlns:xs",
                "xmlns:xsi"
            ],
            "allowed_children_tags": [
                "WindowOpeningMode",
                "Width",
                "Parameters",
                "UsePostingMode",
                "SettingsStorage",
                "Title",
                "ViewModeApplicationOnSetReportResult",
                "ReportResult",
                "CommandInterface",
                "SaveDataInSettings",
                "ChildItems",
                "CommandSet",
                "Commands",
                "UseForFoldersAndItems",
                "VariantAppearance",
                "ChildrenAlign",
                "ShowTitle",
                "VerticalSpacing",
                "ShowCloseButton",
                "VerticalAlign",
                "DetailsData",
                "CommandBarLocation",
                "AutoURL",
                "VerticalScroll",
                "HorizontalSpacing",
                "HorizontalAlign",
                "AutoShowState",
                "RepostOnWrite",
                "ConversationsRepresentation",
                "MobileDeviceCommandBarContent",
                "CollapseItemsByImportanceVariant",
                "Group",
                "AutoSaveDataInSettings",
                "CustomSettingsFolder",
                "AutoCommandBar",
                "AutoTitle",
                "AutoTime",
                "ReportFormType",
                "EnterKeyBehavior",
                "AutoFillCheck",
                "Enabled",
                "Height",
                "SaveWindowSettings",
                "Attributes",
                "Customizable",
                "ReportResultViewMode",
                "ScalingMode",
                "Events",
                "ChildItemsWidth"
            ],
            "mandatory_children_tags": [
                "AutoCommandBar",
                "Attributes"
            ],
            "allowed_values": [],
            "description": "форма"
        },
        "ChildItems": {
            "allowed_parents_tags": [
                "UsualGroup",
                "Table",
                "Pages",
                "Form",
                "Popup",
                "ContextMenu",
                "Page",
                "CommandBar",
                "ColumnGroup",
                "ButtonGroup",
                "AutoCommandBar"
            ],
            "allowed_attributes": [],
            "mandatory_attributes": [],
            "allowed_children_tags": [
                "InputField",
                "PictureDecoration",
                "SpreadSheetDocumentField",
                "GraphicalSchemaField",
                "LabelDecoration",
                "ProgressBarField",
                "SearchStringAddition",
                "FormattedDocumentField",
                "TextDocumentField",
                "ColumnGroup",
                "PictureField",
                "Pages",
                "Button",
                "Page",
                "Table",
                "ButtonGroup",
                "UsualGroup",
                "LabelField",
                "PDFDocumentField",
                "CheckBoxField",
                "Popup",
                "CalendarField",
                "ChartField",
                "HTMLDocumentField",
                "SearchControlAddition",
                "RadioButtonField",
                "CommandBar",
                "TrackBarField"
            ],
            "mandatory_children_tags": [],
            "allowed_values": [],
            "description": "подчиненные элементы"
        },
        "InputField": {
            "allowed_parents_tags": [
                "ChildItems"
            ],
            "allowed_attributes": [
                "DisplayImportance",
                "id",
                "name"
            ],
            "mandatory_attributes": [
                "id",
                "name"
            ],
            "allowed_children_tags": [
                "ChoiceList",
                "UserVisible",
                "TitleTextColor",
                "AutoCellHeight",
                "MultipleValueDataPath",
                "TitleBackColor",
                "ChoiceListHeight",
                "HeaderHorizontalAlign",
                "ChoiceButtonPicture",
                "BorderColor",
                "FooterDataPath",
                "GroupHorizontalAlign",
                "HorizontalAlign",
                "ExtendedEdit",
                "AutoMaxWidth",
                "ChooseType",
                "AutoCorrectionOnTextInput",
                "SpecialTextInputMode",
                "EditFormat",
                "MinValue",
                "WarningOnEditRepresentation",
                "Mask",
                "TitleLocation",
                "WarningOnEdit",
                "ShowInHeader",
                "ShowInFooter",
                "ChoiceParameterLinks",
                "ChoiceHistoryOnInput",
                "DataPath",
                "DefaultItem",
                "DropListButton",
                "ChoiceButtonRepresentation",
                "MultipleValuesFont",
                "Title",
                "InputHint",
                "AutoMarkIncomplete",
                "Format",
                "SkipOnInput",
                "Shortcut",
                "FooterPicture",
                "ClearButton",
                "QuickChoice",
                "AutoShowClearButtonMode",
                "MultipleValuePresentDataPath",
                "Height",
                "Font",
                "GroupVerticalAlign",
                "AutoChoiceIncomplete",
                "HeaderPicture",
                "Enabled",
                "ToolTip",
                "HeightControlVariant",
                "EditTextUpdate",
                "ShowCheckBoxesInDropList",
                "ContextMenu",
                "TextColor",
                "MaxHeight",
                "VerticalStretch",
                "ChoiceListButton",
                "ChoiceParameters",
                "ChoiceForm",
                "ExtendedTooltip",
                "Events",
                "HorizontalStretch",
                "CellHyperlink",
                "MultiLine",
                "EditMode",
                "SpinButton",
                "CreateButton",
                "TitleHeight",
                "ToolTipRepresentation",
                "ChoiceButton",
                "AutoShowOpenButtonMode",
                "FooterTextColor",
                "MultipleValuesBackColor",
                "BackColor",
                "DropListWidth",
                "FooterHorizontalAlign",
                "FooterText",
                "FooterFont",
                "OpenButton",
                "AvailableTypes",
                "AllowInputEmptyMultipleValues",
                "ReadOnly",
                "TextEdit",
                "MultipleValuePictureShape",
                "ListChoiceMode",
                "MaxValue",
                "ExtendedEditMultipleValues",
                "VerticalAlign",
                "Width",
                "MarkNegatives",
                "MultipleValuesTextColor",
                "MaxWidth",
                "ChoiceFoldersAndItems",
                "PasswordMode",
                "TypeDomainEnabled",
                "Visible",
                "IncompleteChoiceMode",
                "AutoMaxHeight",
                "TitleFont",
                "FixingInTable",
                "Wrap",
                "TypeLink",
                "MultipleValuePictureDataPath",
                "SpellCheckingOnTextInput"
            ],
            "mandatory_children_tags": [
                "ExtendedTooltip",
                "ContextMenu"
            ],
            "allowed_values": [],
            "description": "поле ввода"
        },
        "v8:lang": {
            "allowed_parents_tags": [
                "v8:item"
            ],
            "allowed_attributes": [],
            "mandatory_attributes": [],
            "allowed_children_tags": [],
            "mandatory_children_tags": [],
            "allowed_values": [
                "@LangCode_КодЯзыка"
            ],
            "description": "язык"
        },
        "DataPath": {
            "allowed_parents_tags": [
                "Table",
                "SpreadSheetDocumentField",
                "PictureField",
                "TrackBarField",
                "PDFDocumentField",
                "InputField",
                "HTMLDocumentField",
                "RadioButtonField",
                "GraphicalSchemaField",
                "LabelField",
                "FormattedDocumentField",
                "ProgressBarField",
                "CheckBoxField",
                "TextDocumentField",
                "ChartField",
                "CalendarField",
                "Button"
            ],
            "allowed_attributes": [],
            "mandatory_attributes": [],
            "allowed_children_tags": [],
            "mandatory_children_tags": [],
            "allowed_values": [
                "@IBDataPath_ПутьКДаннымИБ"
            ],
            "description": "путь к данным"
        },
        "Attributes": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_attributes": [],
            "mandatory_attributes": [],
            "allowed_children_tags": [
                "ConditionalAppearance",
                "Attribute"
            ],
            "mandatory_children_tags": [],
            "allowed_values": [],
            "description": "реквизиты"
        },
        "#text": null,
        "v8:item": {
            "allowed_parents_tags": [
                "Title",
                "Presentation",
                "NonselectedPictureText",
                "InputHint",
                "Format",
                "FooterText",
                "ToolTip",
                "EditFormat",
                "WarningOnEdit",
                "CollapsedRepresentationTitle"
            ],
            "allowed_attributes": [],
            "mandatory_attributes": [],
            "allowed_children_tags": [
                "v8:content",
                "v8:lang"
            ],
            "mandatory_children_tags": [
                "v8:content",
                "v8:lang"
            ],
            "allowed_values": [],
            "description": "строка с учетом языка"
        },
        "Type": {
            "allowed_parents_tags": [
                "Item",
                "Column",
                "Button",
                "Attribute",
                "Parameter",
                "AdditionSource"
            ],
            "allowed_attributes": [],
            "mandatory_attributes": [],
            "allowed_children_tags": [
                "v8:StringQualifiers",
                "v8:Type",
                "v8:TypeSet",
                "v8:DateQualifiers",
                "v8:NumberQualifiers"
            ],
            "mandatory_children_tags": [],
            "allowed_values": [
                "Added",
                "Auto",
                "CommandBarButton",
                "CommandBarHyperlink",
                "Hyperlink",
                "SearchControl",
                "SearchStringRepresentation",
                "UsualButton",
                "ViewStatusRepresentation"
            ],
            "description": "тип"
        },
        "ExtendedEditMultipleValues": {
            "allowed_parents_tags": [
                "InputField"
            ],
            "allowed_attributes": [],
            "mandatory_attributes": [],
            "allowed_children_tags": [],
            "mandatory_children_tags": [],
            "allowed_values": [
                "@Boolean_Булево"
            ],
            "description": "разрешить расширенное редактирование нескольких значений"
        },
        "ContextMenu": {
            "allowed_parents_tags": [
                "ViewStatusAddition",
                "TextDocumentField",
                "Table",
                "SpreadSheetDocumentField",
                "SearchStringAddition",
                "PictureField",
                "SearchControlAddition",
                "TrackBarField",
                "PDFDocumentField",
                "LabelDecoration",
                "InputField",
                "HTMLDocumentField",
                "RadioButtonField",
                "GraphicalSchemaField",
                "LabelField",
                "FormattedDocumentField",
                "PictureDecoration",
                "ProgressBarField",
                "CheckBoxField",
                "ChartField",
                "CalendarField"
            ],
            "allowed_attributes": [
                "id",
                "name"
            ],
            "mandatory_attributes": [
                "id",
                "name"
            ],
            "allowed_children_tags": [
                "ChildItems",
                "Autofill"
            ],
            "mandatory_children_tags": [],
            "allowed_values": [],
            "description": "контекстное меню"
        },
        "ExtendedTooltip": {
            "allowed_parents_tags": [
                "ViewStatusAddition",
                "UsualGroup",
                "TextDocumentField",
                "Table",
                "SpreadSheetDocumentField",
                "SearchStringAddition",
                "ProgressBarField",
                "RadioButtonField",
                "Popup",
                "SearchControlAddition",
                "PictureField",
                "TrackBarField",
                "PDFDocumentField",
                "HTMLDocumentField",
                "GraphicalSchemaField",
                "LabelField",
                "Pages",
                "PictureDecoration",
                "FormattedDocumentField",
                "CommandBar",
                "InputField",
                "Page",
                "LabelDecoration",
                "CheckBoxField",
                "ColumnGroup",
                "ChartField",
                "CalendarField",
                "ButtonGroup",
                "Button"
            ],
            "allowed_attributes": [
                "id",
                "name"
            ],
            "mandatory_attributes": [
                "id",
                "name"
            ],
            "allowed_children_tags": [
                "TitleHeight",
                "Title",
                "MaxWidth",
                "Events",
                "Width",
                "VerticalAlign",
                "GroupHorizontalAlign",
                "TextColor",
                "Hyperlink",
                "VerticalStretch",
                "AutoMaxHeight",
                "AutoMaxWidth",
                "Font",
                "GroupVerticalAlign",
                "BackColor",
                "HorizontalAlign",
                "HorizontalStretch",
                "Height"
            ],
            "mandatory_children_tags": [],
            "allowed_values": [],
            "description": "расширенная подсказка"
        },
        "Attribute": {
            "allowed_parents_tags": [
                "Attributes"
            ],
            "allowed_attributes": [
                "id",
                "name"
            ],
            "mandatory_attributes": [
                "id",
                "name"
            ],
            "allowed_children_tags": [
                "Type",
                "FillCheck",
                "Columns",
                "MainAttribute",
                "View",
                "Settings",
                "Save",
                "Title",
                "Edit",
                "FunctionalOptions",
                "UseAlways",
                "SavedData"
            ],
            "mandatory_children_tags": [
                "Type"
            ],
            "allowed_values": [],
            "description": "реквизит"
        },
        "Title": {
            "allowed_parents_tags": [
                "UsualGroup",
                "TrackBarField",
                "TextDocumentField",
                "Table",
                "SpreadSheetDocumentField",
                "SearchStringAddition",
                "ProgressBarField",
                "RadioButtonField",
                "Popup",
                "Pages",
                "HTMLDocumentField",
                "LabelField",
                "GraphicalSchemaField",
                "PictureDecoration",
                "FormattedDocumentField",
                "SearchControlAddition",
                "PictureField",
                "Form",
                "Page",
                "CommandBar",
                "InputField",
                "LabelDecoration",
                "Command",
                "Column",
                "CheckBoxField",
                "ColumnGroup",
                "ExtendedTooltip",
                "ChartField",
                "CalendarField",
                "ButtonGroup",
                "Attribute",
                "Button"
            ],
            "allowed_attributes": [
                "formatted"
            ],
            "mandatory_attributes": [],
            "allowed_children_tags": [
                "v8:item"
            ],
            "mandatory_children_tags": [],
            "allowed_values": [],
            "description": "заголовок"
        },
        "v8:content": {
            "allowed_parents_tags": [
                "v8:item"
            ],
            "allowed_attributes": [],
            "mandatory_attributes": [],
            "allowed_children_tags": [],
            "mandatory_children_tags": [],
            "allowed_values": [
                "@String_Строка"
            ],
            "description": "текст"
        },
        "v8:Type": {
            "allowed_parents_tags": [
                "Type",
                "Settings",
                "AvailableTypes"
            ],
            "allowed_attributes": [
                "xmlns:d5p1",
                "xmlns:fd",
                "xmlns:mxl",
                "xmlns:pdfdoc"
            ],
            "mandatory_attributes": [],
            "allowed_children_tags": [],
            "mandatory_children_tags": [],
            "allowed_values": [
                "@TypeFromIB_ТипИзИБ"
            ],
            "description": "тип"
        }
    },
    "attributes": {
        "xmlns:dcssch": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns": {
            "allowed_parents_tags": [
                "orderType",
                "Form",
                "expression",
                "autoOrder"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:sys": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:cfg": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:app": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:dcscor": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:dcsset": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:xr": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:ent": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "name": {
            "allowed_parents_tags": [
                "ViewStatusAddition",
                "UsualGroup",
                "TrackBarField",
                "TextDocumentField",
                "Table",
                "SpreadSheetDocumentField",
                "SearchStringAddition",
                "ProgressBarField",
                "PDFDocumentField",
                "Parameter",
                "Pages",
                "HTMLDocumentField",
                "GraphicalSchemaField",
                "LabelField",
                "PictureDecoration",
                "FormattedDocumentField",
                "SearchControlAddition",
                "Event",
                "PictureField",
                "ContextMenu",
                "Popup",
                "RadioButtonField",
                "Page",
                "CommandBar",
                "InputField",
                "Command",
                "LabelDecoration",
                "CheckBoxField",
                "ExtendedTooltip",
                "ColumnGroup",
                "ChartField",
                "CalendarField",
                "AutoCommandBar",
                "Column",
                "Button",
                "Attribute",
                "app:item",
                "ButtonGroup"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@Name_Имя"
                }
            ],
            "description": "имя"
        },
        "xmlns:lf": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:style": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:v8": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:v8ui": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:xs": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "version": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@String_Строка"
                }
            ],
            "description": "версия"
        },
        "xmlns:web": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:win": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "xmlns:xsi": {
            "allowed_parents_tags": [
                "Form"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@NamespaceUri_ИмяПространстваИмен"
                }
            ],
            "description": "пространство имен"
        },
        "id": {
            "allowed_parents_tags": [
                "ViewStatusAddition",
                "UsualGroup",
                "TrackBarField",
                "TextDocumentField",
                "Table",
                "SpreadSheetDocumentField",
                "SearchStringAddition",
                "ProgressBarField",
                "SearchControlAddition",
                "PictureField",
                "PDFDocumentField",
                "Pages",
                "HTMLDocumentField",
                "PictureDecoration",
                "FormattedDocumentField",
                "GraphicalSchemaField",
                "LabelField",
                "ContextMenu",
                "Popup",
                "RadioButtonField",
                "Page",
                "CommandBar",
                "InputField",
                "Command",
                "LabelDecoration",
                "CheckBoxField",
                "ExtendedTooltip",
                "ColumnGroup",
                "ChartField",
                "CalendarField",
                "ButtonGroup",
                "AutoCommandBar",
                "Column",
                "Button",
                "Attribute"
            ],
            "allowed_values": [
                {
                    "is_common": true,
                    "item": "@ID_Идентификатор"
                }
            ],
            "description": "идентификатор"
        }
    },
    "tags_common_types": null,
    "attributes_common_types": null
}
```
  
**Релевантные примеры XML форм по запросам:**  
*Пример 1: Добавить реквизит "BusinessProcessRef_БизнесПроцессСсылка_Задание" с типом БизнесПроцессСсылка.Задание. Добавить элемент поле ввода для реквизита "BusinessProcessRef_БизнесПроцессСсылка_Задание" с именем "BusinessProcessRef_БизнесПроцессСсылка_Задание".*
```
<?xml version="1.0" encoding="UTF-8"?>
<Form xmlns="http://v8.1c.ru/8.3/xcf/logform" xmlns:app="http://v8.1c.ru/8.2/managed-application/core" xmlns:cfg="http://v8.1c.ru/8.1/data/enterprise/current-config" xmlns:dcscor="http://v8.1c.ru/8.1/data-composition-system/core" xmlns:dcssch="http://v8.1c.ru/8.1/data-composition-system/schema" xmlns:dcsset="http://v8.1c.ru/8.1/data-composition-system/settings" xmlns:ent="http://v8.1c.ru/8.1/data/enterprise" xmlns:lf="http://v8.1c.ru/8.2/managed-application/logform" xmlns:style="http://v8.1c.ru/8.1/data/ui/style" xmlns:sys="http://v8.1c.ru/8.1/data/ui/fonts/system" xmlns:v8="http://v8.1c.ru/8.1/data/core" xmlns:v8ui="http://v8.1c.ru/8.1/data/ui" xmlns:web="http://v8.1c.ru/8.1/data/ui/colors/web" xmlns:win="http://v8.1c.ru/8.1/data/ui/colors/windows" xmlns:xr="http://v8.1c.ru/8.3/xcf/readable" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.20">
<ChildItems>
        <InputField name="BusinessProcessRef_БизнесПроцессСсылка_Задание" id="605">
            <DataPath>BusinessProcessRef_БизнесПроцессСсылка_Задание</DataPath>
            <ExtendedEditMultipleValues>true</ExtendedEditMultipleValues>
            <ContextMenu name="BusinessProcessRef_БизнесПроцессСсылка_ЗаданиеКонтекстноеМеню" id="606"/>
            <ExtendedTooltip name="BusinessProcessRef_БизнесПроцессСсылка_ЗаданиеРасширеннаяПодсказка" id="607"/>
        </InputField>
    </ChildItems>
    <Attributes>
        <Attribute name="BusinessProcessRef_БизнесПроцессСсылка_Задание" id="51">
            <Title>
                <v8:item>
                    <v8:lang>ru</v8:lang>
                    <v8:content>BusinessProcessRef (БизнесПроцессСсылка)</v8:content>
                </v8:item>
            </Title>
            <Type>
                <v8:Type>cfg:BusinessProcessRef.Задание</v8:Type>
            </Type>
        </Attribute>
    </Attributes>
</Form>
```

**Правила форматирования XML: все атрибуты в одной строке, отступ 4 пробела, без лишних переносов строк.**  
**Правило привязки элемнета к реквизиту: `DataPath` **строго** равен `Attribute.name`. Другие варианты запрещены.**  
** Все атрибуты id у тэгов в XML должны быть уникальны.**  