"""Интеграционные тесты контейнера — вызов всех 18 MCP-инструментов через HTTP."""

import json
import time
import sys

import requests

MCP_URL = "http://localhost:8011/mcp"

# Тестовая форма logform
LOGFORM_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<Form xmlns="http://v8.1c.ru/8.3/xcf/logform" xmlns:v8="http://v8.1c.ru/8.1/data/core" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xr="http://v8.1c.ru/8.3/xcf/readable" xmlns:cfg="http://v8.1c.ru/8.1/data/enterprise/current-config" xmlns:app="http://v8.1c.ru/8.2/managed-application/core" xmlns:dcscor="http://v8.1c.ru/8.1/data-composition-system/core" xmlns:dcssch="http://v8.1c.ru/8.1/data-composition-system/schema" xmlns:dcsset="http://v8.1c.ru/8.1/data-composition-system/settings" xmlns:ent="http://v8.1c.ru/8.1/data/enterprise" xmlns:lf="http://v8.1c.ru/8.2/managed-application/logform" xmlns:style="http://v8.1c.ru/8.1/data/ui/style" xmlns:sys="http://v8.1c.ru/8.1/data/ui/fonts/system" xmlns:v8ui="http://v8.1c.ru/8.1/data/ui" xmlns:web="http://v8.1c.ru/8.1/data/ui/colors/web" xmlns:win="http://v8.1c.ru/8.1/data/ui/colors/windows" version="2.16">
  <AutoCommandBar name="" id="-1"/>
  <ChildItems>
    <InputField name="Поле1" id="1">
      <DataPath>Объект.Поле1</DataPath>
      <ContextMenu name="Поле1КонтекстноеМеню" id="2"/>
      <ExtendedTooltip name="Поле1РасширеннаяПодсказка" id="3"/>
    </InputField>
  </ChildItems>
  <Attributes>
    <Attribute name="Объект" id="0">
      <Type><v8:Type>cfg:CatalogObject.Тест</v8:Type></Type>
    </Attribute>
  </Attributes>
</Form>'''

MANAGED_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<ManagedForm xmlns="http://v8.1c.ru/8.3/xcf/managed"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xmlns:xs="http://www.w3.org/2001/XMLSchema"
             xmlns:xr="http://v8.1c.ru/8.3/xcf/readable">
  <AutoTitle>true</AutoTitle>
  <Attributes>
    <Attribute>
      <Name>Объект</Name>
      <Id>0</Id>
      <ValueType><Type>CatalogObject.Тест</Type></ValueType>
    </Attribute>
  </Attributes>
  <Elements>
    <InputField>
      <Name>Поле1</Name>
      <Id>1</Id>
      <DataPath>Объект.Поле1</DataPath>
    </InputField>
  </Elements>
</ManagedForm>'''


def mcp_call(session_id, method, params=None, call_id=1):
    """Вызвать MCP метод."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": call_id,
    }
    if params:
        payload["params"] = params

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id

    resp = requests.post(MCP_URL, json=payload, headers=headers, timeout=30, proxies={"http": None, "https": None})
    new_session = resp.headers.get("Mcp-Session-Id") or session_id
    body = resp.text

    # Парсим SSE формат
    for line in body.split("\n"):
        if line.startswith("data: "):
            return new_session, json.loads(line[6:])

    return new_session, json.loads(body)


def call_tool(session_id, tool_name, arguments=None):
    """Вызвать MCP-инструмент."""
    session_id, result = mcp_call(session_id, "tools/call", {
        "name": tool_name,
        "arguments": arguments or {},
    })

    content = result.get("result", {}).get("content", [])
    is_error = result.get("result", {}).get("isError", False)

    text = ""
    for item in content:
        if item.get("type") == "text":
            text = item["text"]
            break

    return session_id, text, is_error


def main():
    print("Waiting for server...")
    time.sleep(2)

    # Initialize
    session_id, resp = mcp_call(None, "initialize", {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"},
    })
    print(f"Session: {session_id}")
    print(f"Server: {resp['result']['serverInfo']['name']}\n")

    # Все 18 инструментов
    tests = [
        ("get_server_info", {}),
        ("validate_form", {"xml_content": LOGFORM_XML}),
        ("get_form_info", {"xml_content": LOGFORM_XML}),
        ("get_form_schema", {}),
        ("get_form_prompt", {}),
        ("get_xcore_model_info", {}),
        ("generate_form", {"spec": {
            "format": "logform",
            "attributes": [{"name": "Объект", "type_name": "cfg:CatalogObject.Тест", "is_main": True}],
            "elements": [{"name": "Поле", "data_path": "Объект.Поле", "field_type": "InputField"}],
        }}),
        ("generate_form_template", {
            "template": "catalog_element",
            "object_name": "Тест",
            "fields": ["Поле1", "Поле2"],
            "format": "logform",
        }),
        ("list_form_templates", {}),
        ("convert_form", {"xml_content": LOGFORM_XML, "target_format": "managed"}),
        ("convert_form", {"xml_content": MANAGED_XML, "target_format": "logform"}),
        ("search_form_examples", {"query": "Catalog", "mode": "fts", "limit": 3}),
        ("get_form_example", {"form_id": 1}),
        ("edt_status", {}),
        ("get_object_metadata", {"object_type": "Catalog", "object_name": "Тест"}),
        ("validate_form_edt", {"xml_content": LOGFORM_XML}),
        ("form_screenshot", {"form_fqn": "Catalog.Тест.Form.Форма"}),
        ("generate_form_from_metadata", {"object_type": "Catalog", "object_name": "Тест"}),
    ]

    passed = 0
    failed = 0

    for tool_name, args in tests:
        try:
            session_id, text, is_error = call_tool(session_id, tool_name, args)

            if is_error:
                print(f"  FAIL  {tool_name}: {text[:120]}")
                failed += 1
            else:
                try:
                    data = json.loads(text)
                    preview = str(data)[:80]
                except (json.JSONDecodeError, TypeError):
                    preview = text[:80] if text else "(empty)"
                print(f"  OK    {tool_name}: {preview}")
                passed += 1
        except Exception as e:
            print(f"  FAIL  {tool_name}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed, {passed + failed} total")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
