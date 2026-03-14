# 1c-formsserver

MCP-сервер для генерации, валидации и поиска управляемых форм 1С (Form.xml).

Поддерживает оба формата: **EDT** (`xcf/managed`) и **Конфигуратор** (`xcf/logform`).

## Возможности

- **Валидация Form.xml** — уникальность id, обязательные элементы, привязка DataPath к атрибутам
- **Генерация форм** — по JSON-спецификации или из типовых шаблонов (справочник, документ, обработка)
- **Информация о форме** — структура, типы элементов, атрибуты
- **Схема формы** — JSON-схема элементов и промпт для LLM
- **Xcore-модель** — парсинг Form.xcore из EDT 2025.2 (127 классов, 127 перечислений)

## MCP-инструменты

| Инструмент | Описание |
|-----------|----------|
| `validate_form` | Валидация Form.xml (автоопределение формата) |
| `get_form_info` | Структура формы: элементы, атрибуты, команды |
| `generate_form` | Генерация Form.xml по JSON-спецификации |
| `generate_form_template` | Генерация из шаблона (catalog_element, document, data_processor) |
| `list_form_templates` | Список доступных шаблонов |
| `get_form_schema` | JSON-схема элементов формы |
| `get_form_prompt` | Промпт с базой знаний для LLM |
| `get_xcore_model_info` | Информация о Xcore-модели форм |
| `get_server_info` | Информация о сервере |

## Быстрый старт

### Локально

```bash
pip install -e .
python -m mcp_forms
```

Сервер запустится на `http://0.0.0.0:8011/sse`

### Docker

```bash
docker build -t 1c-formsserver .
docker run -p 8011:8011 1c-formsserver
```

### Docker Compose

```bash
docker compose up -d
```

## Конфигурация

Через переменные окружения (или `.env` файл):

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `PORT` | Порт сервера | `8011` |
| `TRANSPORT` | Транспорт MCP (`sse` / `streamable-http`) | `sse` |
| `DATABASES_PATH` | Путь к базам данных | `./databases` |
| `DATA_PATH` | Путь к данным (схемы, промпт) | `./data` |

## Подключение к Claude Code

```json
{
  "mcpServers": {
    "1c-forms": {
      "url": "http://localhost:8011/sse"
    }
  }
}
```

## Форматы Form.xml

| | Конфигуратор (logform) | EDT (managed) |
|---|---|---|
| Namespace | `xcf/logform` | `xcf/managed` |
| Root | `<Form>` | `<ManagedForm>` |
| Namespaces | 17 | 4 |

Формат определяется автоматически по root element и namespace.

## Структура проекта

```
src/mcp_forms/
├── server.py           # FastMCP сервер
├── config.py           # Конфигурация
├── schema/             # Парсер Xcore, модель, валидатор
├── forms/              # Загрузчик, генератор, шаблоны
├── search/             # Поиск примеров (в разработке)
└── tools/              # MCP-инструменты
```

## Лицензия

MIT
