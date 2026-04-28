"""Anthropic provider — Claude models via the Messages API."""

from __future__ import annotations

import json
import uuid
from typing import Any, Generator

import httpx

from ..config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, REQUEST_TIMEOUT, TEMPERATURE
from .base import LLMProvider, Message, ToolCall, ToolDefinition

_API_URL = "https://api.anthropic.com/v1/messages"
_API_VERSION = "2023-06-01"


def _tool_defs_to_anthropic(tools: list[ToolDefinition]) -> list[dict[str, Any]]:
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.parameters,
        }
        for t in tools
    ]


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        api_key: str = "",
        model: str = ANTHROPIC_MODEL,
    ) -> None:
        self._key = api_key or ANTHROPIC_API_KEY
        if not self._key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY missing. Get one at https://console.anthropic.com/"
            )
        self._model = model
        self._http = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            headers={
                "x-api-key": self._key,
                "anthropic-version": _API_VERSION,
                "Content-Type": "application/json",
            },
        )

    @property
    def model_name(self) -> str:
        return f"anthropic/{self._model}"

    def close(self) -> None:
        self._http.close()

    @staticmethod
    def _extract_system(messages: list[Message]) -> tuple[str, list[Message]]:
        system_parts: list[str] = []
        rest: list[Message] = []
        for m in messages:
            if m.role == "system":
                system_parts.append(m.content)
            else:
                rest.append(m)
        return "\n\n".join(system_parts), rest

    def _messages_payload(self, messages: list[Message]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for m in messages:
            if m.role == "assistant" and m.tool_calls:
                content: list[dict[str, Any]] = []
                if m.content:
                    content.append({"type": "text", "text": m.content})
                for tc in m.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                out.append({"role": "assistant", "content": content})
            elif m.role == "tool":
                out.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m.tool_call_id or "",
                        "content": m.content,
                    }],
                })
            else:
                out.append({"role": m.role, "content": m.content})
        return out

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        *,
        stream: bool = False,
    ) -> Message:
        system_text, conv_messages = self._extract_system(messages)
        raw_msgs = self._messages_payload(conv_messages)
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": raw_msgs,
            "max_tokens": 8192,
            "temperature": TEMPERATURE,
        }
        if system_text:
            payload["system"] = system_text
        if tools:
            payload["tools"] = _tool_defs_to_anthropic(tools)

        r = self._http.post(_API_URL, json=payload)
        r.raise_for_status()
        data = r.json()
        content_parts = data.get("content", [])
        text = ""
        tool_calls: list[ToolCall] = []
        for block in content_parts:
            if block.get("type") == "text":
                text += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.get("id", str(uuid.uuid4())),
                        name=block.get("name", ""),
                        arguments=block.get("input", {}),
                    )
                )
        return Message(role="assistant", content=text.strip(), tool_calls=tool_calls)

    def stream_chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> Generator[str, None, Message]:
        system_text, conv_messages = self._extract_system(messages)
        raw_msgs = self._messages_payload(conv_messages)
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": raw_msgs,
            "max_tokens": 8192,
            "temperature": TEMPERATURE,
            "stream": True,
        }
        if system_text:
            payload["system"] = system_text
        if tools:
            payload["tools"] = _tool_defs_to_anthropic(tools)

        full_text = ""
        tool_calls: list[ToolCall] = []
        current_tool: dict[str, Any] | None = None

        with self._http.stream("POST", _API_URL, json=payload) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                try:
                    event = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                evt_type = event.get("type", "")
                if evt_type == "content_block_start":
                    block = event.get("content_block", {})
                    if block.get("type") == "tool_use":
                        current_tool = {
                            "id": block.get("id", str(uuid.uuid4())),
                            "name": block.get("name", ""),
                            "arguments": "",
                        }
                elif evt_type == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        token = delta.get("text", "")
                        full_text += token
                        yield token
                    elif delta.get("type") == "input_json_delta" and current_tool is not None:
                        current_tool["arguments"] += delta.get("partial_json", "")
                elif evt_type == "content_block_stop":
                    if current_tool is not None:
                        args: dict[str, Any] = {}
                        try:
                            args = json.loads(current_tool["arguments"]) if current_tool["arguments"] else {}
                        except json.JSONDecodeError:
                            pass
                        tool_calls.append(
                            ToolCall(
                                id=current_tool["id"],
                                name=current_tool["name"],
                                arguments=args,
                            )
                        )
                        current_tool = None

        return Message(role="assistant", content=full_text.strip(), tool_calls=tool_calls)
