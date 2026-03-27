## Дополнение контекста
**Ты эксперт по программированию управляемых форм 1С в формате EDT (Form.form).**
**Формат EDT использует namespace `http://g5.1c.ru/v8/dt/form` и принципиально отличается от logform/managed.**
**Ниже ОПИСАНИЕ БАЗЫ ЗНАНИЙ в формате JSON по созданию и валидации EDT-форм 1С:**
```
{
    "namespaces": {
        "form": {
            "uri": "http://g5.1c.ru/v8/dt/form",
            "description": "Основной namespace. Root-элемент: <form:Form>. Дочерние элементы БЕЗ prefix: <items>, <name>, <id> и т.д.",
            "usage": "Prefix form: только на root-элементе <form:Form>. Все дочерние элементы записываются БЕЗ prefix. Пример: <items>, НЕ <form:items>. Оба варианта технически валидны, но EDT создаёт без prefix."
        },
        "xsi": {
            "uri": "http://www.w3.org/2001/XMLSchema-instance",
            "description": "Для атрибута xsi:type — типизация элементов",
            "usage": "Атрибут xsi:type на items, dataPath, extInfo. Пример: <items xsi:type=\"form:FormField\">"
        },
        "core": {
            "uri": "http://g5.1c.ru/v8/dt/mcore",
            "description": "Базовые типы ядра (TypeDescription, StringQualifiers и т.д.)",
            "usage": "Используется для xsi:type сложных типов значений. Обычно не нужен для простых форм."
        }
    },
    "root_element": {
        "tag": "form:Form",
        "description": "Корневой элемент EDT-формы. Файл Form.form.",
        "xml_declaration": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "opening_tag": "<form:Form xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:core=\"http://g5.1c.ru/v8/dt/mcore\" xmlns:form=\"http://g5.1c.ru/v8/dt/form\">",
        "children_order": ["items", "autoCommandBar", "autoTitle", "autoUrl", "group", "autoFillCheck", "enabled", "showTitle", "showCloseButton", "attributes", "formCommands", "parameters", "commandInterface"],
        "properties": {
            "autoTitle": { "type": "boolean", "default": "true", "description": "Автозаголовок формы" },
            "autoUrl": { "type": "boolean", "default": "true", "description": "Автоматический URL" },
            "group": { "type": "FormChildrenGroup", "default": "Vertical", "description": "Расположение дочерних элементов формы" },
            "autoFillCheck": { "type": "boolean", "default": "true", "description": "Автоматическая проверка заполнения" },
            "enabled": { "type": "boolean", "default": "true", "description": "Доступность формы" },
            "showTitle": { "type": "boolean", "default": "true", "description": "Показывать заголовок" },
            "showCloseButton": { "type": "boolean", "default": "true", "description": "Показывать кнопку закрытия" },
            "width": { "type": "int", "description": "Ширина формы" },
            "height": { "type": "int", "description": "Высота формы" }
        }
    },
    "item_types": {
        "description": "Все элементы формы — дочерние <items> root-элемента с атрибутом xsi:type",
        "FormField": {
            "xsi_type": "form:FormField",
            "description": "Поле ввода/отображения данных (InputField, CheckBoxField, LabelField и др.)",
            "children_order": ["name", "id", "visible", "enabled", "userVisible", "dataPath", "extendedTooltip", "contextMenu", "type", "editMode", "showInHeader", "headerHorizontalAlign", "showInFooter", "extInfo"],
            "required_children": ["name", "id", "type", "extendedTooltip", "contextMenu", "extInfo"],
            "properties": {
                "name": { "type": "string", "description": "Имя элемента (уникальное)" },
                "id": { "type": "int", "description": "Уникальный ID элемента (scope: items)" },
                "visible": { "type": "boolean", "default": "true" },
                "enabled": { "type": "boolean", "default": "true" },
                "userVisible": { "type": "struct", "description": "Содержит <common>true</common>" },
                "dataPath": { "type": "form:DataPath", "description": "Привязка к данным. Требует xsi:type=\"form:DataPath\". Внутри: <segments>Объект.Поле</segments>" },
                "type": { "type": "ManagedFormFieldType", "description": "Тип поля: InputField, CheckBoxField, LabelField, RadioButtonField и др." },
                "editMode": { "type": "TableFieldEditMode", "description": "Режим редактирования (для колонок таблиц): Enter, Directly, EnterOnInput" },
                "showInHeader": { "type": "boolean", "description": "Показывать в заголовке (для колонок таблиц)" },
                "headerHorizontalAlign": { "type": "ItemHorizontalAlignment", "description": "Выравнивание заголовка (для колонок таблиц)" },
                "showInFooter": { "type": "boolean", "description": "Показывать в подвале (для колонок таблиц)" },
                "title": { "type": "localized_string", "description": "Заголовок элемента. Структура: <title><key>ru</key><value>Текст</value></title>" },
                "titleLocation": { "type": "FormElementTitleLocation", "description": "Расположение заголовка: Auto, None, Left, Top, Right, Bottom" },
                "toolTip": { "type": "localized_string", "description": "Подсказка элемента" },
                "toolTipRepresentation": { "type": "TooltipRepresentation" },
                "horizontalStretch": { "type": "Boolean" },
                "verticalStretch": { "type": "Boolean" },
                "width": { "type": "int" },
                "height": { "type": "int" },
                "autoMaxWidth": { "type": "boolean" },
                "autoMaxHeight": { "type": "boolean" },
                "skipOnInput": { "type": "boolean" },
                "readOnly": { "type": "boolean" }
            }
        },
        "FormGroup": {
            "xsi_type": "form:FormGroup",
            "description": "Группа элементов (UsualGroup, Pages, Page, ColumnGroup, CommandBar, Popup)",
            "children_order": ["name", "id", "items (дочерние)", "visible", "enabled", "userVisible", "title", "extendedTooltip", "type", "extInfo"],
            "required_children": ["name", "id", "type", "extendedTooltip", "extInfo"],
            "note": "Дочерние items вставляются ПЕРЕД visible/enabled/title",
            "properties": {
                "name": { "type": "string", "description": "Имя группы (уникальное)" },
                "id": { "type": "int", "description": "Уникальный ID" },
                "type": { "type": "ManagedFormGroupType", "description": "Тип группы: UsualGroup, Pages, Page, ColumnGroup, CommandBar, Popup" },
                "visible": { "type": "boolean", "default": "true" },
                "enabled": { "type": "boolean", "default": "true" },
                "userVisible": { "type": "struct" },
                "title": { "type": "localized_string" },
                "items": { "type": "nested", "description": "Вложенные элементы формы (FormField, FormGroup, Table, Button)" }
            }
        },
        "Table": {
            "xsi_type": "form:Table",
            "description": "Таблица формы (табличная часть, динамический список)",
            "children_order": ["name", "id", "dataPath", "autoCommandBar", "items (колонки)", "visible", "enabled", "userVisible", "extendedTooltip", "contextMenu", "searchStringAddition", "viewStatusAddition", "extInfo"],
            "required_children": ["name", "id", "autoCommandBar", "extendedTooltip", "contextMenu", "searchStringAddition", "viewStatusAddition"],
            "properties": {
                "name": { "type": "string" },
                "id": { "type": "int" },
                "dataPath": { "type": "form:DataPath", "description": "Привязка: <segments>Объект.ТабличнаяЧасть</segments>" },
                "autoCommandBar": { "type": "struct", "description": "Командная панель таблицы. Содержит name, id, autoFill" },
                "items": { "type": "nested", "description": "Колонки таблицы — FormField с editMode, showInHeader, showInFooter" }
            }
        },
        "Button": {
            "xsi_type": "form:Button",
            "description": "Кнопка формы",
            "required_children": ["name", "id", "extendedTooltip", "contextMenu"],
            "properties": {
                "name": { "type": "string" },
                "id": { "type": "int" },
                "type": { "type": "ManagedFormButtonType", "description": "Тип кнопки: UsualButton (вне CommandBar), CommandBarButton (в CommandBar, дефолт)" },
                "visible": { "type": "boolean" },
                "enabled": { "type": "boolean" },
                "commandName": { "type": "string", "description": "Имя команды: Form.Command.ИмяКоманды" },
                "representation": { "type": "ButtonRepresentation", "description": "Представление кнопки" },
                "defaultButton": { "type": "boolean", "description": "Кнопка по умолчанию" }
            }
        },
        "Decoration": {
            "xsi_type": "form:Decoration",
            "description": "Декорация — надпись или картинка",
            "properties": {
                "name": { "type": "string" },
                "id": { "type": "int" },
                "type": { "type": "ManagedFormDecorationType", "description": "Label или Picture" },
                "title": { "type": "localized_string", "description": "Текст надписи (для Label)" },
                "extInfo": { "type": "form:LabelDecorationExtInfo или form:PictureDecorationExtInfo" }
            }
        }
    },
    "companion_elements": {
        "description": "Обязательные сопровождающие элементы. КАЖДЫЙ FormField, FormGroup, Table, Button ДОЛЖЕН содержать extendedTooltip и contextMenu.",
        "extendedTooltip": {
            "description": "Расширенная подсказка. Обязательна для всех items.",
            "naming": "Имя = ИмяЭлемента + 'РасширеннаяПодсказка'",
            "structure": "<extendedTooltip>\n  <name>ПолеРасширеннаяПодсказка</name>\n  <id>UNIQUE_ID</id>\n  <type>Label</type>\n  <autoMaxWidth>true</autoMaxWidth>\n  <autoMaxHeight>true</autoMaxHeight>\n  <extInfo xsi:type=\"form:LabelDecorationExtInfo\">\n    <horizontalAlign>Left</horizontalAlign>\n  </extInfo>\n</extendedTooltip>"
        },
        "contextMenu": {
            "description": "Контекстное меню. Обязательно для FormField, Table, Button.",
            "naming": "Имя = ИмяЭлемента + 'КонтекстноеМеню'",
            "structure": "<contextMenu>\n  <name>ПолеКонтекстноеМеню</name>\n  <id>UNIQUE_ID</id>\n  <autoFill>true</autoFill>\n</contextMenu>"
        },
        "autoCommandBar": {
            "description": "Командная панель. Обязательна для Table и для корня формы.",
            "naming_root": "ФормаКоманднаяПанель (id=-1)",
            "naming_table": "ИмяТаблицы + 'КоманднаяПанель'",
            "structure": "<autoCommandBar>\n  <name>ИмяКоманднаяПанель</name>\n  <id>UNIQUE_ID</id>\n  <autoFill>true</autoFill>\n</autoCommandBar>"
        },
        "searchStringAddition": {
            "description": "Строка поиска. Обязательна для Table.",
            "naming": "ИмяТаблицы + 'СтрокаПоиска'",
            "structure": "<searchStringAddition>\n  <name>ТаблицаСтрокаПоиска</name>\n  <id>UNIQUE_ID</id>\n  <type>SearchStringAddition</type>\n  <extInfo xsi:type=\"form:SearchStringAdditionExtInfo\">\n    <autoMaxWidth>true</autoMaxWidth>\n  </extInfo>\n</searchStringAddition>"
        },
        "viewStatusAddition": {
            "description": "Состояние просмотра. Обязательно для Table.",
            "naming": "ИмяТаблицы + 'СостояниеПросмотра'",
            "structure": "<viewStatusAddition>\n  <name>ТаблицаСостояниеПросмотра</name>\n  <id>UNIQUE_ID</id>\n  <type>ViewStatusAddition</type>\n  <extInfo xsi:type=\"form:ViewStatusAdditionExtInfo\">\n    <autoMaxWidth>true</autoMaxWidth>\n  </extInfo>\n</viewStatusAddition>"
        }
    },
    "ext_info_types": {
        "description": "Каждый элемент формы имеет extInfo с типом через xsi:type. Тип extInfo зависит от типа элемента.",
        "field_type_mapping": {
            "InputField": "form:InputFieldExtInfo",
            "LabelField": "form:LabelFieldExtInfo",
            "CheckBoxField": "form:CheckBoxFieldExtInfo",
            "RadioButtonField": "form:RadioButtonsFieldExtInfo",
            "ImageField": "form:ImageFieldExtInfo",
            "SpreadSheetDocumentField": "form:SpreadSheetDocFieldExtInfo",
            "CalendarField": "form:CalendarFieldExtInfo",
            "TrackBarField": "form:TrackBarFieldExtInfo",
            "ProgressBarField": "form:ProgressBarFieldExtInfo"
        },
        "group_type_mapping": {
            "UsualGroup": "form:UsualGroupExtInfo",
            "Pages": "form:PagesGroupExtInfo",
            "Page": "form:PageGroupExtInfo",
            "ColumnGroup": "form:ColumnGroupExtInfo",
            "CommandBar": "form:CommandBarExtInfo",
            "Popup": "form:PopupGroupExtInfo"
        },
        "InputFieldExtInfo": {
            "description": "Расширение для полей ввода (InputField)",
            "common_properties": {
                "autoMaxWidth": { "type": "boolean", "default": "true" },
                "autoMaxHeight": { "type": "boolean", "default": "true" },
                "wrap": { "type": "boolean", "description": "Перенос текста" },
                "chooseType": { "type": "boolean", "description": "Выбор типа (для составных типов)" },
                "typeDomainEnabled": { "type": "boolean", "description": "Включение домена типов" },
                "textEdit": { "type": "boolean", "description": "Текстовое редактирование" },
                "multiLine": { "type": "Boolean", "description": "Многострочный ввод" },
                "passwordMode": { "type": "Boolean", "description": "Режим пароля" },
                "choiceButton": { "type": "Boolean", "description": "Кнопка выбора" },
                "clearButton": { "type": "Boolean", "description": "Кнопка очистки" },
                "spinButton": { "type": "Boolean", "description": "Кнопка прокрутки (для чисел)" },
                "openButton": { "type": "Boolean", "description": "Кнопка открытия" },
                "dropListButton": { "type": "Boolean", "description": "Кнопка выпадающего списка" },
                "mask": { "type": "string", "description": "Маска ввода" },
                "format": { "type": "localized_string", "description": "Формат отображения" },
                "editFormat": { "type": "localized_string", "description": "Формат редактирования" }
            }
        },
        "LabelFieldExtInfo": {
            "description": "Расширение для полей-надписей (LabelField)",
            "common_properties": {
                "autoMaxWidth": { "type": "boolean", "default": "true" },
                "autoMaxHeight": { "type": "boolean", "default": "true" },
                "hyperlink": { "type": "boolean", "description": "Гиперссылка" },
                "format": { "type": "localized_string" }
            }
        },
        "CheckBoxFieldExtInfo": {
            "description": "Расширение для чекбоксов (CheckBoxField)",
            "common_properties": {
                "checkBoxType": { "type": "CheckBoxKind", "description": "Вид: Auto, CheckBox, Tumbler, Switcher" },
                "threeState": { "type": "boolean", "description": "Трёхпозиционный" }
            }
        },
        "RadioButtonsFieldExtInfo": {
            "description": "Расширение для переключателей (RadioButtonField)",
            "common_properties": {
                "radioButtonsType": { "type": "RadioButtonType", "description": "Вид: Auto, RadioButtons, Tumbler" },
                "columnsCount": { "type": "int", "description": "Количество колонок" },
                "choiceList": { "type": "array", "description": "Список значений выбора" }
            }
        },
        "UsualGroupExtInfo": {
            "description": "Расширение для обычных групп (UsualGroup)",
            "common_properties": {
                "group": { "type": "FormChildrenGroup", "description": "Расположение: Vertical, HorizontalIfPossible, AlwaysHorizontal" },
                "representation": { "type": "UsualGroupRepresentation", "description": "Представление: None, StrongSeparation, WeakSeparation, NormalSeparation" },
                "showLeftMargin": { "type": "boolean", "default": "true" },
                "united": { "type": "boolean", "default": "true" },
                "throughAlign": { "type": "UsualGroupThroughAlign", "description": "Сквозное выравнивание: Auto, Use, DontUse" },
                "currentRowUse": { "type": "CurrentRowUse", "description": "Использование текущей строки: Auto, DontUse, Auto" },
                "behavior": { "type": "UsualGroupBehavior", "description": "Поведение: Usual, Collapsible, PopUp" },
                "collapsed": { "type": "boolean", "description": "Свёрнута (для Collapsible)" }
            }
        },
        "PageGroupExtInfo": {
            "description": "Расширение для страниц (Page)",
            "common_properties": {
                "group": { "type": "FormChildrenGroup" },
                "showTitle": { "type": "boolean" }
            }
        },
        "PagesGroupExtInfo": {
            "description": "Расширение для контейнера страниц (Pages)",
            "common_properties": {
                "pagesRepresentation": { "type": "FormPagesRepresentation" }
            }
        },
        "ColumnGroupExtInfo": {
            "description": "Расширение для колоночных групп (ColumnGroup)",
            "common_properties": {
                "group": { "type": "FormChildrenGroup" }
            }
        },
        "CommandBarExtInfo": {
            "description": "Расширение для командных панелей (CommandBar)",
            "common_properties": {
                "horizontalAlign": { "type": "ItemHorizontalAlignment" }
            }
        },
        "LabelDecorationExtInfo": {
            "description": "Расширение для текстовых декораций (Label)",
            "common_properties": {
                "horizontalAlign": { "type": "ItemHorizontalAlignment", "default": "Left" },
                "verticalAlign": { "type": "ItemVerticalAlignment" },
                "hyperlink": { "type": "boolean" }
            }
        },
        "PictureDecorationExtInfo": {
            "description": "Расширение для декораций-картинок (Picture)",
            "common_properties": {
                "pictureSize": { "type": "PictureSize" },
                "hyperlink": { "type": "boolean" },
                "zoomable": { "type": "boolean" }
            }
        },
        "SearchStringAdditionExtInfo": {
            "description": "Расширение для строки поиска (таблица)",
            "common_properties": {
                "autoMaxWidth": { "type": "boolean", "default": "true" }
            }
        },
        "ViewStatusAdditionExtInfo": {
            "description": "Расширение для состояния просмотра (таблица)",
            "common_properties": {
                "autoMaxWidth": { "type": "boolean", "default": "true" }
            }
        }
    },
    "handlers_placement": {
        "description": "Обработчики событий (handlers) размещаются на ДВУХ уровнях. FormField и FieldExtInfo оба имеют <handlers>. Правильное размещение критично.",
        "extInfo_handlers": {
            "description": "Обработчики в <extInfo><handlers>. Для событий, связанных с ВВОДОМ и ВЫБОРОМ значения.",
            "events": ["StartChoice", "Clearing", "Opening", "ChoiceProcessing", "AutoComplete", "TextEditEnd"]
        },
        "element_handlers": {
            "description": "Обработчики на уровне элемента <items><handlers>. Для событий, связанных с ИЗМЕНЕНИЕМ и ПЕРЕТАСКИВАНИЕМ.",
            "events": ["OnChange", "DragStart", "DragEnd", "DragOver", "DragAndDropDone"]
        },
        "format": "<handlers>\n  <event>EventName</event>\n  <name>ИмяПроцедурыОбработчика</name>\n</handlers>"
    },
    "attributes_structure": {
        "description": "Реквизиты формы. Корневые <attributes> элементы формы.",
        "children_order": ["name", "title", "id", "valueType", "view", "edit", "main", "savedData", "columns"],
        "properties": {
            "name": { "type": "string", "description": "Имя реквизита" },
            "title": { "type": "localized_string", "description": "Заголовок реквизита (опционально)" },
            "id": { "type": "int", "description": "Уникальный ID (scope: attributes, начинается с 0 для главного реквизита)" },
            "valueType": { "type": "struct", "description": "Тип значения. Содержит <types>ТипДанных</types>" },
            "view": { "type": "struct", "description": "Просмотр. Содержит <common>true</common>" },
            "edit": { "type": "struct", "description": "Редактирование. Содержит <common>true</common>" },
            "main": { "type": "boolean", "description": "Основной реквизит формы (обычно один — Объект)" },
            "savedData": { "type": "boolean", "description": "Сохраняемые данные (обычно для главного реквизита)" },
            "columns": { "type": "array", "description": "Колонки реквизита-таблицы (для табличных частей)" }
        },
        "type_names": {
            "description": "Типы в <types> записываются БЕЗ prefix. Простые типы: Boolean, Number, String, Date.",
            "examples": [
                "CatalogObject.Номенклатура",
                "CatalogRef.Контрагенты",
                "DocumentObject.ПоступлениеТоваров",
                "DocumentRef.РеализацияТоваров",
                "EnumRef.ВидыОпераций",
                "Boolean",
                "Number",
                "String",
                "Date"
            ],
            "xs_to_edt_mapping": {
                "xs:boolean": "Boolean",
                "xs:decimal": "Number",
                "xs:integer": "Number",
                "xs:string": "String",
                "xs:dateTime": "Date",
                "xs:float": "Number"
            }
        }
    },
    "commands_structure": {
        "description": "Команды формы. Корневые <formCommands> элементы формы.",
        "properties": {
            "name": { "type": "string", "description": "Имя команды" },
            "id": { "type": "int", "description": "Уникальный ID (scope: formCommands, отдельный от items и attributes)" },
            "title": { "type": "localized_string" },
            "action": { "type": "struct", "description": "Обработчик команды" },
            "representation": { "type": "DefaultRepresentation" },
            "modifiesStoredData": { "type": "boolean" }
        }
    },
    "enums": {
        "ManagedFormFieldType": ["InputField", "CheckBoxField", "LabelField", "RadioButtonField", "ImageField", "SpreadsheetDocumentField", "TextDocumentField", "HTMLDocumentField", "CalendarField", "ChartField", "PlannerField", "DendrogramField", "ProgressBarField", "TrackBarField", "FormattedDocumentField", "GeographicalSchemaField", "GraphicalSchemaField", "GanttChartField", "PeriodField", "PDFDocumentField"],
        "ManagedFormGroupType": ["UsualGroup", "Pages", "Page", "ColumnGroup", "CommandBar", "Popup", "ButtonGroup", "ContextMenu", "AutoCommandBar"],
        "ManagedFormDecorationType": ["Label", "Picture"],
        "FormChildrenGroup": ["Vertical", "HorizontalIfPossible", "AlwaysHorizontal", "Auto"],
        "ItemHorizontalAlignment": ["Auto", "Left", "Center", "Right"],
        "ItemVerticalAlignment": ["Auto", "Top", "Center", "Bottom"],
        "FormElementTitleLocation": ["Auto", "None", "Left", "Top", "Right", "Bottom"],
        "UsualGroupRepresentation": ["None", "StrongSeparation", "WeakSeparation", "NormalSeparation"],
        "UsualGroupBehavior": ["Usual", "Collapsible", "PopUp"],
        "TableFieldEditMode": ["Directly", "Enter", "EnterOnInput"],
        "CheckBoxKind": ["Auto", "CheckBox", "Tumbler", "Switcher"],
        "RadioButtonType": ["Auto", "RadioButtons", "Tumbler"],
        "TooltipRepresentation": ["Auto", "None", "Balloon", "Button"],
        "ButtonRepresentation": ["Auto", "PictureAndText", "Text", "Picture", "Hyperlink"],
        "FormButtonRepresentation": ["Auto", "PictureAndText", "Text", "Picture"],
        "TableRepresentation": ["List", "HierarchicalList", "Tree"],
        "TableSelectionMode": ["SingleRow", "MultiRow"],
        "LogFormScrollMode": ["Auto", "Use", "UseIfNecessary", "UseWithoutStretch"],
        "ManagedFormButtonType": ["CommandBarButton", "UsualButton"]
    },
    "id_rules": {
        "description": "В EDT три отдельных пространства ID. ID должны быть уникальны ВНУТРИ своего пространства.",
        "items": {
            "description": "Все items (поля, группы, таблицы, кнопки, companion-элементы). Начинаются с 1. autoCommandBar корня формы = -1.",
            "scope": "Все items, включая extendedTooltip, contextMenu, autoCommandBar таблиц, searchStringAddition, viewStatusAddition"
        },
        "attributes": {
            "description": "Реквизиты формы. Главный реквизит (main=true) обычно id=0. Остальные — с 1 и далее.",
            "scope": "Только <attributes> элементы"
        },
        "formCommands": {
            "description": "Команды формы. Начинаются с 1.",
            "scope": "Только <formCommands> элементы"
        }
    },
    "common_patterns": {
        "dataPath": {
            "description": "Привязка элемента к данным реквизита",
            "rule": "Значение segments СТРОГО равно Attribute.name или Attribute.name.Поле (через точку). Один segment = полный путь.",
            "xml": "<dataPath xsi:type=\"form:DataPath\">\n  <segments>Объект.Наименование</segments>\n</dataPath>",
            "table_columns": "Для колонок таблицы: <segments>Объект.ТабличнаяЧасть.Колонка</segments>"
        },
        "title": {
            "description": "Локализованный заголовок",
            "xml": "<title>\n  <key>ru</key>\n  <value>Текст заголовка</value>\n</title>"
        },
        "userVisible": {
            "description": "Пользовательская видимость",
            "xml": "<userVisible>\n  <common>true</common>\n</userVisible>"
        },
        "valueType": {
            "description": "Тип значения реквизита",
            "xml": "<valueType>\n  <types>CatalogObject.Номенклатура</types>\n</valueType>",
            "multiple_types": "<valueType>\n  <types>CatalogRef.Контрагенты</types>\n  <types>CatalogRef.ФизическиеЛица</types>\n</valueType>"
        }
    }
}
```

**Ключевые правила EDT-формата:**

1. **Namespace**: root-элемент `<form:Form xmlns:form="..." xmlns:xsi="..." xmlns:core="...">`. Дочерние элементы записываются БЕЗ prefix `form:`. Пример: `<items>`, а НЕ `<form:items>`.

2. **Типизация**: каждый `<items>` обязан иметь `xsi:type`: `form:FormField`, `form:FormGroup`, `form:Table`, `form:Button`, `form:Decoration`.

3. **extInfo обязателен**: каждый FormField и FormGroup должен иметь `<extInfo xsi:type="form:XXXExtInfo">`. Тип определяется по `<type>` элемента (см. field_type_mapping и group_type_mapping).

4. **Companion-элементы обязательны**: `extendedTooltip` для всех items; `contextMenu` для FormField, Table, Button; `autoCommandBar` для Table и root.

5. **ID уникальны в своём scope**: items (с 1, кроме root autoCommandBar = -1), attributes (с 0), formCommands (с 1).

6. **DataPath**: `<dataPath xsi:type="form:DataPath"><segments>Объект.Поле</segments></dataPath>`. Segments — полный путь через точку в одном элементе.

7. **Типы без prefix**: `<types>CatalogObject.Номенклатура</types>` (не `cfg:CatalogObject`).

8. **Порядок дочерних элементов root**: items → autoCommandBar → свойства формы (autoTitle, autoUrl, group...) → attributes → formCommands.

9. **Все атрибуты id у элементов в XML должны быть уникальны внутри своего scope.**

10. **Правила форматирования XML**: отступ 2 пробела, все xsi:type атрибуты в открывающем теге.

**ПРИМЕР ПОЛНОЙ EDT-ФОРМЫ (форма элемента справочника):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<form:Form xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:core="http://g5.1c.ru/v8/dt/mcore" xmlns:form="http://g5.1c.ru/v8/dt/form">
  <items xsi:type="form:FormField">
    <name>Наименование</name>
    <id>1</id>
    <visible>true</visible>
    <enabled>true</enabled>
    <userVisible>
      <common>true</common>
    </userVisible>
    <dataPath xsi:type="form:DataPath">
      <segments>Объект.Наименование</segments>
    </dataPath>
    <extendedTooltip>
      <name>НаименованиеРасширеннаяПодсказка</name>
      <id>2</id>
      <type>Label</type>
      <autoMaxWidth>true</autoMaxWidth>
      <autoMaxHeight>true</autoMaxHeight>
      <extInfo xsi:type="form:LabelDecorationExtInfo">
        <horizontalAlign>Left</horizontalAlign>
      </extInfo>
    </extendedTooltip>
    <contextMenu>
      <name>НаименованиеКонтекстноеМеню</name>
      <id>3</id>
      <autoFill>true</autoFill>
    </contextMenu>
    <type>InputField</type>
    <extInfo xsi:type="form:InputFieldExtInfo">
      <autoMaxWidth>true</autoMaxWidth>
      <autoMaxHeight>true</autoMaxHeight>
      <chooseType>true</chooseType>
      <typeDomainEnabled>true</typeDomainEnabled>
      <textEdit>true</textEdit>
    </extInfo>
  </items>
  <items xsi:type="form:FormField">
    <name>Код</name>
    <id>4</id>
    <visible>true</visible>
    <enabled>true</enabled>
    <userVisible>
      <common>true</common>
    </userVisible>
    <dataPath xsi:type="form:DataPath">
      <segments>Объект.Код</segments>
    </dataPath>
    <extendedTooltip>
      <name>КодРасширеннаяПодсказка</name>
      <id>5</id>
      <type>Label</type>
      <autoMaxWidth>true</autoMaxWidth>
      <autoMaxHeight>true</autoMaxHeight>
      <extInfo xsi:type="form:LabelDecorationExtInfo">
        <horizontalAlign>Left</horizontalAlign>
      </extInfo>
    </extendedTooltip>
    <contextMenu>
      <name>КодКонтекстноеМеню</name>
      <id>6</id>
      <autoFill>true</autoFill>
    </contextMenu>
    <type>InputField</type>
    <extInfo xsi:type="form:InputFieldExtInfo">
      <autoMaxWidth>true</autoMaxWidth>
      <autoMaxHeight>true</autoMaxHeight>
      <chooseType>true</chooseType>
      <typeDomainEnabled>true</typeDomainEnabled>
      <textEdit>true</textEdit>
    </extInfo>
  </items>
  <items xsi:type="form:FormGroup">
    <name>ГруппаОсновная</name>
    <id>7</id>
    <items xsi:type="form:FormField">
      <name>Артикул</name>
      <id>8</id>
      <visible>true</visible>
      <enabled>true</enabled>
      <userVisible>
        <common>true</common>
      </userVisible>
      <dataPath xsi:type="form:DataPath">
        <segments>Объект.Артикул</segments>
      </dataPath>
      <extendedTooltip>
        <name>АртикулРасширеннаяПодсказка</name>
        <id>9</id>
        <type>Label</type>
        <autoMaxWidth>true</autoMaxWidth>
        <autoMaxHeight>true</autoMaxHeight>
        <extInfo xsi:type="form:LabelDecorationExtInfo">
          <horizontalAlign>Left</horizontalAlign>
        </extInfo>
      </extendedTooltip>
      <contextMenu>
        <name>АртикулКонтекстноеМеню</name>
        <id>10</id>
        <autoFill>true</autoFill>
      </contextMenu>
      <type>InputField</type>
      <extInfo xsi:type="form:InputFieldExtInfo">
        <autoMaxWidth>true</autoMaxWidth>
        <autoMaxHeight>true</autoMaxHeight>
      </extInfo>
    </items>
    <visible>true</visible>
    <enabled>true</enabled>
    <userVisible>
      <common>true</common>
    </userVisible>
    <title>
      <key>ru</key>
      <value>Основная</value>
    </title>
    <extendedTooltip>
      <name>ГруппаОсновнаяРасширеннаяПодсказка</name>
      <id>11</id>
      <type>Label</type>
      <autoMaxWidth>true</autoMaxWidth>
      <autoMaxHeight>true</autoMaxHeight>
      <extInfo xsi:type="form:LabelDecorationExtInfo">
        <horizontalAlign>Left</horizontalAlign>
      </extInfo>
    </extendedTooltip>
    <type>UsualGroup</type>
    <extInfo xsi:type="form:UsualGroupExtInfo">
      <representation>None</representation>
      <showLeftMargin>true</showLeftMargin>
      <united>true</united>
      <throughAlign>Auto</throughAlign>
      <currentRowUse>Auto</currentRowUse>
    </extInfo>
  </items>
  <autoCommandBar>
    <name>ФормаКоманднаяПанель</name>
    <id>-1</id>
    <autoFill>true</autoFill>
  </autoCommandBar>
  <autoTitle>true</autoTitle>
  <autoUrl>true</autoUrl>
  <group>Vertical</group>
  <autoFillCheck>true</autoFillCheck>
  <enabled>true</enabled>
  <showTitle>true</showTitle>
  <showCloseButton>true</showCloseButton>
  <attributes>
    <name>Объект</name>
    <id>0</id>
    <valueType>
      <types>CatalogObject.Номенклатура</types>
    </valueType>
    <view>
      <common>true</common>
    </view>
    <edit>
      <common>true</common>
    </edit>
    <main>true</main>
    <savedData>true</savedData>
  </attributes>
</form:Form>
```

**ПРИМЕР ТАБЛИЦЫ В EDT-ФОРМЕ:**
```xml
  <items xsi:type="form:Table">
    <name>Товары</name>
    <id>20</id>
    <dataPath xsi:type="form:DataPath">
      <segments>Объект.Товары</segments>
    </dataPath>
    <autoCommandBar>
      <name>ТоварыКоманднаяПанель</name>
      <id>21</id>
      <autoFill>true</autoFill>
    </autoCommandBar>
    <items xsi:type="form:FormField">
      <name>ТоварыНоменклатура</name>
      <id>22</id>
      <dataPath xsi:type="form:DataPath">
        <segments>Объект.Товары.Номенклатура</segments>
      </dataPath>
      <extendedTooltip>
        <name>ТоварыНоменклатураРасширеннаяПодсказка</name>
        <id>23</id>
        <type>Label</type>
        <autoMaxWidth>true</autoMaxWidth>
        <autoMaxHeight>true</autoMaxHeight>
        <extInfo xsi:type="form:LabelDecorationExtInfo">
          <horizontalAlign>Left</horizontalAlign>
        </extInfo>
      </extendedTooltip>
      <contextMenu>
        <name>ТоварыНоменклатураКонтекстноеМеню</name>
        <id>24</id>
        <autoFill>true</autoFill>
      </contextMenu>
      <type>InputField</type>
      <editMode>Enter</editMode>
      <showInHeader>true</showInHeader>
      <headerHorizontalAlign>Left</headerHorizontalAlign>
      <showInFooter>true</showInFooter>
      <extInfo xsi:type="form:InputFieldExtInfo">
        <autoMaxWidth>true</autoMaxWidth>
        <autoMaxHeight>true</autoMaxHeight>
        <chooseType>true</chooseType>
        <typeDomainEnabled>true</typeDomainEnabled>
        <textEdit>true</textEdit>
      </extInfo>
    </items>
    <items xsi:type="form:FormField">
      <name>ТоварыКоличество</name>
      <id>25</id>
      <dataPath xsi:type="form:DataPath">
        <segments>Объект.Товары.Количество</segments>
      </dataPath>
      <extendedTooltip>
        <name>ТоварыКоличествоРасширеннаяПодсказка</name>
        <id>26</id>
        <type>Label</type>
        <autoMaxWidth>true</autoMaxWidth>
        <autoMaxHeight>true</autoMaxHeight>
        <extInfo xsi:type="form:LabelDecorationExtInfo">
          <horizontalAlign>Left</horizontalAlign>
        </extInfo>
      </extendedTooltip>
      <contextMenu>
        <name>ТоварыКоличествоКонтекстноеМеню</name>
        <id>27</id>
        <autoFill>true</autoFill>
      </contextMenu>
      <type>InputField</type>
      <editMode>Enter</editMode>
      <showInHeader>true</showInHeader>
      <headerHorizontalAlign>Left</headerHorizontalAlign>
      <showInFooter>true</showInFooter>
      <extInfo xsi:type="form:InputFieldExtInfo">
        <autoMaxWidth>true</autoMaxWidth>
        <autoMaxHeight>true</autoMaxHeight>
      </extInfo>
    </items>
    <visible>true</visible>
    <enabled>true</enabled>
    <userVisible>
      <common>true</common>
    </userVisible>
    <extendedTooltip>
      <name>ТоварыРасширеннаяПодсказка</name>
      <id>28</id>
      <type>Label</type>
      <autoMaxWidth>true</autoMaxWidth>
      <autoMaxHeight>true</autoMaxHeight>
      <extInfo xsi:type="form:LabelDecorationExtInfo">
        <horizontalAlign>Left</horizontalAlign>
      </extInfo>
    </extendedTooltip>
    <contextMenu>
      <name>ТоварыКонтекстноеМеню</name>
      <id>29</id>
      <autoFill>true</autoFill>
    </contextMenu>
    <searchStringAddition>
      <name>ТоварыСтрокаПоиска</name>
      <id>30</id>
      <type>SearchStringAddition</type>
      <extInfo xsi:type="form:SearchStringAdditionExtInfo">
        <autoMaxWidth>true</autoMaxWidth>
      </extInfo>
    </searchStringAddition>
    <viewStatusAddition>
      <name>ТоварыСостояниеПросмотра</name>
      <id>31</id>
      <type>ViewStatusAddition</type>
      <extInfo xsi:type="form:ViewStatusAdditionExtInfo">
        <autoMaxWidth>true</autoMaxWidth>
      </extInfo>
    </viewStatusAddition>
  </items>
```
