from __future__ import annotations

import json
import re
import sys
import time
from typing import Any

import httpx

from .config import (
    AGENT_MAX_TOOL_ROUNDS,
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MAX_COMPLETION_TOKENS,
    GROQ_MAX_HISTORY_MESSAGES,
    GROQ_MODEL,
    GROQ_RATE_LIMIT_MAX_RETRIES,
    GROQ_REQUEST_TIMEOUT_SEC,
    GROQ_TEMPERATURE,
    WORKSPACE_ROOT,
)
from .ollama_tools import agent_function_tools
from .prompts import primary_system_groq
from .tools import ToolContext

_FAKE_TOOL_MARKERS = ("<function", "</function>", "<tool", "</tool>")

_RETRY_AFTER_IN_MESSAGE_RE = re.compile(r"try again in\s+([\d.]+)\s*s", re.IGNORECASE)

_CORRECTIVE_USER = (
    "Ta dernière réponse contenait du texte qui imite un appel d’outil ; sur cette API c’est interdit et inutile. "
    "Réponds maintenant en français naturel à ma question initiale, sans balises, sans <function>, sans JSON d’outil. "
    "Si tu n’as pas besoin de lire ou modifier un fichier réel du workspace, ne demande aucun outil."
)

_GROQ_TOOL_REPAIR_USER = (
    "L’API Groq a refusé la réponse : tu as probablement généré un pseudo-appel du type "
    "<function=nom{...}> ou fusionné le nom d’outil avec du JSON dans le texte. "
    "Réessaie : utilise uniquement les appels d’outils natifs de l’API (ex. fonction web_search avec le seul argument query), "
    "sans aucune balise <function dans le contenu du message."
)

_GROQ_TOOL_FALLBACK_NO_TOOLS_USER = (
    "Les appels d’outils échouent encore sur ce tour. Réponds en français **sans aucun outil** : "
    "résume ce que tu ferais (ex. requêtes web à lancer), ce que tu peux déduire sans recherche, "
    "et ce que l’opérateur peut vérifier lui-même sur le web."
)


def _looks_like_fake_tool_text(content: str) -> bool:
    if not content:
        return False
    lower = content.lower()
    return any(m in lower for m in _FAKE_TOOL_MARKERS)


def _is_groq_tool_format_rejected(exc: BaseException) -> bool:
    s = str(exc).lower()
    return "tool_use_failed" in s or "tool call validation failed" in s


def _parse_tool_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return {}
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return {}
    return {}


class GroqAgent:
    """Agent cloud via l’API Groq (format OpenAI Chat Completions)."""

    def __init__(self) -> None:
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY manquante. Clé : https://console.groq.com/keys — ajoute-la dans .env"
            )
        self._base = GROQ_BASE_URL.rstrip("/")
        self._model = GROQ_MODEL
        self._ctx = ToolContext()
        self._history: list[dict[str, Any]] = []
        self._tools = agent_function_tools()
        self._http = httpx.Client(
            timeout=GROQ_REQUEST_TIMEOUT_SEC,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
        )

    def close(self) -> None:
        """Ferme proprement le client HTTP."""
        self._http.close()

    def clear_history(self) -> None:
        """Efface l’historique conversationnel en mémoire."""
        self._history.clear()

    def _seconds_to_wait_on_429(self, r: httpx.Response, attempt: int) -> float:
        """Calcule l’attente avant nouvel essai en cas de 429."""
        ra = r.headers.get("Retry-After")
        if ra:
            try:
                return min(120.0, float(str(ra).strip()))
            except ValueError:
                pass

        msg = ""
        try:
            err_body = r.json()
            inner = err_body.get("error")
            if isinstance(inner, dict):
                msg = str(inner.get("message") or "")
            else:
                msg = str(inner or "")
        except Exception:
            msg = (r.text or "")[:4000]

        m = _RETRY_AFTER_IN_MESSAGE_RE.search(msg)
        if m:
            return min(120.0, float(m.group(1)) + 0.35)
        return min(60.0, 2.0 ** min(attempt + 1, 6))

    def _raise_api_error(self, r: httpx.Response) -> None:
        """Construit une erreur Groq détaillée et homogène."""
        try:
            err_body = r.json()
            detail = err_body.get("error", err_body)
        except Exception:
            detail = (r.text or "")[:800]
        hint = (
            "Essaie /new pour vider l’historique, augmente GROQ_RATE_LIMIT_MAX_RETRIES, "
            "réduis GROQ_MAX_HISTORY_MESSAGES, ou passe à un modèle plus léger "
            "(ex. llama-3.1-8b-instant) — voir console.groq.com/docs/models."
        )
        raise RuntimeError(f"Groq API {r.status_code} : {detail}. {hint}") from None

    def _chat_completions(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        stream_output: bool = True,
    ) -> dict[str, Any]:
        """Envoie une requête Groq; streaming activé seulement sans outils."""
        url = f"{self._base}/chat/completions"
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": GROQ_TEMPERATURE,
        }
        if tools is not None:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        if GROQ_MAX_COMPLETION_TOKENS > 0:
            body["max_tokens"] = GROQ_MAX_COMPLETION_TOKENS

        r: httpx.Response | None = None
        use_stream = tools is None and stream_output

        for attempt in range(GROQ_RATE_LIMIT_MAX_RETRIES + 1):
            if use_stream:
                body["stream"] = True
                with self._http.stream("POST", url, json=body) as rs:
                    r = rs
                    if rs.status_code == 429 and attempt < GROQ_RATE_LIMIT_MAX_RETRIES:
                        wait = self._seconds_to_wait_on_429(rs, attempt)
                        print(
                            f"Groq 429 (limite TPM) — attente {wait:.1f}s, "
                            f"essai {attempt + 2}/{GROQ_RATE_LIMIT_MAX_RETRIES + 1}…",
                            file=sys.stderr,
                            flush=True,
                        )
                        rs.read()
                        time.sleep(wait)
                        continue
                    if rs.status_code >= 400:
                        err_text = rs.read().decode("utf-8", errors="replace")
                        fake = httpx.Response(
                            status_code=rs.status_code,
                            headers=rs.headers,
                            request=rs.request,
                            content=err_text.encode("utf-8", errors="replace"),
                        )
                        self._raise_api_error(fake)

                    chunks: list[str] = []
                    for line in rs.iter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            payload = line[6:].strip()
                        elif line.startswith("data:"):
                            payload = line[5:].strip()
                        else:
                            continue
                        if payload == "[DONE]":
                            break
                        try:
                            data = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        delta = ((data.get("choices") or [{}])[0].get("delta") or {}).get("content")
                        if delta:
                            part = str(delta)
                            chunks.append(part)
                            print(part, end="", flush=True)
                    full = "".join(chunks).strip()
                    if full:
                        print()
                    return {"choices": [{"message": {"content": full}}]}
            else:
                body["stream"] = False
                r = self._http.post(url, json=body)
                if r.status_code < 400:
                    return r.json()
                if r.status_code == 429 and attempt < GROQ_RATE_LIMIT_MAX_RETRIES:
                    wait = self._seconds_to_wait_on_429(r, attempt)
                    print(
                        f"Groq 429 (limite TPM) — attente {wait:.1f}s, "
                        f"essai {attempt + 2}/{GROQ_RATE_LIMIT_MAX_RETRIES + 1}…",
                        file=sys.stderr,
                        flush=True,
                    )
                    time.sleep(wait)
                    continue
                break

        if r is None:
            raise RuntimeError("Aucune réponse HTTP reçue.")
        self._raise_api_error(r)

    def _chat_text_non_stream(self, messages: list[dict[str, Any]]) -> str:
        """Récupère un texte assistant sans streaming (usage interne silencieux)."""
        data = self._chat_completions(messages, tools=None, stream_output=False)
        _, content = self._parse_assistant_message(data)
        return content

    def _maybe_compress_history(self, system_prompt: str) -> None:
        """Compresse l’historique quand il approche la limite pour réduire les 429."""
        threshold = int(GROQ_MAX_HISTORY_MESSAGES * 0.8)
        if len(self._history) <= max(8, threshold):
            return
        ask = (
            "Résume cette conversation en 5 points clés max, en français, format bullet points."
        )
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *self._history,
            {"role": "user", "content": ask},
        ]
        summary = self._chat_text_non_stream(messages).strip()
        if summary:
            self._history = [{"role": "assistant", "content": "[RÉSUMÉ] " + summary}]
            print("Historique compressé (résumé automatique).", file=sys.stderr, flush=True)

    def _groq_chat_with_tool_repair(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Tente de réparer automatiquement les erreurs Groq liées au format d’outil."""
        try:
            return self._chat_completions(messages, tools=tools)
        except RuntimeError as e:
            if not _is_groq_tool_format_rejected(e):
                raise
            messages.append({"role": "user", "content": _GROQ_TOOL_REPAIR_USER})
            try:
                return self._chat_completions(messages, tools=tools)
            except RuntimeError as e2:
                if not _is_groq_tool_format_rejected(e2):
                    raise
                messages.append({"role": "user", "content": _GROQ_TOOL_FALLBACK_NO_TOOLS_USER})
                return self._chat_completions(messages, tools=None)

    def _parse_assistant_message(self, data: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
        """Extrait tool_calls et contenu texte depuis une réponse Groq."""
        choices = data.get("choices") or []
        if not choices:
            return [], ""
        msg = choices[0].get("message") or {}
        tool_calls = msg.get("tool_calls") or []
        content = msg.get("content")
        if content is None:
            content = ""
        return tool_calls, str(content).strip()

    def run_turn(self, user_text: str, max_tool_rounds: int | None = None) -> str:
        """Exécute un tour user→assistant avec outils et protections anti-erreurs."""
        limit = max_tool_rounds if max_tool_rounds is not None else AGENT_MAX_TOOL_ROUNDS
        system = primary_system_groq(WORKSPACE_ROOT)
        self._maybe_compress_history(system)
        if len(self._history) > GROQ_MAX_HISTORY_MESSAGES:
            del self._history[:-GROQ_MAX_HISTORY_MESSAGES]

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system},
            *self._history,
            {"role": "user", "content": user_text},
        ]

        for _ in range(limit):
            data = self._groq_chat_with_tool_repair(messages, self._tools)
            tool_calls, content = self._parse_assistant_message(data)

            if not tool_calls and content and _looks_like_fake_tool_text(content):
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": _CORRECTIVE_USER})
                data = self._groq_chat_with_tool_repair(messages, self._tools)
                tool_calls, content = self._parse_assistant_message(data)

            if not tool_calls and content and _looks_like_fake_tool_text(content):
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": _CORRECTIVE_USER})
                data = self._chat_completions(messages, tools=None)
                tool_calls, content = self._parse_assistant_message(data)

            if not data.get("choices"):
                return "Erreur : réponse vide de l’API Groq."

            if tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": content if content else None,
                        "tool_calls": tool_calls,
                    }
                )
                for tc in tool_calls:
                    fn = tc.get("function") or {}
                    name = fn.get("name") or ""
                    args = _parse_tool_arguments(fn.get("arguments"))
                    result = self._ctx.dispatch(name, args)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.get("id") or "",
                            "content": result,
                        }
                    )
                continue

            if content:
                self._history.append({"role": "user", "content": user_text})
                self._history.append({"role": "assistant", "content": content})
                return content

            return "Erreur : réponse vide du modèle (essaye un modèle Groq qui supporte les outils)."

        return "Arrêt : trop d’appels d’outils successifs (limite de sécurité)."
