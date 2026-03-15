"""Поиск примеров форм по запросу.

Поддерживает два режима:
1. FTS (SQLite Full-Text Search) — всегда доступен
2. Векторный поиск (sentence-transformers + cosine similarity) — если установлен
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from mcp_forms.config import FORMS_KNOWLEDGE_DB
from mcp_forms.search.indexer import _init_db


def _has_fts_table(conn: sqlite3.Connection) -> bool:
    """Проверить наличие FTS-таблицы."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='forms_fts'"
    )
    return cur.fetchone() is not None


def search_fts(
    query: str,
    limit: int = 5,
    db_path: Path | None = None,
) -> list[dict]:
    """Полнотекстовый поиск по SQLite FTS5.

    Args:
        query: поисковый запрос
        limit: максимум результатов
        db_path: путь к SQLite

    Returns:
        список результатов с ключами: id, description, form_type, object_type,
        object_name, form_name, source_path, score
    """
    conn = _init_db(db_path)
    try:
        if not _has_fts_table(conn):
            return _search_like(conn, query, limit)

        # FTS5 поиск с ранжированием
        cur = conn.execute(
            """SELECT f.id, f.description, f.form_type, f.object_type,
                      f.object_name, f.form_name, f.source_path,
                      rank AS score
               FROM forms_fts fts
               JOIN forms f ON f.id = fts.rowid
               WHERE forms_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, limit),
        )
        return [dict(row) for row in cur.fetchall()]
    except sqlite3.OperationalError:
        # FTS-запрос невалидный — fallback на LIKE
        return _search_like(conn, query, limit)
    finally:
        conn.close()


def _search_like(
    conn: sqlite3.Connection,
    query: str,
    limit: int,
) -> list[dict]:
    """Fallback поиск через LIKE."""
    pattern = f"%{query}%"
    cur = conn.execute(
        """SELECT id, description, form_type, object_type, object_name,
                  form_name, source_path, 0.0 AS score
           FROM forms
           WHERE description LIKE ?
              OR form_type LIKE ?
              OR object_type LIKE ?
              OR object_name LIKE ?
              OR form_name LIKE ?
           LIMIT ?""",
        (pattern, pattern, pattern, pattern, pattern, limit),
    )
    return [dict(row) for row in cur.fetchall()]


def search_vector(
    query: str,
    limit: int = 5,
    db_path: Path | None = None,
    model_name: str | None = None,
) -> list[dict]:
    """Векторный поиск через эмбеддинги (cosine similarity).

    Требует: sentence-transformers.

    Args:
        query: поисковый запрос на естественном языке
        limit: максимум результатов
        db_path: путь к SQLite
        model_name: модель для эмбеддингов

    Returns:
        список результатов с ключами: id, description, form_type, object_type,
        object_name, form_name, source_path, score
    """
    from mcp_forms.search.embeddings import encode_single

    query_embedding = encode_single(query, model_name)

    conn = _init_db(db_path)
    try:
        # Загружаем все описания
        cur = conn.execute(
            "SELECT id, description, form_type, object_type, object_name, form_name, source_path FROM forms"
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    # Кодируем описания
    from mcp_forms.search.embeddings import encode

    descriptions = [row["description"] for row in rows]
    doc_embeddings = encode(descriptions, model_name)

    # Cosine similarity
    scored = []
    for row, doc_emb in zip(rows, doc_embeddings):
        score = _cosine_similarity(query_embedding, doc_emb)
        scored.append({
            "id": row["id"],
            "description": row["description"],
            "form_type": row["form_type"],
            "object_type": row["object_type"],
            "object_name": row["object_name"],
            "form_name": row["form_name"],
            "source_path": row["source_path"],
            "score": round(score, 4),
        })

    # Сортировка по убыванию score
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity между двумя векторами."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def get_form_code(form_id: int, db_path: Path | None = None) -> str | None:
    """Получить XML-код формы по id.

    Args:
        form_id: id записи в базе
        db_path: путь к SQLite

    Returns:
        XML-код формы или None
    """
    db_path = db_path or FORMS_KNOWLEDGE_DB
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute("SELECT form_code FROM forms WHERE id = ?", (form_id,))
        row = cur.fetchone()
        return row["form_code"] if row else None
    finally:
        conn.close()


def search(
    query: str,
    mode: str = "fts",
    limit: int = 5,
    db_path: Path | None = None,
    include_code: bool = False,
) -> list[dict]:
    """Универсальный поиск форм.

    Args:
        query: поисковый запрос
        mode: "fts" (полнотекстовый), "vector" (векторный), "auto" (vector если доступен, иначе fts)
        limit: максимум результатов
        db_path: путь к SQLite
        include_code: включить XML-код формы в результат

    Returns:
        список результатов
    """
    if mode == "auto":
        from mcp_forms.search.embeddings import is_available
        mode = "vector" if is_available() else "fts"

    if mode == "vector":
        results = search_vector(query, limit, db_path)
    else:
        results = search_fts(query, limit, db_path)

    if include_code:
        for r in results:
            r["form_code"] = get_form_code(r["id"], db_path) or ""

    return results
