"""User management — authentication, roles, API key management.

Lightweight local-first implementation using JSON storage.
Supports multiple users, roles, and per-user API key vaults.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

USERS_DIR = Path.home() / ".saisa" / "users"


class Role(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"

    @property
    def permissions(self) -> set[str]:
        perms: dict[str, set[str]] = {
            "admin": {
                "read", "write", "execute", "git", "shell", "manage_users",
                "manage_keys", "autopilot", "swarm", "scaffold",
            },
            "developer": {
                "read", "write", "execute", "git", "shell",
                "autopilot", "swarm", "scaffold",
            },
            "viewer": {"read"},
        }
        return perms.get(self.value, set())


@dataclass
class APIKeyEntry:
    provider: str  # ollama, groq, openai, anthropic, custom
    key: str  # encrypted/masked for display
    added_at: float = field(default_factory=time.time)
    label: str = ""

    @property
    def masked(self) -> str:
        if len(self.key) <= 8:
            return "****"
        return self.key[:4] + "..." + self.key[-4:]


@dataclass
class UserProfile:
    username: str
    password_hash: str
    role: str = "developer"
    created_at: float = field(default_factory=time.time)
    last_login: float = 0.0
    api_keys: list[dict[str, Any]] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    session_count: int = 0
    active: bool = True


class UserManager:
    """Manages users, authentication, and API key vaults."""

    def __init__(self, users_dir: Path | None = None) -> None:
        self._dir = users_dir or USERS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._users_file = self._dir / "users.json"
        self._users: dict[str, UserProfile] = {}
        self._current_user: UserProfile | None = None
        self._session_token: str | None = None
        self._load()

    def _load(self) -> None:
        if self._users_file.exists():
            try:
                raw = json.loads(self._users_file.read_text(encoding="utf-8"))
                for udata in raw.get("users", []):
                    user = UserProfile(**udata)
                    self._users[user.username] = user
            except Exception:
                pass

    def _save(self) -> None:
        data = {"users": [asdict(u) for u in self._users.values()]}
        self._users_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _hash_password(password: str, salt: str = "") -> str:
        if not salt:
            salt = secrets.token_hex(16)
        h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
        return f"{salt}${h}"

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        parts = password_hash.split("$", 1)
        if len(parts) != 2:
            return False
        salt, _ = parts
        expected = UserManager._hash_password(password, salt)
        return expected == password_hash

    # ── Registration & Auth ──────────────────────────────────────────────

    def register(self, username: str, password: str, role: str = "developer") -> dict[str, Any]:
        """Register a new user."""
        if username in self._users:
            return {"error": f"User '{username}' already exists"}
        if len(password) < 4:
            return {"error": "Password too short (min 4 characters)"}
        if role not in [r.value for r in Role]:
            return {"error": f"Invalid role. Use: {', '.join(r.value for r in Role)}"}

        user = UserProfile(
            username=username,
            password_hash=self._hash_password(password),
            role=role,
        )
        self._users[username] = user
        self._save()
        return {"ok": True, "username": username, "role": role}

    def login(self, username: str, password: str) -> dict[str, Any]:
        """Authenticate a user and create a session."""
        user = self._users.get(username)
        if user is None:
            return {"error": "User not found"}
        if not user.active:
            return {"error": "Account is deactivated"}
        if not self._verify_password(password, user.password_hash):
            return {"error": "Invalid password"}

        user.last_login = time.time()
        user.session_count += 1
        self._current_user = user
        self._session_token = secrets.token_hex(32)
        self._save()

        return {
            "ok": True,
            "username": username,
            "role": user.role,
            "session_token": self._session_token,
        }

    def logout(self) -> dict[str, Any]:
        """End the current session."""
        self._current_user = None
        self._session_token = None
        return {"ok": True}

    @property
    def current_user(self) -> UserProfile | None:
        return self._current_user

    def has_permission(self, permission: str) -> bool:
        """Check if current user has a specific permission."""
        if self._current_user is None:
            return True  # no auth = full access (single-user mode)
        role = Role(self._current_user.role)
        return permission in role.permissions

    # ── API Key Vault ────────────────────────────────────────────────────

    def add_api_key(self, provider: str, key: str, label: str = "") -> dict[str, Any]:
        """Store an API key for the current user."""
        if self._current_user is None:
            return {"error": "Not logged in"}

        entry = {
            "provider": provider,
            "key": key,
            "added_at": time.time(),
            "label": label or provider,
        }
        self._current_user.api_keys.append(entry)
        self._save()
        masked = key[:4] + "..." + key[-4:] if len(key) > 8 else "****"
        return {"ok": True, "provider": provider, "key_masked": masked}

    def get_api_key(self, provider: str) -> str | None:
        """Get the API key for a provider from the current user's vault."""
        if self._current_user is None:
            return None
        for entry in reversed(self._current_user.api_keys):
            if entry["provider"] == provider:
                return entry["key"]
        return None

    def list_api_keys(self) -> list[dict[str, Any]]:
        """List all API keys (masked) for the current user."""
        if self._current_user is None:
            return []
        result = []
        for entry in self._current_user.api_keys:
            key = entry["key"]
            masked = key[:4] + "..." + key[-4:] if len(key) > 8 else "****"
            result.append({
                "provider": entry["provider"],
                "key_masked": masked,
                "label": entry.get("label", ""),
                "added_at": entry.get("added_at", 0),
            })
        return result

    def remove_api_key(self, provider: str) -> dict[str, Any]:
        """Remove an API key for a provider."""
        if self._current_user is None:
            return {"error": "Not logged in"}
        before = len(self._current_user.api_keys)
        self._current_user.api_keys = [
            e for e in self._current_user.api_keys if e["provider"] != provider
        ]
        removed = before - len(self._current_user.api_keys)
        if removed > 0:
            self._save()
        return {"ok": True, "removed": removed}

    # ── User Management ──────────────────────────────────────────────────

    def list_users(self) -> list[dict[str, Any]]:
        """List all users."""
        return [
            {
                "username": u.username,
                "role": u.role,
                "active": u.active,
                "sessions": u.session_count,
                "last_login": u.last_login,
            }
            for u in self._users.values()
        ]

    def update_role(self, username: str, new_role: str) -> dict[str, Any]:
        """Update a user's role (admin only)."""
        user = self._users.get(username)
        if user is None:
            return {"error": "User not found"}
        if new_role not in [r.value for r in Role]:
            return {"error": f"Invalid role. Use: {', '.join(r.value for r in Role)}"}
        user.role = new_role
        self._save()
        return {"ok": True, "username": username, "new_role": new_role}

    def deactivate(self, username: str) -> dict[str, Any]:
        """Deactivate a user account."""
        user = self._users.get(username)
        if user is None:
            return {"error": "User not found"}
        user.active = False
        self._save()
        return {"ok": True, "username": username, "active": False}

    def set_preference(self, key: str, value: Any) -> dict[str, Any]:
        """Set a user preference."""
        if self._current_user is None:
            return {"error": "Not logged in"}
        self._current_user.preferences[key] = value
        self._save()
        return {"ok": True, "key": key, "value": value}

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        if self._current_user is None:
            return default
        return self._current_user.preferences.get(key, default)


def auto_configure_provider(user_manager: UserManager, provider: str) -> dict[str, str]:
    """Auto-configure environment variables from user's API key vault."""
    env_map: dict[str, str] = {}
    key = user_manager.get_api_key(provider)
    if key:
        provider_env = {
            "groq": "GROQ_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        env_var = provider_env.get(provider)
        if env_var:
            os.environ[env_var] = key
            env_map[env_var] = key[:4] + "..."
    return env_map
