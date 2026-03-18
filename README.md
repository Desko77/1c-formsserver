# 1c-formsserver

MCP-сервер для генерации, валидации, конвертации и поиска управляемых форм 1С (Form.xml).

Поддерживает оба формата: **EDT** (`xcf/managed`) и **Конфигуратор** (`xcf/logform`).

## Возможности

- **Валидация** — структурная проверка Form.xml (уникальность id, обязательные элементы, привязка DataPath)
- **Генерация** — создание Form.xml по JSON-спецификации или из шаблонов (справочник, документ, обработка)
- **Конвертация** — двунаправленная EDT ↔ Конфигуратор с roundtrip-сохранением семантики
- **Поиск** — полнотекстовый (FTS5) и векторный (sentence-transformers) поиск по базе примеров
- **EDT интеграция** — метаданные объектов, скриншоты форм, валидация через EDT MCP

## MCP-инструменты (18)

| Категория | Инструменты |
|-----------|------------|
| Валидация | `validate_form`, `get_form_info`, `validate_form_edt` |
| Схема | `get_form_schema`, `get_form_prompt`, `get_xcore_model_info` |
| Генерация | `generate_form`, `generate_form_template`, `list_form_templates`, `generate_form_from_metadata` |
| Конвертация | `convert_form` |
| Поиск | `search_form_examples`, `index_forms`, `get_form_example` |
| EDT | `edt_status`, `get_object_metadata`, `form_screenshot` |
| Инфо | `get_server_info` |

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

```json
{
  "mcpServers": {
    "1c-forms": {
      "url": "http://localhost:8011/mcp"
    }
  }
}
```

## Форматы Form.xml

| | Конфигуратор (logform) | EDT (managed) |
|---|---|---|
| Root | `<Form>` | `<ManagedForm>` |
| Namespace | `xcf/logform` | `xcf/managed` |
| Namespaces | 17 | 4 |
| Идентификация | `name`/`id` атрибуты | `<Name>`/`<Id>` элементы |
| Companion-элементы | ContextMenu + ExtendedTooltip | нет |

Формат определяется автоматически. Конвертация сохраняет семантику при roundtrip.

## Конфигурация

Через переменные окружения или `.env` файл:

| Переменная | По умолчанию | Описание |
|-----------|-------------|----------|
| `PORT` | `8011` | Порт сервера |
| `TRANSPORT` | `streamable-http` | Транспорт MCP (streamable-http, sse) |
| `DATABASES_PATH` | `./databases` | Путь к базам данных |
| `DATA_PATH` | `./data` | Путь к данным (схемы, промпт) |
| `EDT_ENABLED` | `false` | Включить интеграцию с EDT MCP |
| `EDT_MCP_URL` | `http://localhost:9999/sse` | URL EDT MCP сервера |
| `EDT_TIMEOUT` | `10` | Таймаут запросов к EDT (сек) |

Полный список — в `.env.example`.

## Структура проекта

```
src/mcp_forms/
├── server.py           # FastMCP сервер (18 инструментов)
├── config.py           # Конфигурация из env vars
├── edt_client.py       # Клиент EDT MCP (graceful degradation)
├── schema/             # Парсер Xcore, Pydantic-модель, валидатор
├── forms/              # Загрузчик, генератор, конвертер, шаблоны
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

70 тестов: валидация, конвертация (roundtrip), поиск, EDT интеграция.

## Лицензия

MIT
