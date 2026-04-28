"""Core agent — ties LLM provider, tools, and conversation together."""

from __future__ import annotations

from typing import Any, Generator

from .config import MAX_CONTEXT_MESSAGES, MAX_TOOL_ROUNDS, WORKSPACE_ROOT
from .prompts import coding_system_prompt
from .providers.base import LLMProvider, Message, ToolCall
from .tools.registry import ToolRegistry


class CodingAgent:
    """The main SAISA coding agent — agentic loop with tool use."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider
        self.tools = ToolRegistry()
        self.history: list[Message] = []
        self._system = Message(role="system", content=coding_system_prompt(WORKSPACE_ROOT))

    def clear_history(self) -> None:
        self.history.clear()

    def _trimmed_history(self) -> list[Message]:
        if len(self.history) > MAX_CONTEXT_MESSAGES:
            return self.history[-MAX_CONTEXT_MESSAGES:]
        return list(self.history)

    def _build_messages(self, user_text: str | None = None) -> list[Message]:
        msgs = [self._system, *self._trimmed_history()]
        if user_text is not None:
            msgs.append(Message(role="user", content=user_text))
        return msgs

    def _execute_tool_calls(self, tool_calls: list[ToolCall]) -> list[Message]:
        results: list[Message] = []
        for tc in tool_calls:
            output = self.tools.dispatch(tc.name, tc.arguments)
            results.append(
                Message(role="tool", content=output, tool_call_id=tc.id, name=tc.name)
            )
        return results

    # ── Blocking turn ────────────────────────────────────────────────────

    def run_turn(self, user_text: str) -> str:
        """Run a full turn: user message -> (optional tool loops) -> final text."""
        self.history.append(Message(role="user", content=user_text))
        messages = self._build_messages()

        for _ in range(MAX_TOOL_ROUNDS):
            response = self.provider.chat(messages, tools=self.tools.definitions)

            if response.tool_calls:
                self.history.append(response)
                messages.append(response)
                tool_results = self._execute_tool_calls(response.tool_calls)
                self.history.extend(tool_results)
                messages.extend(tool_results)
                continue

            if response.content:
                self.history.append(response)
                return response.content

            break

        fallback = "I wasn't able to generate a response. Please try rephrasing."
        self.history.append(Message(role="assistant", content=fallback))
        return fallback

    # ── Streaming turn ───────────────────────────────────────────────────

    def run_turn_streaming(
        self,
        user_text: str,
        on_tool_start: Any = None,
        on_tool_end: Any = None,
    ) -> Generator[str, None, str]:
        """Run a turn with streaming.

        Yields text tokens as they arrive.
        When the model calls tools, yields nothing but executes them and continues.
        Returns the full final assistant text.
        """
        self.history.append(Message(role="user", content=user_text))
        messages = self._build_messages()

        for _ in range(MAX_TOOL_ROUNDS):
            # first try streaming
            full_text = ""
            tool_calls: list[ToolCall] = []
            try:
                gen = self.provider.stream_chat(messages, tools=self.tools.definitions)
                try:
                    while True:
                        token = next(gen)
                        full_text += token
                        yield token
                except StopIteration as e:
                    response = e.value
                    if response is not None:
                        tool_calls = response.tool_calls
                        if response.content and not full_text:
                            full_text = response.content
            except Exception:
                # fallback to blocking
                response = self.provider.chat(messages, tools=self.tools.definitions)
                full_text = response.content
                tool_calls = response.tool_calls
                if full_text:
                    yield full_text

            if tool_calls:
                assistant_msg = Message(role="assistant", content=full_text, tool_calls=tool_calls)
                self.history.append(assistant_msg)
                messages.append(assistant_msg)

                for tc in tool_calls:
                    if on_tool_start:
                        on_tool_start(tc.name, tc.arguments)
                    output = self.tools.dispatch(tc.name, tc.arguments)
                    if on_tool_end:
                        on_tool_end(tc.name, output)
                    tool_msg = Message(role="tool", content=output, tool_call_id=tc.id, name=tc.name)
                    self.history.append(tool_msg)
                    messages.append(tool_msg)
                full_text = ""
                continue

            if full_text:
                self.history.append(Message(role="assistant", content=full_text))
                return full_text

            break

        fallback = "No response generated."
        self.history.append(Message(role="assistant", content=fallback))
        return fallback
