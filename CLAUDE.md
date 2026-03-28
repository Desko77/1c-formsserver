# 1c-formsserver

MCP-сервер для работы с управляемыми формами 1С (Form.xml / Form.form).

## DONE: EDT-дефолты и валидация (реализовано)

Трехслойная защита от пропуска EDT-свойств агентом. Дополнено 2026-03-28: маппинг типов Object, стрип v8:, дефолты таблиц (16 свойств), 3 новых правила MANDATORY-чеклиста (типы, autoCommandBar, view/edit).

### 1. get_form_prompt - добавить MANDATORY-чеклист в начало промпта

В самом начале ответа (ДО JSON, ДО примеров) добавить короткий императивный блок. Короткие правила в начале имеют больший "вес" для агента, чем свойства на 200-й строке JSON.

```
**MANDATORY - НИКОГДА НЕ ПРОПУСКАТЬ:**

1. Каждый InputField -> extInfo ОБЯЗАН содержать:
   chooseType, typeDomainEnabled, textEdit (даже если true по умолчанию)

2. Каждый FormField в таблице -> ОБЯЗАН содержать:
   editMode (EnterOnInput), showInHeader (true),
   headerHorizontalAlign (Left), showInFooter (true)

3. Handlers InputField - РАЗМЕЩЕНИЕ:
   - В <extInfo> (как <handlers>): StartChoice, Clearing, Opening,
     ChoiceProcessing, AutoComplete, TextEditEnd
   - На уровне элемента (<Events>): OnChange, Drag*

4. Button вне CommandBar -> type ОБЯЗАН быть UsualButton
   Button в CommandBar -> type = CommandBarButton (дефолт, можно не указывать)

5. Имя кнопки = имя команды (НЕ "Кнопка" + имя, НЕ имя + "Кнопка")

6. НЕ добавлять containedObjects с classId вручную - EDT добавляет сам

7. НЕ дублировать title, если он совпадает с именем реквизита - платформа подставит автоматически

8. Предпочитать встроенную кнопку выбора (choiceButton + StartChoice)
   вместо отдельной кнопки рядом с полем
```

**Файл:** `src/mcp_forms/server.py`, тулза `get_form_prompt`.
**Где вставить:** в начало строки result, перед `## Дополнение контекста`.

### 2. generate_form - автоматические EDT-дефолты

При генерации формы сервер должен гарантированно добавлять дефолтные свойства, даже если пользователь их не указал.

**InputFieldExtInfo** - всегда добавлять:
- `autoMaxWidth: true`
- `autoMaxHeight: true`
- `chooseType: true`
- `typeDomainEnabled: true`
- `textEdit: true`

**FormField внутри Table** (колонки) - всегда добавлять:
- `editMode: EnterOnInput`
- `showInHeader: true`
- `headerHorizontalAlign: Left`
- `showInFooter: true`

**Все FormField** - всегда добавлять:
- `visible: true`
- `enabled: true`
- `userVisible: { common: true }`

**Button вне CommandBar** - автоматически `type: UsualButton`.

**Файл:** `src/mcp_forms/forms/generator.py`.

### 3. validate_form - warnings для пропущенных дефолтов

Добавить soft-warnings (severity: warning, не error) для:

- [ ] InputFieldExtInfo без `chooseType` / `typeDomainEnabled` / `textEdit`
- [ ] FormField в таблице без `editMode` / `showInHeader` / `showInFooter`
- [ ] Button без `<type>` вне CommandBar
- [ ] Handler `StartChoice` в `<Events>` элемента вместо `<handlers>` в extInfo
- [ ] `containedObjects` с нестандартным `classId`

Warnings не блокируют генерацию, но агент увидит их и исправит.

**Файл:** `src/mcp_forms/schema/validator.py`.

### 4. generate_form_from_metadata - те же дефолты что в п.2

Генерация из метаданных EDT должна включать те же автоматические дефолты.

**Файл:** `src/mcp_forms/server.py`, тулза `generate_form_from_metadata`.

### Приоритет реализации

1. **get_form_prompt** (п.1) - максимальный эффект, минимальные изменения (вставить текст в начало)
2. **validate_form** (п.3) - ловит ошибки независимо от способа генерации
3. **generate_form** (п.2) - гарантирует корректность при использовании генератора
4. **generate_form_from_metadata** (п.4) - аналогично п.2

### Контекст проблемы

Xcore-модель (`edt_reference/Form.xcore`) содержит все эти свойства:
- `chooseType` (строка 988), `typeDomainEnabled` (строка 990), `textEdit` (строка 991) - в `InputFieldExtInfo`
- `wrap` (строка 958) - в `InputFieldExtInfo`
- `editMode` (строка 905), `showInHeader` (строка 909), `headerHorizontalAlign` (строка 911) - в `FormField`
- `userVisible` (строка 107) - в `FormVisualEntity` (AdjustableBoolean)
- `placementArea` у Button (строка 715) - `transient`, НЕ сериализуется (EDT вычисляет сам)
- Handlers: `EventHandlerContainer` - interface и у `FormField`, и у `FieldExtInfo` (оба содержат handlers)

Модель Python (`src/mcp_forms/schema/model.py`) должна уже содержать эти свойства из парсинга Xcore. Проверить соответствие.
