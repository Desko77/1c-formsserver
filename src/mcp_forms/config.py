"""Конфигурация MCP Forms Server."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Пути
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = Path(os.getenv("DATA_PATH", PROJECT_ROOT / "data"))
DATABASES_PATH = Path(os.getenv("DATABASES_PATH", PROJECT_ROOT / "databases"))
EDT_REFERENCE_PATH = Path(os.getenv("EDT_REFERENCE_PATH", PROJECT_ROOT / "edt_reference"))

# Сервер
PORT = int(os.getenv("PORT", "8011"))
HEALTH_PORT = int(os.getenv("HEALTH_PORT", str(PORT + 1)))
TRANSPORT = os.getenv("TRANSPORT", "streamable-http")

# Файлы данных
FORM_SCHEMA_JSON = DATA_PATH / "form_schema.json"
FORM_PROMPT_MD = DATA_PATH / "formprompt.md"
FORM_PROMPT_EDT_MD = DATA_PATH / "formprompt_edt.md"
FORM_XCORE = EDT_REFERENCE_PATH / "Form.xcore"
FORMS_KNOWLEDGE_DB = DATABASES_PATH / "forms_knowledge.db"

# OpenRouter (опционально, для генерации описаний)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-235b-a22b-2507")

# EDT MCP интеграция (опционально)
EDT_MCP_URL = os.getenv("EDT_MCP_URL", "http://localhost:9999/sse")
EDT_ENABLED = os.getenv("EDT_ENABLED", "true").lower() in ("true", "1", "yes")
EDT_TIMEOUT = int(os.getenv("EDT_TIMEOUT", "10"))
