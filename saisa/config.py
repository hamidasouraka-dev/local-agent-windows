"""Centralised configuration loaded from environment / .env file."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------
PROVIDER = os.environ.get("SAISA_PROVIDER", "ollama").strip().lower()

# Ollama
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2").strip()

# Groq
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()

# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o").strip()
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()

# Anthropic
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514").strip()

# ---------------------------------------------------------------------------
# Agent settings
# ---------------------------------------------------------------------------
TEMPERATURE = float(os.environ.get("SAISA_TEMPERATURE", "0.3").strip() or "0.3")
MAX_TOOL_ROUNDS = int(os.environ.get("SAISA_MAX_TOOL_ROUNDS", "30").strip() or "30")
MAX_CONTEXT_MESSAGES = int(os.environ.get("SAISA_MAX_CONTEXT", "60").strip() or "60")
REQUEST_TIMEOUT = float(os.environ.get("SAISA_TIMEOUT", "300").strip() or "300")

# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------
WORKSPACE_ROOT = Path(os.environ.get("SAISA_WORKSPACE", os.getcwd())).resolve()

# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
SESSIONS_DIR = Path(os.environ.get("SAISA_SESSIONS_DIR", str(Path.home() / ".saisa" / "sessions")))

# ---------------------------------------------------------------------------
# Feature flags
# ---------------------------------------------------------------------------
ALLOW_SHELL = os.environ.get("SAISA_ALLOW_SHELL", "1").strip().lower() in ("1", "true", "yes")
ALLOW_GIT = os.environ.get("SAISA_ALLOW_GIT", "1").strip().lower() in ("1", "true", "yes")
STREAMING = os.environ.get("SAISA_STREAMING", "1").strip().lower() in ("1", "true", "yes")

# ---------------------------------------------------------------------------
# Agent identity
# ---------------------------------------------------------------------------
AGENT_NAME = os.environ.get("SAISA_NAME", "SAISA").strip()
OWNER_NAME = os.environ.get("SAISA_OWNER", "").strip()
