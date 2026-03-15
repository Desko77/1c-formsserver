"""Тесты модуля поиска примеров форм."""

from pathlib import Path
import sqlite3
import tempfile

import pytest

from mcp_forms.search.indexer import index_form, index_directory, _init_db, _rebuild_fts
from mcp_forms.search.query import search_fts, search, get_form_code

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_db(tmp_path):
    """Временная SQLite БД для тестов."""
    return tmp_path / "test_forms.db"


@pytest.fixture
def populated_db(temp_db):
    """БД с проиндексированными тестовыми формами."""
    catalog_xml = (FIXTURES / "logform_catalog_element.xml").read_text(encoding="utf-8")
    document_xml = (FIXTURES / "logform_document.xml").read_text(encoding="utf-8")
    managed_xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")

    index_form(
        xml_content=catalog_xml,
        form_name="ФормаЭлемента",
        object_type="Catalog",
        object_name="Номенклатура",
        form_type="ФормаЭлемента",
        db_path=temp_db,
    )
    index_form(
        xml_content=document_xml,
        form_name="ФормаДокумента",
        object_type="Document",
        object_name="РТУ",
        form_type="ФормаДокумента",
        db_path=temp_db,
    )
    index_form(
        xml_content=managed_xml,
        form_name="Форма",
        object_type="Catalog",
        object_name="Контрагенты",
        form_type="ФормаЭлемента",
        db_path=temp_db,
    )
    return temp_db


class TestIndexer:
    """Тесты индексации."""

    def test_index_form(self, temp_db):
        """Индексация одной формы."""
        xml = (FIXTURES / "logform_catalog_element.xml").read_text(encoding="utf-8")
        row_id = index_form(
            xml_content=xml,
            form_name="ФормаЭлемента",
            object_type="Catalog",
            object_name="Номенклатура",
            db_path=temp_db,
        )
        assert row_id > 0

    def test_index_creates_db(self, tmp_path):
        """Индексация создаёт БД если не существует."""
        db_path = tmp_path / "subdir" / "new.db"
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        row_id = index_form(xml_content=xml, form_name="Test", db_path=db_path)
        assert row_id > 0
        assert db_path.exists()

    def test_index_stores_code(self, temp_db):
        """XML-код формы сохраняется в БД."""
        xml = (FIXTURES / "managed_simple.xml").read_text(encoding="utf-8")
        row_id = index_form(xml_content=xml, form_name="Test", db_path=temp_db)

        code = get_form_code(row_id, temp_db)
        assert code is not None
        assert "ManagedForm" in code

    def test_index_generates_description(self, temp_db):
        """Автоматическая генерация описания."""
        xml = (FIXTURES / "logform_catalog_element.xml").read_text(encoding="utf-8")
        row_id = index_form(
            xml_content=xml,
            form_name="ФормаЭлемента",
            object_type="Catalog",
            object_name="Номенклатура",
            form_type="ФормаЭлемента",
            db_path=temp_db,
        )

        conn = sqlite3.connect(str(temp_db))
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT description FROM forms WHERE id = ?", (row_id,))
        row = cur.fetchone()
        conn.close()

        assert row is not None
        assert "Catalog" in row["description"] or "Номенклатура" in row["description"]

    def test_index_directory(self, temp_db):
        """Индексация директории с фикстурами."""
        stats = index_directory(FIXTURES, pattern="*.xml", db_path=temp_db)
        assert stats["indexed"] >= 3  # 3 валидных XML + 1 broken
        assert isinstance(stats["errors"], list)


class TestSearch:
    """Тесты поиска."""

    def test_fts_by_object_type(self, populated_db):
        """FTS поиск по типу объекта."""
        results = search_fts("Catalog", db_path=populated_db)
        assert len(results) >= 1
        assert any("Catalog" in r["object_type"] for r in results)

    def test_fts_by_object_name(self, populated_db):
        """FTS поиск по имени объекта."""
        results = search_fts("Номенклатура", db_path=populated_db)
        assert len(results) >= 1

    def test_fts_by_form_type(self, populated_db):
        """FTS поиск по типу формы."""
        results = search_fts("ФормаДокумента", db_path=populated_db)
        assert len(results) >= 1
        assert any(r["form_type"] == "ФормаДокумента" for r in results)

    def test_fts_no_results(self, populated_db):
        """FTS поиск без результатов."""
        results = search_fts("НесуществующийЗапрос12345", db_path=populated_db)
        assert len(results) == 0

    def test_fts_limit(self, populated_db):
        """FTS поиск с ограничением."""
        results = search_fts("Catalog", limit=1, db_path=populated_db)
        assert len(results) <= 1

    def test_search_auto_mode(self, populated_db):
        """Универсальный поиск в режиме fts."""
        results = search("Document", mode="fts", db_path=populated_db)
        assert len(results) >= 1

    def test_search_with_code(self, populated_db):
        """Поиск с включением XML-кода."""
        results = search("Catalog", mode="fts", include_code=True, db_path=populated_db)
        assert len(results) >= 1
        assert "form_code" in results[0]
        assert len(results[0]["form_code"]) > 0

    def test_get_form_code_exists(self, populated_db):
        """Получение кода существующей формы."""
        code = get_form_code(1, populated_db)
        assert code is not None
        assert "<?xml" in code

    def test_get_form_code_not_exists(self, populated_db):
        """Получение кода несуществующей формы."""
        code = get_form_code(99999, populated_db)
        assert code is None


def _embeddings_available() -> bool:
    try:
        from mcp_forms.search.embeddings import is_available
        return is_available()
    except Exception:
        return False


class TestEmbeddings:
    """Тесты модуля эмбеддингов."""

    def test_is_available(self):
        """Проверка доступности sentence-transformers."""
        from mcp_forms.search.embeddings import is_available
        assert isinstance(is_available(), bool)

    @pytest.mark.skipif(
        not _embeddings_available(),
        reason="sentence-transformers не установлен",
    )
    def test_vector_search(self, populated_db):
        """Векторный поиск (если sentence-transformers доступен)."""
        results = search("форма справочника", mode="vector", db_path=populated_db)
        assert len(results) >= 1
        assert all("score" in r for r in results)
