# 1c-formsserver

MCP-сервер для генерации, валидации, конвертации и поиска управляемых форм 1С:Предприятие.

Поддерживает три формата: **Конфигуратор** (`logform`), **Managed** (`managed`) и **EDT** (`edt`).

## Быстрый старт

### Docker (рекомендуется)

```bash
docker compose up -d
```

Сервер доступен на `http://localhost:8011/mcp`.

### Локально

```bash
pip install -e .
python -m mcp_forms
```

### Подключение к Claude Code

В `settings.json`:

```json
{
  "mcpServers": {
    "1c-forms": {
      "url": "http://localhost:8011/mcp"
    }
  }
}
```

## Форматы форм

Сервер работает с тремя форматами Form.xml / Form.form:

| | Конфигуратор (`logform`) | Managed (`managed`) | EDT (`edt`) |
|---|---|---|---|
| **Файл** | `Form.xml` | `Form.xml` | `Form.form` |
| **Root** | `<Form xmlns="...xcf/logform">` | `<ManagedForm xmlns="...xcf/managed">` | `<form:Form xmlns:form="...dt/form">` |
| **Элементы** | `<InputField name="X" id="1">` | `<InputField><Name>X</Name><Id>1</Id>` | `<items xsi:type="form:FormField"><name>X</name><id>1</id><type>InputField</type>` |
| **DataPath** | `<DataPath>Объект.Поле</DataPath>` | `<DataPath>Объект.Поле</DataPath>` | `<dataPath xsi:type="form:DataPath"><segments>Объект.Поле</segments></dataPath>` |
| **Типы** | `<v8:Type>cfg:CatalogObject.X</v8:Type>` | `<Type>CatalogObject.X</Type>` | `<valueType><types>CatalogObject.X</types></valueType>` |
| **Companion** | `<ContextMenu>` + `<ExtendedTooltip>` | нет | `<contextMenu>` + `<extendedTooltip>` |
| **ExtInfo** | нет | нет | `<extInfo xsi:type="form:InputFieldExtInfo">` |

Формат определяется автоматически по namespace корневого элемента. Конвертация между всеми тремя форматами с сохранением семантики.

## MCP-инструменты (18)

### Генерация форм

**`generate_form_template`** — быстрая генерация типовой формы по шаблону. Лучший выбор для начала.

```
Параметры:
  template: "catalog_element" | "document" | "data_processor"
  object_name: имя объекта ("Номенклатура", "ЗаказКлиента")
  fields: список полей (["Наименование", "Артикул"])
  format: "logform" (по умолчанию) | "managed" | "edt"

  Для document:
    header_fields: поля шапки (["Дата", "Номер", "Контрагент"])
    table_name: имя ТЧ ("Товары")
    table_columns: колонки ТЧ (["Номенклатура", "Количество", "Сумма"])
```

**`generate_form`** — генерация по произвольной JSON-спецификации. Для нестандартных форм.

```
Параметры:
  spec: {
    format: "logform" | "managed" | "edt",
    object_type: "Catalog" | "Document" | "DataProcessor",
    object_name: "Номенклатура",
    title: "Заголовок формы",
    attributes: [
      {name: "Объект", type_name: "CatalogObject.Номенклатура", is_main: true, save_data: true}
    ],
    elements: [
      {name: "Поле", data_path: "Объект.Поле", field_type: "InputField"},
      {name: "Группа", group_type: "UsualGroup", title: "Заголовок", direction: "Vertical",
       children: [{name: "Поле2", data_path: "Объект.Поле2"}]},
      {name: "Таблица", data_path: "Объект.Товары",
       columns: [{name: "Номенклатура", data_path: "Объект.Товары.Номенклатура"}]}
    ]
  }
```

**`generate_form_from_metadata`** — автогенерация на основе метаданных из EDT. Самый быстрый способ при наличии EDT.

```
Параметры:
  object_type: "Catalog" | "Document" | "DataProcessor"
  object_name: имя объекта
  format: "logform" | "managed" | "edt"
  include_table_parts: true | false (включать ТЧ, по умолчанию true)
```

**`list_form_templates`** — список доступных шаблонов с описанием параметров.

### Валидация

**`validate_form`** — проверка Form.xml / Form.form на ошибки. Вызывать после каждой генерации.

```
Параметры:
  xml_content: содержимое файла формы

Проверки:
  - logform: уникальность id, companion-элементы (ContextMenu, ExtendedTooltip),
             имена атрибутов, привязка DataPath → Attribute
  - edt: xsi:type у items, уникальность id (раздельно для items/attributes/commands),
          dataPath/segments, структура attributes
  - managed: базовая проверка структуры
```

**`get_form_info`** — быстрый обзор формы: формат, количество элементов, атрибутов, структура.

**`validate_form_edt`** — расширенная валидация: встроенные проверки + проверки EDT (если EDT доступен).

```
Параметры:
  xml_content: содержимое формы
  form_fqn: FQN формы в EDT (напр. "Catalog.Номенклатура.Form.ФормаЭлемента"), опционально
```

### Конвертация

**`convert_form`** — конвертация между форматами.

```
Параметры:
  xml_content: исходный XML
  target_format: "logform" | "managed" | "edt"

Маршруты:
  logform ↔ managed — напрямую
  logform ↔ edt    — напрямую
  managed ↔ edt    — через промежуточный logform
```

При конвертации:
- Companion-элементы добавляются/преобразуются автоматически
- DataPath конвертируется между форматами (точечная нотация ↔ segments)
- Типы: `cfg:` prefix добавляется/удаляется автоматически
- Структура элементов: теги ↔ items/xsi:type

### Схема и справка

**`get_form_prompt`** — полная база знаний по Form.xml: теги, атрибуты, допустимые значения. **Обязательно вызвать перед первой генерацией** в сессии — без этого LLM не знает допустимые теги.

**`get_form_schema`** — JSON-справочник элементов формы с описанием свойств.

**`get_xcore_model_info`** — метамодель EDT из Xcore: классы (FormField, FormGroup, Table, Button, Decoration), перечисления, свойства.

### Поиск примеров

**`search_form_examples`** — поиск форм в базе знаний по тексту (FTS) или вектору (embeddings).

```
Параметры:
  query: поисковый запрос ("форма справочника с таблицей")
  object_type: фильтр по типу ("Catalog", "Document")
  limit: количество результатов (по умолчанию 5)
```

**`index_forms`** — индексация Form.xml из директории конфигурации в базу поиска.

```
Параметры:
  directory: путь к конфигурации (напр. "/path/to/src")
  pattern: глоб-паттерн (по умолчанию "**/Form.xml")
```

**`get_form_example`** — загрузить полный XML примера по id из результатов поиска.

### EDT интеграция

Требует запущенный [EDT MCP](https://github.com/DitriXNew/EDT-MCP) сервер (`EDT_ENABLED=true`).

**`edt_status`** — проверить доступность EDT. Вызвать перед другими EDT-инструментами.

**`get_object_metadata`** — получить реквизиты и табличные части объекта из проекта EDT.

```
Параметры:
  object_type: "Catalog" | "Document" | "DataProcessor" и др.
  object_name: "Номенклатура"
```

**`form_screenshot`** — PNG-скриншот формы из WYSIWYG-редактора EDT.

```
Параметры:
  form_fqn: "Catalog.Номенклатура.Form.ФормаЭлемента"
```

### Информация

**`get_server_info`** — версия сервера, список инструментов, поддерживаемые форматы.

## Типовые сценарии

### Создать форму для EDT-проекта

```
1. get_form_prompt                    → загрузить базу знаний
2. generate_form_template             → template="catalog_element", object_name="Товары",
                                        fields=["Наименование","Артикул","Цена"], format="edt"
3. validate_form                      → проверить результат
4. Сохранить как Form.form в EDT-проект
```

### Создать форму из метаданных EDT

```
1. edt_status                         → проверить доступность
2. get_object_metadata                → object_type="Document", object_name="ЗаказКлиента"
3. generate_form_from_metadata        → format="edt", include_table_parts=true
4. validate_form_edt                  → расширенная валидация
```

### Конвертировать форму Конфигуратора в EDT

```
1. convert_form                       → xml_content=<Form...>, target_format="edt"
2. validate_form                      → проверить результат
3. Сохранить как Form.form
```

### Найти пример и создать похожую форму

```
1. search_form_examples               → query="документ с табличной частью товары"
2. get_form_example                   → form_id из результатов
3. Использовать пример как образец для generate_form
```

## Конфигурация

Через переменные окружения или `.env` файл:

| Переменная | По умолчанию | Описание |
|-----------|-------------|----------|
| `PORT` | `8011` | Порт сервера |
| `TRANSPORT` | `streamable-http` | Транспорт MCP (streamable-http, sse) |
| `DATABASES_PATH` | `./databases` | Путь к базам данных поиска |
| `DATA_PATH` | `./data` | Путь к данным (схемы, промпт) |
| `EDT_ENABLED` | `false` | Включить интеграцию с [EDT MCP](https://github.com/DitriXNew/EDT-MCP) |
| `EDT_MCP_URL` | `http://localhost:9999/sse` | URL EDT MCP сервера |
| `EDT_TIMEOUT` | `10` | Таймаут запросов к EDT (сек) |

Полный список — в `.env.example`.

## Структура проекта

```
src/mcp_forms/
├── server.py           # FastMCP сервер (18 инструментов)
├── config.py           # Конфигурация из env vars
├── edt_client.py       # Клиент EDT MCP (https://github.com/DitriXNew/EDT-MCP)
├── schema/             # Парсер Xcore, Pydantic-модель, валидатор
├── forms/              # Загрузчик, генератор, конвертер, шаблоны
│   ├── loader.py       # Автоопределение формата, загрузка XML
│   ├── generator.py    # Генерация logform / managed / edt
│   ├── converter.py    # Конвертация между форматами
│   └── templates.py    # Шаблоны (catalog, document, data_processor)
├── search/             # Индексатор, эмбеддинги, FTS + vector поиск
└── tools/              # MCP-инструменты (validate, generate, convert, search, edt)
```

## Зависимости

**Core:** fastmcp, lxml, pydantic, python-dotenv, uvicorn

**Search (опционально):**
```bash
pip install -e ".[search]"
```
Добавляет sentence-transformers для векторного поиска примеров форм.

## Тесты

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

91 тест: валидация (logform, managed, edt), конвертация (roundtrip между всеми форматами), генерация, шаблоны, поиск, EDT интеграция.

## Лицензия

MIT
