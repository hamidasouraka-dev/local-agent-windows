"""Abstract base for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generator


@dataclass
class Message:
    role: str  # system | user | assistant | tool
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    tool_call_id: str
    name: str
    content: str


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]


class LLMProvider(ABC):
    """Interface that every LLM provider must implement."""

    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        *,
        stream: bool = False,
    ) -> Message:
        """Send messages and get a response (blocking)."""

    @abstractmethod
    def stream_chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> Generator[str, None, Message]:
        """Yield text tokens as they arrive, then return the full Message."""

    @abstractmethod
    def close(self) -> None:
        """Release resources."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier."""
