"""OpenAI provider — GPT-4o and compatible models."""

from __future__ import annotations

import json
from typing import Any, Generator

import httpx

from ..config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, REQUEST_TIMEOUT, TEMPERATURE
from .base import LLMProvider, Message, ToolCall, ToolDefinition


def _tool_defs_to_openai(tools: list[ToolDefinition]) -> list[dict[str, Any]]:
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


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        api_key: str = "",
        base_url: str = OPENAI_BASE_URL,
        model: str = OPENAI_MODEL,
    ) -> None:
        self._key = api_key or OPENAI_API_KEY
        if not self._key:
            raise RuntimeError(
                "OPENAI_API_KEY missing. Get one at https://platform.openai.com/api-keys"
            )
        self._base = base_url.rstrip("/")
        self._model = model
        self._http = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            headers={
                "Authorization": f"Bearer {self._key}",
                "Content-Type": "application/json",
            },
        )

    @property
    def model_name(self) -> str:
        return f"openai/{self._model}"

    def close(self) -> None:
        self._http.close()

    def _messages_payload(self, messages: list[Message]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for m in messages:
            d: dict[str, Any] = {"role": m.role, "content": m.content}
            if m.tool_calls:
                d["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                    }
                    for tc in m.tool_calls
                ]
            if m.tool_call_id:
                d["tool_call_id"] = m.tool_call_id
            if m.name:
                d["name"] = m.name
            out.append(d)
        return out

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        *,
        stream: bool = False,
    ) -> Message:
        raw_msgs = self._messages_payload(messages)
        raw_tools = _tool_defs_to_openai(tools) if tools else None
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": raw_msgs,
            "temperature": TEMPERATURE,
        }
        if raw_tools:
            payload["tools"] = raw_tools
        r = self._http.post(f"{self._base}/chat/completions", json=payload)
        r.raise_for_status()
        data = r.json()
        choice = data["choices"][0]
        msg = choice.get("message", {})
        content = (msg.get("content") or "").strip()
        tool_calls: list[ToolCall] = []
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function", {})
            tool_calls.append(
                ToolCall(
                    id=tc.get("id", ""),
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
        raw_tools = _tool_defs_to_openai(tools) if tools else None
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": raw_msgs,
            "temperature": TEMPERATURE,
            "stream": True,
        }
        if raw_tools:
            payload["tools"] = raw_tools

        full_content = ""
        tool_calls: list[ToolCall] = []
        tc_accum: dict[int, dict[str, str]] = {}

        with self._http.stream("POST", f"{self._base}/chat/completions", json=payload) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                token = delta.get("content") or ""
                if token:
                    full_content += token
                    yield token
                for tc_delta in delta.get("tool_calls") or []:
                    idx = tc_delta.get("index", 0)
                    if idx not in tc_accum:
                        tc_accum[idx] = {"id": "", "name": "", "arguments": ""}
                    fn = tc_delta.get("function", {})
                    if fn.get("name"):
                        tc_accum[idx]["name"] = fn["name"]
                    if fn.get("arguments"):
                        tc_accum[idx]["arguments"] += fn["arguments"]
                    if tc_delta.get("id"):
                        tc_accum[idx]["id"] = tc_delta["id"]

        for _idx in sorted(tc_accum):
            acc = tc_accum[_idx]
            tool_calls.append(
                ToolCall(
                    id=acc["id"],
                    name=acc["name"],
                    arguments=_parse_arguments(acc["arguments"]),
                )
            )
        return Message(role="assistant", content=full_content.strip(), tool_calls=tool_calls)
