"""Robust error handling — custom exceptions and error recovery.

Centralized error types for the entire SAISA ecosystem.
Each error type has a user-friendly message and recovery suggestion.
"""

from __future__ import annotations


class SaisaError(Exception):
    """Base exception for all SAISA errors."""

    def __init__(self, message: str, suggestion: str = "") -> None:
        self.suggestion = suggestion
        super().__init__(message)

    def friendly(self) -> str:
        msg = str(self)
        if self.suggestion:
            msg += f"\n  Suggestion: {self.suggestion}"
        return msg


# ── Provider Errors ──────────────────────────────────────────────────────


class ProviderError(SaisaError):
    """Error communicating with an LLM provider."""
    pass


class ProviderConnectionError(ProviderError):
    """Cannot reach the provider."""

    def __init__(self, provider: str, url: str, original: Exception | None = None) -> None:
        suggestions = {
            "ollama": "Start Ollama with: ollama serve\nThen pull a model: ollama pull llama3.2",
            "groq": "Check your internet connection and GROQ_API_KEY in .env",
            "openai": "Check your internet connection and OPENAI_API_KEY in .env",
            "anthropic": "Check your internet connection and ANTHROPIC_API_KEY in .env",
        }
        suggestion = suggestions.get(provider, "Check the provider URL and your network connection.")
        super().__init__(
            f"Cannot connect to {provider} at {url}",
            suggestion=suggestion,
        )
        self.provider = provider
        self.url = url
        self.original = original


class APIKeyMissingError(ProviderError):
    """API key not configured for a cloud provider."""

    URLS = {
        "groq": "https://console.groq.com/keys",
        "openai": "https://platform.openai.com/api-keys",
        "anthropic": "https://console.anthropic.com/settings/keys",
    }

    def __init__(self, provider: str) -> None:
        url = self.URLS.get(provider, "")
        env_var = f"{provider.upper()}_API_KEY"
        suggestion = f"Set {env_var} in your .env file"
        if url:
            suggestion += f"\nGet a key at: {url}"
        suggestion += "\nOr use Ollama (free, local): saisa -p ollama"
        super().__init__(
            f"API key missing for {provider}",
            suggestion=suggestion,
        )
        self.provider = provider


class RateLimitError(ProviderError):
    """Rate limit hit on a cloud provider."""

    def __init__(self, provider: str, wait_seconds: float = 0) -> None:
        suggestion = f"Wait {wait_seconds:.0f}s and retry" if wait_seconds > 0 else "Wait a moment and retry"
        suggestion += "\nOr switch to a local provider: saisa -p ollama"
        super().__init__(
            f"Rate limit reached on {provider}",
            suggestion=suggestion,
        )
        self.wait_seconds = wait_seconds


class ModelNotFoundError(ProviderError):
    """Requested model not available."""

    def __init__(self, provider: str, model: str) -> None:
        suggestions = {
            "ollama": f"Pull the model first: ollama pull {model}\nList available: ollama list",
            "groq": "Check available models at: https://console.groq.com/docs/models",
            "openai": "Check available models at: https://platform.openai.com/docs/models",
            "anthropic": "Check available models at: https://docs.anthropic.com/en/docs/about-claude/models",
        }
        super().__init__(
            f"Model '{model}' not found on {provider}",
            suggestion=suggestions.get(provider, "Check the model name and try again."),
        )


# ── Tool Errors ──────────────────────────────────────────────────────────


class ToolError(SaisaError):
    """Error executing a tool."""
    pass


class FileNotFoundError_(ToolError):
    """File not found during a tool operation."""

    def __init__(self, path: str) -> None:
        super().__init__(
            f"File not found: {path}",
            suggestion="Check the file path. Use /tree or find_files to locate files.",
        )


class EditConflictError(ToolError):
    """edit_file old_string not found or not unique."""

    def __init__(self, path: str, reason: str = "not found") -> None:
        super().__init__(
            f"Edit conflict in {path}: search string {reason}",
            suggestion="Use read_file first, then provide more context in old_string to make it unique.",
        )


class ShellCommandError(ToolError):
    """Shell command failed or was blocked."""

    def __init__(self, command: str, reason: str = "") -> None:
        super().__init__(
            f"Command failed: {command}" + (f" ({reason})" if reason else ""),
            suggestion="Check the command syntax. Some dangerous commands are blocked for safety.",
        )


class PermissionDeniedError(ToolError):
    """Operation not allowed for current user/role."""

    def __init__(self, operation: str, role: str = "") -> None:
        suggestion = "Login with appropriate permissions: /login <user> <pass>"
        if role:
            suggestion += f"\nCurrent role '{role}' does not have '{operation}' permission."
        super().__init__(
            f"Permission denied: {operation}",
            suggestion=suggestion,
        )


# ── Session Errors ───────────────────────────────────────────────────────


class SessionError(SaisaError):
    """Error with session management."""
    pass


class SessionNotFoundError(SessionError):
    """Session file not found."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            f"Session not found: {session_id}",
            suggestion="List sessions with /sessions to see available ones.",
        )


class SessionCorruptedError(SessionError):
    """Session file is corrupted."""

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Session file corrupted: {path}",
            suggestion="The session file may be damaged. Start a new session with /new.",
        )


# ── Configuration Errors ─────────────────────────────────────────────────


class ConfigError(SaisaError):
    """Configuration error."""
    pass


class InvalidProviderError(ConfigError):
    """Unknown provider name."""

    def __init__(self, provider: str) -> None:
        super().__init__(
            f"Unknown provider: {provider}",
            suggestion="Available providers: ollama, groq, openai, anthropic\nUse: saisa -p <provider>",
        )
