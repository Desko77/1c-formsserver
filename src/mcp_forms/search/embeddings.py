"""Генерация эмбеддингов для векторного поиска форм.

Опциональная зависимость: sentence-transformers.
Если не установлена, модуль недоступен.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

# Модель по умолчанию (русскоязычная, лёгкая)
DEFAULT_MODEL = "cointegrated/rubert-tiny2"

_model = None
_model_name = None


def _get_model(model_name: str | None = None):
    """Ленивая загрузка модели sentence-transformers."""
    global _model, _model_name

    model_name = model_name or DEFAULT_MODEL

    if _model is not None and _model_name == model_name:
        return _model

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError(
            "sentence-transformers не установлен. "
            "Установите: pip install sentence-transformers"
        )

    _model = SentenceTransformer(model_name)
    _model_name = model_name
    return _model


def encode(texts: list[str], model_name: str | None = None) -> list[list[float]]:
    """Получить эмбеддинги для списка текстов.

    Args:
        texts: список текстов для кодирования
        model_name: имя модели (по умолчанию rubert-tiny2)

    Returns:
        список эмбеддингов (каждый — list[float])
    """
    model = _get_model(model_name)
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


def encode_single(text: str, model_name: str | None = None) -> list[float]:
    """Получить эмбеддинг для одного текста."""
    result = encode([text], model_name)
    return result[0]


def is_available() -> bool:
    """Проверить доступность sentence-transformers."""
    try:
        import sentence_transformers  # noqa: F401
        return True
    except ImportError:
        return False
