from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_WORKSPACE = PROJECT_ROOT / "workspace"

WORKSPACE_ROOT = Path(
    os.environ.get("WORKSPACE_ROOT", str(_DEFAULT_WORKSPACE))
).resolve()

# groq | ollama
AGENT_BACKEND = os.environ.get("AGENT_BACKEND", "groq").strip().lower()

# 0 = prompts complets (meilleure qualité, plus de tokens). 1 = prompt court + cache web agressif (utile si 429 TPM).
AGENT_PERFORMANCE_MODE = os.environ.get("AGENT_PERFORMANCE_MODE", "0").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
GROQ_REQUEST_TIMEOUT_SEC = float(
    os.environ.get("GROQ_REQUEST_TIMEOUT_SEC", "120").strip() or "120"
)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
# Default to gemma4 (most powerful local model)
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:2b").strip()
OLLAMA_CRITIC_MODEL = os.environ.get("OLLAMA_CRITIC_MODEL", "gemma4:2b").strip()

def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return float(str(raw).strip())
    except ValueError:
        return default


GROQ_TEMPERATURE = max(0.0, min(2.0, _float_env("GROQ_TEMPERATURE", 0.65)))
OLLAMA_TEMPERATURE = max(0.0, min(2.0, _float_env("OLLAMA_TEMPERATURE", 0.65)))


# Fenêtre d’historique (messages user+assistant). Plus haut = conversations plus longues mais plus de TPM (429).
GROQ_MAX_HISTORY_MESSAGES = max(4, _int_env("GROQ_MAX_HISTORY_MESSAGES", 48))

# Nouveaux essais automatiques quand l’API renvoie 429 (rate limit).
GROQ_RATE_LIMIT_MAX_RETRIES = max(0, min(20, _int_env("GROQ_RATE_LIMIT_MAX_RETRIES", 8)))

# 0 = ne pas envoyer max_tokens (défaut API). Ex. 8192 pour des réponses plus longues (consomme plus de TPM).
GROQ_MAX_COMPLETION_TOKENS = max(0, min(131_072, _int_env("GROQ_MAX_COMPLETION_TOKENS", 0)))

AGENT_MAX_TOOL_ROUNDS = max(4, min(32, _int_env("AGENT_MAX_TOOL_ROUNDS", 16)))

# Cache DuckDuckGo (même requête = réponse immédiate pendant TTL secondes ; 0 = désactivé)
WEB_SEARCH_CACHE_TTL_SEC = _int_env(
    "WEB_SEARCH_CACHE_TTL_SEC",
    120 if AGENT_PERFORMANCE_MODE else 0,
)
WEB_SEARCH_CACHE_MAX_ENTRIES = max(8, _int_env("WEB_SEARCH_CACHE_MAX_ENTRIES", 96))

OLLAMA_REQUEST_TIMEOUT_SEC = float(
    os.environ.get("OLLAMA_REQUEST_TIMEOUT_SEC", "600").strip() or "600"
)
OLLAMA_NUM_CTX = _int_env("OLLAMA_NUM_CTX", 0)
OLLAMA_MAX_HISTORY_MESSAGES = max(4, _int_env("OLLAMA_MAX_HISTORY_MESSAGES", 48))

SELF_EVAL_ENABLED = os.environ.get("SELF_EVAL", "1").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
)
SELF_EVAL_MIN_SCORE = max(1, min(10, _int_env("SELF_EVAL_MIN_SCORE", 7)))

ALLOW_POWERSHELL = os.environ.get("ALLOW_POWERSHELL", "0").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
)

# Identité affichée dans le prompt système (créateur / opérateur)
AGENT_OWNER_NAME = os.environ.get("AGENT_OWNER_NAME", "").strip()
AGENT_OWNER_ONLINE_HINT = os.environ.get("AGENT_OWNER_ONLINE_HINT", "").strip()

# Télécharge une page http(s) en texte brut (pas un vrai navigateur graphique)
ALLOW_FETCH_URL = os.environ.get("ALLOW_FETCH_URL", "0").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
)
MAX_FETCH_URL_BYTES = _int_env("MAX_FETCH_URL_BYTES", 500_000)
FETCH_URL_TIMEOUT_SEC = float(
    os.environ.get("FETCH_URL_TIMEOUT_SEC", "25").strip() or "25"
)

# E-mail (SMTP) — mot de passe souvent « mot de passe d’application » (Gmail, etc.)
ALLOW_SMTP_SEND = os.environ.get("ALLOW_SMTP_SEND", "0").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
)
SMTP_HOST = os.environ.get("SMTP_HOST", "").strip()
SMTP_PORT = _int_env("SMTP_PORT", 587)
SMTP_USER = os.environ.get("SMTP_USER", "").strip()
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "").strip()
SMTP_FROM = os.environ.get("SMTP_FROM", "").strip()
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "1").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
    "",
)

# Ouvre le navigateur par défaut (wa.me, liens https) — confirmation humaine à chaque fois
ALLOW_OPEN_BROWSER = os.environ.get("ALLOW_OPEN_BROWSER", "0").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
)

MAX_EMAIL_BODY_CHARS = _int_env("MAX_EMAIL_BODY_CHARS", 200_000)

# Mémoire longue durée (fichiers dans le workspace, sur ton disque)
LOCAL_MEMORY_JOURNAL = os.environ.get(
    "LOCAL_MEMORY_JOURNAL", "memory/journal.md"
).strip().replace("\\", "/")
MAX_MEMORY_JOURNAL_BYTES = _int_env("MAX_MEMORY_JOURNAL_BYTES", 5_000_000)
MAX_MEMORY_READ_CHARS = _int_env("MAX_MEMORY_READ_CHARS", 220_000)

MAX_READ_BYTES = _int_env("MAX_READ_BYTES", 450_000)
MAX_SHELL_OUTPUT = _int_env("MAX_SHELL_OUTPUT", 28_000)
SHELL_TIMEOUT_SEC = 120

# ============ NOUVELLES CONFIGURATIONS POUR AGENT PUISSANT ============

# Mode autonome - permet à l'agent de fonctionner sans intervention humaine
AUTONOMOUS_MODE = os.environ.get("AUTONOMOUS_MODE", "0").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
)

# Surveillance système - permet l'accès aux métriques système
ALLOW_SYSTEM_MONITOR = os.environ.get("ALLOW_SYSTEM_MONITOR", "1").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
)

# Accès Docker - permet de gérer les conteneurs
ALLOW_DOCKER = os.environ.get("ALLOW_DOCKER", "0").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
)

# Accès Git - permet de gérer les dépôt Git
ALLOW_GIT = os.environ.get("ALLOW_GIT", "1").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
)

# Planification de tâches (cron-like)
ALLOW_SCHEDULER = os.environ.get("ALLOW_SCHEDULER", "0").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
)

# Nombre max de tours autonomes sans intervention
AUTONOMOUS_MAX_TURNS = max(10, _int_env("AUTONOMOUS_MAX_TURNS", 100))

# Apprentissage automatique - l'agent apprend de ses erreurs
LEARNING_MODE = os.environ.get("LEARNING_MODE", "1").strip().lower() in (
    "1",
    "true",
    "yes",
    "oui",
)

# Fichier de mémoire apprise
LEARNING_MEMORY_FILE = os.environ.get(
    "LEARNING_MEMORY_FILE", "memory/learned.json"
).strip()

# Nom de l'agent (pour personalisation)
AGENT_NAME = os.environ.get("AGENT_NAME", "LocalAgent").strip()

# Temperature plus haute pour la créativité
OLLAMA_TEMPERATURE = max(0.0, min(2.0, _float_env("OLLAMA_TEMPERATURE", 0.7)))
