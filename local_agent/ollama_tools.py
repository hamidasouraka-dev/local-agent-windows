from __future__ import annotations

from typing import Any

from .config import ALLOW_FETCH_URL, ALLOW_OPEN_BROWSER, ALLOW_POWERSHELL, ALLOW_SMTP_SEND

# Schémas compatibles API chat Ollama / Groq OpenAI (outils type « function »).
OLLAMA_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "Liste le contenu d'un dossier dans le workspace (chemin relatif).",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Chemin relatif au workspace, ex. '.' ou 'sous-dossier'.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lit un fichier texte du workspace (taille limitée côté agent).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Chemin relatif au workspace."}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Écrit ou remplace un fichier dans le workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Supprime un fichier dans le workspace (confirmations humaines côté terminal).",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_powershell",
            "description": "Exécute une commande PowerShell dans le workspace si autorisé par la configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Commande PowerShell complète."}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Recherche courte via DuckDuckGo (résumés publics). "
                "Appel API uniquement : nom exact « web_search », paramètre query (string) — ne pas imiter avec du texte <function=…>."
            ),
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "news_search",
            "description": "Recherche d'actualités via DuckDuckGo News.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "description": "Nombre max de résultats (défaut 5)."},
                },
                "required": ["query"],
            },
        },
    },
]

_MEMORY_APPEND_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "append_memory_note",
        "description": (
            "Ajoute une entrée datée dans le journal de mémoire persistant sur le disque (fichier dans workspace/memory). "
            "À utiliser pour faits importants, préférences, décisions à retenir entre les sessions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "note": {"type": "string", "description": "Texte à mémoriser (clair et concis)."},
                "tag": {"type": "string", "description": "Tag optionnel (défaut: projet)."},
            },
            "required": ["note"],
        },
    },
}

_MEMORY_READ_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "read_memory_notes",
        "description": "Lit le journal de mémoire persistant (derniers caractères si très long).",
        "parameters": {
            "type": "object",
            "properties": {
                "max_chars": {
                    "type": "integer",
                    "description": "Optionnel : nombre max de caractères (défaut config).",
                },
                "tag": {
                    "type": "string",
                    "description": "Optionnel : filtre les notes portant ce tag exact.",
                },
            },
        },
    },
}

_FETCH_URL_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "fetch_url",
        "description": (
            "Télécharge une page web http(s) et renvoie un extrait texte (pas un navigateur graphique). "
            "Utile pour lire une URL précise après une recherche."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL complète https:// ou http://",
                }
            },
            "required": ["url"],
        },
    },
}

_SMTP_EMAIL_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "send_smtp_email",
        "description": (
            "Envoie un e-mail texte via SMTP (config .env). L’opérateur confirme dans le terminal. "
            "Une seule adresse destinataire."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Adresse e-mail du destinataire."},
                "subject": {"type": "string"},
                "body": {"type": "string", "description": "Corps du message en texte brut."},
            },
            "required": ["to", "subject", "body"],
        },
    },
}

_WHATSAPP_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_whatsapp_compose",
        "description": (
            "Prépare un message WhatsApp via le lien officiel wa.me (numéro international sans +, ex. 33612345678). "
            "N’envoie pas tout seul : ouvre le navigateur / l’app pour que l’humain valide l’envoi. "
            "Pas d’API WhatsApp Business ici."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "Chiffres uniquement, indicatif pays inclus."},
                "message": {"type": "string", "description": "Texte du message (peut être vide)."},
                "open_in_browser": {
                    "type": "boolean",
                    "description": "Si true (défaut), ouvre le lien ; si false, retourne seulement l’URL wa.me.",
                },
            },
            "required": ["phone"],
        },
    },
}

_OPEN_BROWSER_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_browser_url",
        "description": "Ouvre une URL http(s) dans le navigateur par défaut (confirmation humaine).",
        "parameters": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
}


def agent_function_tools() -> list[dict[str, Any]]:
    out = list(OLLAMA_TOOLS)
    out.append(_MEMORY_APPEND_TOOL)
    out.append(_MEMORY_READ_TOOL)
    if not ALLOW_POWERSHELL:
        out = [t for t in out if ((t.get("function") or {}).get("name") != "run_powershell")]
    if ALLOW_FETCH_URL:
        out.append(_FETCH_URL_TOOL)
    if ALLOW_SMTP_SEND:
        out.append(_SMTP_EMAIL_TOOL)
    out.append(_WHATSAPP_TOOL)
    if ALLOW_OPEN_BROWSER:
        out.append(_OPEN_BROWSER_TOOL)
    return out
