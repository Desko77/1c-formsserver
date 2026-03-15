"""MCP-инструменты поиска примеров форм."""

from __future__ import annotations

from mcp_forms.search.query import search, get_form_code
from mcp_forms.search.indexer import index_form, index_directory


def search_form_examples(
    query: str,
    mode: str = "fts",
    limit: int = 5,
    include_code: bool = False,
) -> dict:
    """Поиск примеров форм по запросу.

    Args:
        query: поисковый запрос (напр. "форма списка документов с отбором по дате")
        mode: режим поиска: "fts" (полнотекстовый), "vector" (по эмбеддингам), "auto"
        limit: максимум результатов
        include_code: включить XML-код формы в результат

    Returns:
        dict с ключами: results, count, mode
    """
    try:
        results = search(query, mode=mode, limit=limit, include_code=include_code)
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "mode": mode,
        }
    except Exception as e:
        return {
            "success": False,
            "results": [],
            "count": 0,
            "mode": mode,
            "error": str(e),
        }


def index_forms_from_directory(directory: str, pattern: str = "**/Form.xml") -> dict:
    """Индексировать Form.xml файлы из директории в базу поиска.

    Args:
        directory: путь к директории с конфигурацией 1С
        pattern: glob-паттерн для поиска файлов Form.xml

    Returns:
        dict со статистикой: indexed, skipped, errors
    """
    try:
        stats = index_directory(directory, pattern)
        return {
            "success": True,
            **stats,
        }
    except Exception as e:
        return {
            "success": False,
            "indexed": 0,
            "skipped": 0,
            "errors": [str(e)],
        }


def get_form_example(form_id: int) -> dict:
    """Получить XML-код формы по id из базы примеров.

    Args:
        form_id: id записи (из результатов search_form_examples)

    Returns:
        dict с ключами: xml, success
    """
    code = get_form_code(form_id)
    if code:
        return {"success": True, "xml": code}
    return {"success": False, "error": f"Форма с id={form_id} не найдена"}
