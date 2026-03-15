"""Индексация Form.xml файлов в SQLite."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from mcp_forms.forms.loader import detect_format, load_form, NS_LOGFORM, NS_MANAGED
from mcp_forms.config import FORMS_KNOWLEDGE_DB


def _init_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Создать/открыть SQLite БД и обеспечить схему."""
    db_path = db_path or FORMS_KNOWLEDGE_DB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL DEFAULT '',
            form_code TEXT NOT NULL,
            form_type TEXT NOT NULL DEFAULT '',
            object_type TEXT NOT NULL DEFAULT '',
            object_name TEXT NOT NULL DEFAULT '',
            form_name TEXT NOT NULL DEFAULT '',
            source_path TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT ''
        )
    """)
    # Полнотекстовый индекс для SQLite FTS
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS forms_fts USING fts5(
            description, form_type, object_type, object_name, form_name,
            content='forms',
            content_rowid='id'
        )
    """)
    conn.commit()
    return conn


def _rebuild_fts(conn: sqlite3.Connection) -> None:
    """Перестроить FTS-индекс из основной таблицы."""
    conn.execute("DELETE FROM forms_fts")
    conn.execute("""
        INSERT INTO forms_fts(rowid, description, form_type, object_type, object_name, form_name)
        SELECT id, description, form_type, object_type, object_name, form_name
        FROM forms
    """)
    conn.commit()


def _extract_form_metadata(xml_content: str) -> dict:
    """Извлечь метаданные из Form.xml для индексации."""
    fmt = detect_format(xml_content)
    if fmt == "unknown":
        return {"format": "unknown"}

    doc = load_form(xml_content)
    ns = doc.namespace
    root = doc.root

    result = {"format": fmt}

    if fmt == "logform":
        # Атрибуты: ищем MainAttribute для определения типа объекта
        attrs = root.findall(".//{%s}Attribute" % ns)
        for attr in attrs:
            main = attr.find("{%s}MainAttribute" % ns)
            if main is None:
                main = attr.find("MainAttribute")
            if main is not None and main.text == "true":
                type_el = attr.find("{%s}Type" % ns)
                if type_el is None:
                    type_el = attr.find("Type")
                if type_el is not None:
                    ns_v8 = "http://v8.1c.ru/8.1/data/core"
                    v8_type = type_el.find("{%s}Type" % ns_v8)
                    if v8_type is not None and v8_type.text:
                        result["main_type"] = v8_type.text
                break

        # Элементы
        elements = root.findall(".//{%s}ChildItems/*" % ns)
        element_types = set()
        for el in elements:
            tag = el.tag
            if tag.startswith("{"):
                tag = tag.split("}", 1)[1]
            if tag not in ("ContextMenu", "ExtendedTooltip", "AutoCommandBar"):
                element_types.add(tag)
        result["element_types"] = sorted(element_types)
        result["element_count"] = len(elements)

    elif fmt == "managed":
        # Атрибуты
        attrs = root.findall(".//{%s}Attribute" % ns)
        for attr in attrs:
            name_el = attr.find("{%s}Name" % ns)
            if name_el is None:
                name_el = attr.find("Name")
            vt = attr.find("{%s}ValueType" % ns)
            if vt is None:
                vt = attr.find("ValueType")
            if vt is not None:
                t = vt.find("{%s}Type" % ns)
                if t is None:
                    t = vt.find("Type")
                if t is not None and t.text:
                    result["main_type"] = t.text
                    break

        elements = root.findall(".//{%s}Elements/*" % ns)
        element_types = set()
        for el in elements:
            tag = el.tag
            if tag.startswith("{"):
                tag = tag.split("}", 1)[1]
            element_types.add(tag)
        result["element_types"] = sorted(element_types)
        result["element_count"] = len(elements)

    return result


def _generate_description(
    form_name: str,
    object_type: str,
    object_name: str,
    form_type: str,
    metadata: dict,
) -> str:
    """Сгенерировать текстовое описание формы для поиска."""
    parts = []

    if form_type:
        parts.append(form_type)
    if object_type and object_name:
        parts.append(f"для {object_type}.{object_name}")
    elif object_name:
        parts.append(f"для {object_name}")

    main_type = metadata.get("main_type", "")
    if main_type:
        parts.append(f"({main_type})")

    el_types = metadata.get("element_types", [])
    if el_types:
        parts.append(f"Элементы: {', '.join(el_types)}")

    el_count = metadata.get("element_count", 0)
    if el_count:
        parts.append(f"({el_count} элементов)")

    return ". ".join(parts) if parts else form_name


def index_form(
    xml_content: str,
    form_name: str = "",
    object_type: str = "",
    object_name: str = "",
    form_type: str = "",
    source_path: str = "",
    db_path: Path | None = None,
) -> int:
    """Добавить Form.xml в индекс поиска.

    Args:
        xml_content: содержимое Form.xml
        form_name: имя формы (ФормаЭлемента, ФормаСписка...)
        object_type: тип объекта (Catalog, Document...)
        object_name: имя объекта (Номенклатура, ПоступлениеТоваров...)
        form_type: тип формы (ФормаЭлемента, ФормаДокумента...)
        source_path: путь к исходному файлу
        db_path: путь к SQLite (по умолчанию из config)

    Returns:
        id добавленной записи
    """
    metadata = _extract_form_metadata(xml_content)
    description = _generate_description(form_name, object_type, object_name, form_type, metadata)

    conn = _init_db(db_path)
    try:
        cur = conn.execute(
            """INSERT INTO forms (description, form_code, form_type, object_type, object_name,
                form_name, source_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                description,
                xml_content,
                form_type,
                object_type,
                object_name,
                form_name,
                source_path,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        row_id = cur.lastrowid

        # Обновить FTS
        conn.execute(
            "INSERT INTO forms_fts(rowid, description, form_type, object_type, object_name, form_name) VALUES (?, ?, ?, ?, ?, ?)",
            (row_id, description, form_type, object_type, object_name, form_name),
        )
        conn.commit()
        return row_id
    finally:
        conn.close()


def index_directory(
    directory: str | Path,
    pattern: str = "**/Form.xml",
    db_path: Path | None = None,
) -> dict:
    """Индексировать все Form.xml из директории.

    Args:
        directory: корневая директория для поиска
        pattern: glob-паттерн для поиска файлов
        db_path: путь к SQLite

    Returns:
        dict со статистикой: indexed, skipped, errors
    """
    directory = Path(directory)
    stats = {"indexed": 0, "skipped": 0, "errors": []}

    for form_path in directory.glob(pattern):
        try:
            xml_content = form_path.read_text(encoding="utf-8")
            fmt = detect_format(xml_content)
            if fmt == "unknown":
                stats["skipped"] += 1
                continue

            # Извлекаем информацию из пути
            parts = form_path.parts
            object_type = ""
            object_name = ""
            form_name = form_path.parent.name if form_path.parent.name != "Ext" else form_path.parent.parent.name

            # Попробуем определить тип по структуре пути (EDT / Конфигуратор)
            for i, part in enumerate(parts):
                if part in ("Catalogs", "Catalog"):
                    object_type = "Catalog"
                    if i + 1 < len(parts):
                        object_name = parts[i + 1]
                elif part in ("Documents", "Document"):
                    object_type = "Document"
                    if i + 1 < len(parts):
                        object_name = parts[i + 1]
                elif part in ("DataProcessors", "DataProcessor"):
                    object_type = "DataProcessor"
                    if i + 1 < len(parts):
                        object_name = parts[i + 1]
                elif part in ("Reports", "Report"):
                    object_type = "Report"
                    if i + 1 < len(parts):
                        object_name = parts[i + 1]

            index_form(
                xml_content=xml_content,
                form_name=form_name,
                object_type=object_type,
                object_name=object_name,
                form_type=form_name,
                source_path=str(form_path),
                db_path=db_path,
            )
            stats["indexed"] += 1
        except Exception as e:
            stats["errors"].append({"path": str(form_path), "error": str(e)})

    return stats
