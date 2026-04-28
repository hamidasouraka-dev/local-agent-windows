"""User input handling with prompt_toolkit for multiline and history."""

from __future__ import annotations

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

PROMPT_STYLE = Style.from_dict({
    "prompt": "bold #bb86fc",
    "": "#e0e0e0",
})

_kb = KeyBindings()


@_kb.add("escape", "enter")
def _multiline_enter(event):  # type: ignore
    """Alt+Enter inserts a newline for multiline input."""
    event.current_buffer.insert_text("\n")


class UserInput:
    """Handles reading user input with history and multiline support."""

    def __init__(self) -> None:
        self._session: PromptSession[str] = PromptSession(
            history=InMemoryHistory(),
            style=PROMPT_STYLE,
            key_bindings=_kb,
            multiline=False,
        )

    def read(self, prompt_text: str = "You > ") -> str | None:
        """Read a line from the user. Returns None on EOF/Ctrl-D."""
        try:
            return self._session.prompt(
                HTML(f"<prompt>{prompt_text}</prompt>"),
            )
        except (EOFError, KeyboardInterrupt):
            return None
