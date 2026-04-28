"""Session management — save and restore conversations."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import SESSIONS_DIR
from .providers.base import Message


def _ensure_dir() -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR


def save_session(history: list[Message], provider_name: str, session_id: str = "") -> Path:
    """Persist conversation history to a JSON file."""
    d = _ensure_dir()
    sid = session_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    path = d / f"{sid}.json"
    data: list[dict[str, Any]] = []
    for m in history:
        entry: dict[str, Any] = {"role": m.role, "content": m.content}
        if m.tool_calls:
            entry["tool_calls"] = [
                {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                for tc in m.tool_calls
            ]
        if m.tool_call_id:
            entry["tool_call_id"] = m.tool_call_id
        if m.name:
            entry["name"] = m.name
        data.append(entry)

    payload = {
        "session_id": sid,
        "provider": provider_name,
        "created": datetime.now().isoformat(),
        "messages": data,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_session(path: Path) -> tuple[str, list[Message]]:
    """Load a session from a JSON file. Returns (provider_name, history)."""
    from .providers.base import ToolCall

    raw = json.loads(path.read_text(encoding="utf-8"))
    provider_name = raw.get("provider", "ollama")
    messages: list[Message] = []
    for entry in raw.get("messages", []):
        tool_calls: list[ToolCall] = []
        for tc_data in entry.get("tool_calls", []):
            tool_calls.append(
                ToolCall(
                    id=tc_data.get("id", ""),
                    name=tc_data.get("name", ""),
                    arguments=tc_data.get("arguments", {}),
                )
            )
        messages.append(
            Message(
                role=entry["role"],
                content=entry.get("content", ""),
                tool_calls=tool_calls,
                tool_call_id=entry.get("tool_call_id"),
                name=entry.get("name"),
            )
        )
    return provider_name, messages


def list_sessions() -> list[dict[str, Any]]:
    """List all saved sessions."""
    d = _ensure_dir()
    sessions: list[dict[str, Any]] = []
    for f in sorted(d.glob("*.json"), reverse=True):
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
            sessions.append({
                "id": raw.get("session_id", f.stem),
                "provider": raw.get("provider", "?"),
                "created": raw.get("created", "?"),
                "messages": len(raw.get("messages", [])),
                "path": str(f),
            })
        except Exception:
            continue
    return sessions
