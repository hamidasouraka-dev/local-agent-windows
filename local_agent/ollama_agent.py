from __future__ import annotations

import json
import re
from typing import Any

import httpx

from .config import (
    AGENT_MAX_TOOL_ROUNDS,
    OLLAMA_BASE_URL,
    OLLAMA_CRITIC_MODEL,
    OLLAMA_MAX_HISTORY_MESSAGES,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
    OLLAMA_REQUEST_TIMEOUT_SEC,
    OLLAMA_TEMPERATURE,
    SELF_EVAL_ENABLED,
    SELF_EVAL_MIN_SCORE,
    WORKSPACE_ROOT,
)
from .ollama_tools import agent_function_tools
from .prompts import critic_system_ollama, primary_system_ollama, refinement_user_message
from .tools import ToolContext


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


def _parse_eval_score(text: str) -> int | None:
    m = re.search(r"SCORE:\s*(\d{1,2})\b", text, re.IGNORECASE)
    if not m:
        return None
    try:
        v = int(m.group(1))
        return v if 1 <= v <= 10 else None
    except ValueError:
        return None


def _verdict_is_improve(text: str) -> bool:
    if re.search(r"VERDICT:\s*AMELIORER", text, re.IGNORECASE):
        return True
    if re.search(r"VERDICT:\s*AMÉLIORER", text, re.IGNORECASE):
        return True
    return False


def _strip_auto_eval_footer(reply: str) -> str:
    marker = "\n\n---\n**Auto-évaluation**"
    if marker in reply:
        return reply.split(marker, 1)[0].strip()
    return reply.strip()


class OllamaAgent:
    def __init__(self) -> None:
        self._base = OLLAMA_BASE_URL.rstrip("/")
        self._model = OLLAMA_MODEL
        self._critic_model = OLLAMA_CRITIC_MODEL or OLLAMA_MODEL
        self._ctx = ToolContext()
        self._history: list[dict[str, Any]] = []
        self._tools = agent_function_tools()
        self._http = httpx.Client(timeout=OLLAMA_REQUEST_TIMEOUT_SEC)
        try:
            r = self._http.get(f"{self._base}/api/tags", timeout=10.0)
            r.raise_for_status()
        except Exception as e:
            self._http.close()
            raise RuntimeError(
                f"Ollama injoignable sur {self._base}. Lance l'application Ollama "
                f"ou le service (ollama serve), puis vérifie OLLAMA_BASE_URL. Détail : {e}"
            ) from e

    def close(self) -> None:
        self._http.close()

    def clear_history(self) -> None:
        self._history.clear()

    def _post_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if tools is not None:
            payload["tools"] = tools
        opts: dict[str, Any] = {"temperature": OLLAMA_TEMPERATURE}
        if OLLAMA_NUM_CTX > 0:
            opts["num_ctx"] = OLLAMA_NUM_CTX
        payload["options"] = opts
        url = f"{self._base}/api/chat"
        r = self._http.post(url, json=payload)
        r.raise_for_status()
        return r.json()

    def _run_tool_rounds(self, user_text: str, max_tool_rounds: int) -> str:
        """Exécute les tours d'outils avec historique borné pour éviter l'explosion contexte."""
        system = primary_system_ollama(WORKSPACE_ROOT)
        if len(self._history) > OLLAMA_MAX_HISTORY_MESSAGES:
            del self._history[:-OLLAMA_MAX_HISTORY_MESSAGES]
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system},
            *self._history,
            {"role": "user", "content": user_text},
        ]

        for _ in range(max_tool_rounds):
            data = self._post_chat(self._model, messages, tools=self._tools)
            msg = data.get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()

            if tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": content,
                        "tool_calls": tool_calls,
                    }
                )
                for tc in tool_calls:
                    fn = (tc.get("function") or {})
                    name = fn.get("name") or ""
                    args = _parse_tool_arguments(fn.get("arguments"))
                    result = self._ctx.dispatch(name, args)
                    tid = tc.get("id")
                    tool_msg: dict[str, Any] = {"role": "tool", "content": result}
                    if tid:
                        tool_msg["tool_call_id"] = tid
                    if name:
                        tool_msg["name"] = name
                    messages.append(tool_msg)
                continue

            if content:
                return content

            return "Erreur : réponse vide du modèle (vérifie que le modèle supporte les outils, ex. qwen2.5, llama3.1)."

        return "Arrêt : trop d'appels d'outils successifs (limite de sécurité)."

    def _self_eval(self, user_question: str, draft: str) -> tuple[str, int | None]:
        messages = [
            {"role": "system", "content": critic_system_ollama()},
            {
                "role": "user",
                "content": f"Question :\n{user_question}\n\nRéponse à évaluer :\n{draft}",
            },
        ]
        data = self._post_chat(self._critic_model, messages, tools=None)
        msg = data.get("message") or {}
        crit = (msg.get("content") or "").strip()
        return crit, _parse_eval_score(crit)

    def _refine(self, user_question: str, draft: str, critique_block: str) -> str:
        system = primary_system_ollama(WORKSPACE_ROOT)
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": refinement_user_message(user_question, draft, critique_block),
            },
        ]
        data = self._post_chat(self._model, messages, tools=None)
        msg = data.get("message") or {}
        out = (msg.get("content") or "").strip()
        return out or draft

    def run_turn(self, user_text: str, max_tool_rounds: int | None = None) -> str:
        limit = max_tool_rounds if max_tool_rounds is not None else AGENT_MAX_TOOL_ROUNDS
        draft = self._run_tool_rounds(user_text, max_tool_rounds=limit)
        if not SELF_EVAL_ENABLED:
            self._history.append({"role": "user", "content": user_text})
            self._history.append({"role": "assistant", "content": draft})
            return draft

        critique, score = self._self_eval(user_text, draft)
        need_refine = (
            _verdict_is_improve(critique)
            or (score is not None and score < SELF_EVAL_MIN_SCORE)
        )
        if need_refine and critique:
            improved = self._refine(user_text, draft, critique)
            full = (
                f"{improved}\n\n---\n**Auto-évaluation** (score initial "
                f"{score if score is not None else '?'}/10)\n{critique}"
            )
            self._history.append({"role": "user", "content": user_text})
            self._history.append({"role": "assistant", "content": _strip_auto_eval_footer(full)})
            return full

        suffix = (
            f"\n\n---\n**Auto-évaluation** ({score if score is not None else '?'}/10)\n{critique}"
            if critique
            else ""
        )
        full = f"{draft}{suffix}"
        self._history.append({"role": "user", "content": user_text})
        self._history.append({"role": "assistant", "content": _strip_auto_eval_footer(full)})
        return full
