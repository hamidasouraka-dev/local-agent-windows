"""Ollama provider — fully local inference."""

from __future__ import annotations

import json
import uuid
from typing import Any, Generator

import httpx

from ..config import OLLAMA_BASE_URL, OLLAMA_MODEL, REQUEST_TIMEOUT, TEMPERATURE
from .base import LLMProvider, Message, ToolCall, ToolDefinition


def _tool_defs_to_ollama(tools: list[ToolDefinition]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in tools
    ]


def _parse_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw.strip()) if raw.strip() else {}
        except json.JSONDecodeError:
            return {}
    return {}


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._model = model
        self._http = httpx.Client(timeout=REQUEST_TIMEOUT)
        # verify connectivity
        try:
            r = self._http.get(f"{self._base}/api/tags", timeout=10.0)
            r.raise_for_status()
        except Exception as exc:
            self._http.close()
            raise ConnectionError(
                f"Ollama unreachable at {self._base}. "
                "Start Ollama (ollama serve) and check OLLAMA_BASE_URL."
            ) from exc

    @property
    def model_name(self) -> str:
        return f"ollama/{self._model}"

    def close(self) -> None:
        self._http.close()

    # ----- internal helpers -----

    def _messages_payload(self, messages: list[Message]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for m in messages:
            d: dict[str, Any] = {"role": m.role, "content": m.content}
            if m.tool_calls:
                d["tool_calls"] = [
                    {
                        "id": tc.id,
                        "function": {"name": tc.name, "arguments": tc.arguments},
                    }
                    for tc in m.tool_calls
                ]
            if m.tool_call_id:
                d["tool_call_id"] = m.tool_call_id
            if m.name:
                d["name"] = m.name
            out.append(d)
        return out

    def _post(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        *,
        stream: bool = False,
    ) -> httpx.Response:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": TEMPERATURE},
        }
        if tools:
            payload["tools"] = tools
        return self._http.post(f"{self._base}/api/chat", json=payload)

    # ----- public API -----

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        *,
        stream: bool = False,
    ) -> Message:
        raw_msgs = self._messages_payload(messages)
        raw_tools = _tool_defs_to_ollama(tools) if tools else None
        r = self._post(raw_msgs, raw_tools, stream=False)
        r.raise_for_status()
        data = r.json()
        msg = data.get("message") or {}
        content = (msg.get("content") or "").strip()
        tool_calls: list[ToolCall] = []
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function") or {}
            tool_calls.append(
                ToolCall(
                    id=tc.get("id") or str(uuid.uuid4()),
                    name=fn.get("name", ""),
                    arguments=_parse_arguments(fn.get("arguments")),
                )
            )
        return Message(role="assistant", content=content, tool_calls=tool_calls)

    def stream_chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> Generator[str, None, Message]:
        raw_msgs = self._messages_payload(messages)
        raw_tools = _tool_defs_to_ollama(tools) if tools else None
        with self._http.stream(
            "POST",
            f"{self._base}/api/chat",
            json={
                "model": self._model,
                "messages": raw_msgs,
                "stream": True,
                "options": {"temperature": TEMPERATURE},
                **({"tools": raw_tools} if raw_tools else {}),
            },
        ) as resp:
            resp.raise_for_status()
            full_content = ""
            tool_calls: list[ToolCall] = []
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = chunk.get("message") or {}
                token = msg.get("content") or ""
                if token:
                    full_content += token
                    yield token
                for tc in msg.get("tool_calls") or []:
                    fn = tc.get("function") or {}
                    tool_calls.append(
                        ToolCall(
                            id=tc.get("id") or str(uuid.uuid4()),
                            name=fn.get("name", ""),
                            arguments=_parse_arguments(fn.get("arguments")),
                        )
                    )
            return Message(role="assistant", content=full_content.strip(), tool_calls=tool_calls)
